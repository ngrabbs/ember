"""One LibreSDR owner: continuous DBPSK receive and bounded Yamcs command uplink."""
import argparse
from collections import OrderedDict
import hashlib
import os
from pathlib import Path
import queue
import signal
import socket
import threading
import time

import numpy as np

from codec import decode as native_decode
from live import Windows, downsample
from modem import decode, frame
from uplink_probe import RATE, DIGITAL_OFFSET, FPGA_SHA

DOWNLINK = ('127.0.0.1', 10019)
COMMAND_PORT = 10029
TX_FREQUENCY = 434994550
RX_FREQUENCY = 437000000
TX_GAIN = 70
RX_GAIN = 0
AMPLITUDE = .20
UPLINK_LIMIT = 128


class Recent:
    """Bounded overlap/command suppression. Reject new keys if saturated."""
    def __init__(self, capacity, lifetime):
        self.capacity = capacity
        self.lifetime = lifetime
        self.keys = OrderedDict()

    def admit(self, key, now):
        while self.keys and now - next(iter(self.keys.values())) >= self.lifetime:
            self.keys.popitem(last=False)
        if key in self.keys or len(self.keys) >= self.capacity:
            return False
        self.keys[key] = now
        return True


def admit_command(wire):
    if len(wire) > UPLINK_LIMIT:
        raise ValueError('Packet too large')
    packet = native_decode(wire)
    h = packet['header']
    if (packet['name'] not in ('PING', 'REQUEST_STATUS', 'REQUEST_IHU_FAULTS', 'REQUEST_RADIO_CONFIG', 'SET_RADIO_PROFILE',
                              'CONFIRM_RADIO_PROFILE', 'REQUEST_TELEMETRY', 'STATUS_CAPTURE',
                              'STATUS_FETCH', 'PAYLOAD_FIRE_CHECK', 'IHU_REBOOT', 'SET_HEARTBEAT',
                              'SET_UHF_TELEMETRY_SCHEDULE', 'SET_UHF_TELEMETRY', 'SET_UHF_TELEMETRY_SET') or h['source'] != 1 or h['target'] != 2 or
            not all(h[k] for k in ('transaction_epoch', 'transaction_id', 'source_boot_id'))):
        raise ValueError('Command is unsupported or missing EMBER addressing/correlation')
    return packet['sequence'], (h['transaction_epoch'], h['transaction_id'])


def waveform(wire, sequence):
    bits = np.unpackbits(np.frombuffer(frame(wire, sequence), np.uint8))
    signal = np.r_[np.zeros(RATE//20),
                   np.repeat(1-2*(np.cumsum(bits)%2).astype(float), RATE//1200),
                   np.zeros(RATE//20)]
    iq = (signal*AMPLITUDE*np.exp(2j*np.pi*DIGITAL_OFFSET*np.arange(len(signal))/RATE)).astype(np.complex64)
    if len(iq) >= RATE or not np.isfinite(iq).all() or np.max(np.abs(iq)) > AMPLITUDE+1e-6:
        raise ValueError('Uplink waveform exceeds burst limit')
    return iq


def forward_window(raw, sock, seen):
    count = 0
    samples = downsample(raw)
    for baud in (1200, 1500):
        for packet in decode(samples, single_window=True, baud=baud):
            wire = bytes.fromhex(packet['hex'])
            if not seen.admit(wire, time.monotonic()):
                continue
            sock.sendto(wire, DOWNLINK)
            count += 1
            h = packet['decoded']['header']
            print(f"RF_RX name={packet['decoded']['name']} source={h['source']} "
                  f"epoch={h['transaction_epoch']} transaction={h['transaction_id']} baud={baud}", flush=True)
    return count


def transmit(radio, tx, uhd, iq):
    radio.set_tx_gain(TX_GAIN, 0)
    try:
        m = uhd.types.TXMetadata()
        m.start_of_burst = m.end_of_burst = m.has_time_spec = True
        m.time_spec = uhd.types.TimeSpec(radio.get_time_now().get_real_secs()+.25)
        if tx.send(iq.reshape(1, -1), m, 2) != len(iq):
            raise RuntimeError('Short RF send; outcome unknown')
        ack = uhd.types.TXAsyncMetadata()
        end = time.monotonic()+2
        while time.monotonic() < end:
            if tx.recv_async_msg(ack, .1):
                if ack.event_code == uhd.types.TXMetadataEventCode.burst_ack:
                    return
                raise RuntimeError(f'RF TX {ack.event_code}')
        raise RuntimeError('Missing SDR burst acknowledgement')
    finally:
        radio.set_tx_gain(0, 0)


def notify_ready():
    address = os.environ.get('NOTIFY_SOCKET')
    if address:
        with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as sock:
            sock.connect('\0'+address[1:] if address.startswith('@') else address)
            sock.sendall(b'READY=1')


def run(args, stop):
    fpga = args.images/'usrp_b210_fpga.bin'
    if hashlib.sha256(fpga.read_bytes()).hexdigest() != FPGA_SHA:
        raise ValueError('FPGA hash mismatch')
    os.environ['UHD_IMAGES_DIR'] = str(args.images)
    import uhd

    radio = uhd.usrp.MultiUSRP(f'type=b200,fpga={fpga}')
    radio.set_master_clock_rate(49152000)
    radio.set_rx_rate(RATE, 0)
    radio.set_tx_rate(RATE, 0)
    radio.set_rx_freq(uhd.types.TuneRequest(RX_FREQUENCY), 0)
    radio.set_tx_freq(uhd.types.TuneRequest(TX_FREQUENCY-DIGITAL_OFFSET), 0)
    radio.set_rx_antenna('RX2', 0)
    radio.set_tx_antenna('TX/RX', 0)
    radio.set_rx_gain(RX_GAIN, 0)
    radio.set_tx_gain(0, 0)
    if any(abs(get(0)-RATE)>1 for get in (radio.get_rx_rate, radio.get_tx_rate)):
        raise ValueError('Unexpected sample rate')
    sa = uhd.usrp.StreamArgs('fc32', 'sc16')
    sa.channels = [0]
    rx = radio.get_rx_stream(sa)
    tx = radio.get_tx_stream(sa)
    jobs = queue.Queue(maxsize=4)
    failures = queue.Queue()
    stats = dict(windows=0, forwarded=0)

    def decode_loop():
        seen = Recent(4096, 30)
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            while not stop.is_set():
                try:
                    window = jobs.get(timeout=.2)
                except queue.Empty:
                    continue
                stats['forwarded'] += forward_window(window, sock, seen)
                stats['windows'] += 1

    def command_loop(sock):
        seen = Recent(4096, 600)
        while not stop.is_set():
            try:
                wire, _ = sock.recvfrom(UPLINK_LIMIT+1)
            except socket.timeout:
                continue
            try:
                seq, key = admit_command(wire)
            except ValueError as exc:
                print(f'RF_TC_REJECT {exc}', flush=True)
                continue
            if not seen.admit(key, time.monotonic()):
                print(f'RF_TC_SUPPRESSED epoch={key[0]} transaction={key[1]}', flush=True)
                continue
            try:
                transmit(radio, tx, uhd, waveform(wire, seq))
                print(f'RF_TX_ACK epoch={key[0]} transaction={key[1]} ground_ack=0', flush=True)
            except RuntimeError as exc:
                # Do not resend or fabricate a command result.
                print(f'RF_TX_UNKNOWN epoch={key[0]} transaction={key[1]} reason={exc}', flush=True)

    def guarded(fn, *parameters):
        try:
            fn(*parameters)
        except Exception as exc:
            failures.put(exc)
            stop.set()

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as commands:
        commands.bind((args.bind, COMMAND_PORT))
        commands.settimeout(.2)
        md = uhd.types.RXMetadata()
        buffer = np.empty((1, 8192), np.complex64)
        windows = Windows()
        threads = [threading.Thread(target=guarded,args=(decode_loop,)),
                   threading.Thread(target=guarded,args=(command_loop,commands))]
        cmd = uhd.types.StreamCMD(uhd.types.StreamMode.start_cont)
        cmd.stream_now = True
        rx.issue_stream_cmd(cmd)
        try:
            for thread in threads:thread.start()
            notify_ready()
            print('RF_LINK_READY rx=continuous tx=bounded_command', flush=True)
            next_status = time.monotonic()+30
            gaps = 0
            while not stop.is_set():
                n = rx.recv(buffer, md, .5)
                if md.error_code != uhd.types.RXMetadataErrorCode.none:
                    if md.error_code != uhd.types.RXMetadataErrorCode.overflow:
                        raise RuntimeError(f'RF RX {md.strerror()}')
                    gaps += 1
                    windows = Windows()
                    print('RF_RX_GAP overflow', flush=True)
                    continue
                if n:
                    for _, job in windows.feed(buffer[0, :n]):
                        try:
                            jobs.put_nowait(job)
                        except queue.Full:
                            raise RuntimeError('RF decoder is not keeping up')
                if time.monotonic() >= next_status:
                    print(f"RF_LINK_STATUS forwarded={stats['forwarded']} "
                          f"windows={stats['windows']} gaps={gaps}", flush=True)
                    next_status = time.monotonic()+30
        finally:
            stop.set()
            rx.issue_stream_cmd(uhd.types.StreamCMD(uhd.types.StreamMode.stop_cont))
            for thread in threads:
                if thread.ident is not None:thread.join()
            radio.set_tx_gain(0, 0)
    if not failures.empty():
        raise failures.get()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bind',default='192.168.1.251')
    parser.add_argument('--images',type=Path,default=Path.home()/'work/ember-lte/images')
    args = parser.parse_args()
    stop = threading.Event()
    for sig in (signal.SIGINT,signal.SIGTERM):
        signal.signal(sig,lambda *_: stop.set())
    run(args,stop)


if __name__ == '__main__':
    main()
