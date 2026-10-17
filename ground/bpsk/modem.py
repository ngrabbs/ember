"""Version3 1200-baud DBPSK bench decoder; opaque CRC32 frame + native CRC16.

Offline only. No radio ownership or UDP forwarding on import/run.
"""
import argparse
import json
from pathlib import Path
import struct
import sys
import zlib
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'ember'))
from codec import decode as decode_native
BAUD = 1200
SYNC = bytes.fromhex('1acffc1d')

def frame(packet, sequence):
    if not 1 <= len(packet) <= 240:
        raise ValueError('packet length')
    body = struct.pack('>BIH', 3, sequence, len(packet)) + packet
    return b'\x55'*32 + SYNC + body + struct.pack('>I', zlib.crc32(body)) + bytes(16)

def recover_bits(bits):
    sync = np.unpackbits(np.frombuffer(SYNC, np.uint8))
    if len(bits) < 88:
        return []
    hits = np.flatnonzero(np.all(np.lib.stride_tricks.sliding_window_view(bits,32)==sync,axis=1))
    result=[]
    for hit in hits:
        at=hit+32
        if at+56>len(bits):continue
        header=np.packbits(bits[at:at+56]).tobytes()
        version,sequence,size=struct.unpack('>BIH',header)
        if version!=3 or not 1<=size<=240:continue
        end=at+(7+size+4)*8
        if end>len(bits):continue
        body=np.packbits(bits[at:end]).tobytes()
        if zlib.crc32(body[:-4])!=int.from_bytes(body[-4:],'big'):continue
        packet=body[7:-4]
        try: native=decode_native(packet)
        except ValueError:continue
        if native['header']['kind'] not in (1,2):continue
        result.append(dict(sequence=sequence,hex=packet.hex(),decoded=native))
    return result

def decode(iq, rate=48000, *, phase_diagnostic=False, single_window=False):
    if rate%BAUD or rate<4*BAUD:raise ValueError('integer samples/symbol required')
    iq=np.asarray(iq,dtype=np.complex64)
    if iq.ndim!=1 or not np.isfinite(iq).all():raise ValueError('invalid IQ')
    sps=rate//BAUD
    # Four-second windows, one-second stride: cover even a 240-byte native frame
    # (2.02s on air), including preamble, at every window alignment.
    result=[];seen=set()
    for start in ([0] if single_window else range(0,len(iq),rate)):
        a=iq[start:start+4*rate]
        if len(a)<sps*256:continue
        # Squaring removes BPSK sign. Carrier search is limited to +/- rate/4.
        nfft=1 << (len(a)*4-1).bit_length()
        spectrum=np.abs(np.fft.fft(a*a,nfft))
        k=int(np.argmax(spectrum)); k=k if k<nfft//2 else k-nfft
        carrier=k*rate/nfft/2
        corrected=a*np.exp(-2j*np.pi*carrier*np.arange(len(a))/rate)
        integ=np.r_[0,np.cumsum(corrected)]
        for phase in range(sps):
            bounds=np.arange(phase,len(a)+1,sps)
            symbols=np.diff(integ[bounds])
            if len(symbols)<2:continue
            diff=symbols[1:]*np.conj(symbols[:-1])
            # Explicit diagnostic for non-antipodal phase switching. Not a BPSK pass.
            bits=((np.abs(np.angle(diff))>np.pi/4) if phase_diagnostic
                  else (diff.real<0)).astype(np.uint8)
            for item in recover_bits(bits):
                key=(item['sequence'],item['hex'])
                if key in seen:continue
                seen.add(key);item.update(carrier_offset_hz=carrier,window_start=start,timing_sample=phase,decoder='phase-transition-diagnostic' if phase_diagnostic else 'dbpsk')
                result.append(item)
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('iq',type=Path);p.add_argument('--rate',type=int,default=48000)
    p.add_argument('--phase-diagnostic',action='store_true',help='45-degree transition threshold; NOT standard BPSK validation')
    args=p.parse_args()
    print(json.dumps(decode(np.load(args.iq,allow_pickle=False),args.rate,phase_diagnostic=args.phase_diagnostic),indent=2))
