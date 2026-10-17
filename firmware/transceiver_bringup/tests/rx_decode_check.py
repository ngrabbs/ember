#!/usr/bin/env python3
"""Run the exact embedded decoder against recorded ADC and synthetic negatives."""
from pathlib import Path
import json, math, random, re, struct, subprocess, tempfile, zlib
ROOT=Path(__file__).resolve().parents[3]
SRC=Path(__file__).with_name('rx_decode.c')
with tempfile.TemporaryDirectory() as d:
    exe=Path(d)/'decode'; raw=Path(d)/'samples.bin'
    subprocess.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Wno-unused-function',
                    '-fsanitize=address,undefined',str(SRC),'-o',str(exe)],check=True)
    def run(samples):
        raw.write_bytes(struct.pack('<32768H',*samples))
        return subprocess.check_output([str(exe),str(raw)],text=True).strip()
    evidence=ROOT/'system/ground_station/evidence/rx-bringup-20261017'
    proofs=json.loads((evidence/'libre-packet-40db-proof.json').read_text())
    for proof in proofs:
        text=(evidence/(proof['name']+'-console.txt')).read_text()
        h=re.search(r'\[rx_adc\].*? hex=([0-9a-f]+)',text).group(1)
        samples=[int(h[i:i+3],16) for i in range(0,len(h),3)]
        actual=run(samples)
        assert f"sequence={proof['tx']['rf_sequence']} " in actual and actual.endswith('hex='+proof['tx']['packet_hex']),actual
    packet=bytes.fromhex(proofs[0]['tx']['packet_hex'])
    def waveform(freq=1209, delay=.31, corrupt_outer=False, corrupt_native=False, command=False):
        p=bytearray(packet)
        if corrupt_native:p[-1]^=1
        if command:
            p[7]=0
            import binascii
            p[-2:]=binascii.crc_hqx(p[:-2],0xffff).to_bytes(2,'big')
        body=struct.pack('>BIH',3,1901,len(p))+p
        crc=zlib.crc32(body)^(1 if corrupt_outer else 0)
        frame=b'\x55'*32+bytes.fromhex('1acffc1d')+body+struct.pack('>I',crc)+bytes(16)
        signs=[];sign=1
        for b in frame:
            for shift in range(7,-1,-1):
                if (b>>shift)&1:sign=-sign
                signs.append(sign)
        rng=random.Random(77);out=[]
        for i in range(32768):
            at=int(math.floor((i/8000-delay)*1200))
            v=15*signs[at]*math.cos(2*math.pi*freq*i/8000+.7) if 0<=at<len(signs) else 0
            out.append(round(2085+v+rng.gauss(0,.8)))
        return out
    for f in (1000,1209,1391,1700):
        for delay in (.310,.31007,.900):
            assert run(waveform(f,delay)).endswith('hex='+packet.hex()),(f,delay)
    for kwargs in ({'corrupt_outer':True},{'corrupt_native':True},{'command':True}):
        assert run(waveform(**kwargs))=='NO_PACKET',kwargs
    assert run([2085]*32768)=='NO_PACKET'
    rng=random.Random(93)
    assert run([round(2085+rng.gauss(0,4)) for _ in range(32768)])=='NO_PACKET'
    samples=waveform();samples[100]=4095
    assert run(samples)=='NO_PACKET'
print('PASS: 3 recorded packets, 12 synthetic frequency/timing cases, CRC corruption, command rejection, silence, noise and clipping')
