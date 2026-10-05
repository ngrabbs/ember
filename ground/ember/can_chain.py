"""Verify two CAN Feathers and IHU -> COMMS -> Walter bench packet returns."""
import argparse
import json
import re
from pathlib import Path
from comms_uart import Console
from codec import decode, DICTIONARY


def numeric_status(text):
    return {key: int(value) for key, value in re.findall(r' (\w+)=(\d+)\b', text)}


def run(port, output, eps=False):
    c = Console(port)
    results = {'passed': False}
    try:
        first = c.command('status')
        assert 'role=IHU_MCU fw=can-bench-v2' in first and 'can_ready=1' in first, first
        initial = numeric_status(first)
        boot = initial['boot']
        assert initial['pending'] == 0 and boot, first
        results['initial_status'] = first.strip()
        local = c.command('selftest', .6)
        assert 'SELFTEST outcome=PASS kind=LOCAL_LOOPBACK' in local, local
        mode = c.command('normal')
        assert 'CAN_NORMAL ready=1' in mode, mode
        hello = c.command('hello', .7)
        c.require_match(hello, 'CAN_HELLO_CONFIRMED')
        for size in (1, 8, 32, 239, 240):
            reply = c.command(f'ping {size}', .8)
            c.require_match(reply, 'CAN_ECHO_MATCHED')
            returned = re.search(r'bytes=(\d+) hex=([0-9a-f]+)', reply)
            assert returned and int(returned[1]) == size and bytes.fromhex(returned[2]) == bytes(range(size)), reply
        results['can_echoes'] = 5
        packets = []
        for _ in range(10):
            reply = c.command('eps telemetry' if eps else 'telemetry', .8)
            c.require_match(reply, 'WALTER_BENCH_RETURN')
            returned = re.search(r'bytes=(\d+) hex=([0-9a-f]+)', reply)
            assert returned, reply
            raw = bytes.fromhex(returned[2])
            assert len(raw) == int(returned[1]), reply
            packet = decode(raw)
            assert packet['name'] == ('POWER_STATUS' if eps else 'HEARTBEAT'), packet
            assert packet['header']['source'] == DICTIONARY['endpoints']['ihu'], packet
            assert packet['header']['target'] == DICTIONARY['endpoints']['ground'], packet
            assert packet['header']['source_boot_id'] == boot, packet
            if eps:
                p=packet['payload']
                assert (p['provenance'],p['bridge_session_id'],p['readout_valid'])==(2,0,1),packet
                assert p['adc_valid']==1 and p['conversion_valid']==1,packet
                if packets:assert p['readout_count']==packets[-1]['payload']['readout_count']+1,packet
            if packets:
                assert packet['sequence'] == (packets[-1]['sequence']+1) % 16384, packet
                assert packet['header']['uptime_ms'] > packets[-1]['header']['uptime_ms'], packet
            packets.append(packet)
        results['ihu_eps_returns' if eps else 'ihu_heartbeat_returns'] = packets
        final = c.command('status')
        last = numeric_status(final)
        assert last['boot'] == boot and last['pending'] == 0, final
        assert last['matched'] - initial['matched'] == 16, final
        for name in ('unknown', 'tx_fail', 'tx_timeout', 'rx_bad', 'rx_overflow', 'fragments_bad', 'fragments_timeout', 'busy_drops'):
            assert last[name] == initial[name], (name, first, final)
        assert 'eflg=00' in final and last['tec'] == 0 and last['rec'] == 0, final
        results['final_status'] = final.strip()
        results['scope'] = ('Hardware IHU reads EPS via PEC-checked I2C and generates native POWER_STATUS' if eps else
                            'Hardware IHU generates manual bench heartbeat') + '; CAN to COMMS; UART to Walter echo; UART/CAN return to IHU. No LTE delivery or flight command handling.'
        results['passed'] = True
        print(json.dumps(results, indent=2))
    finally:
        c.serial.close()
        output.mkdir(parents=True, exist_ok=True)
        (output/'can-chain.log').write_text(''.join(c.transcript))
        (output/'can-chain.json').write_text(json.dumps(results, indent=2)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--eps',action='store_true',help='Verify real ADC-valid EPS packets instead of heartbeat')
    args = parser.parse_args()
    run(args.port, args.output,args.eps)
