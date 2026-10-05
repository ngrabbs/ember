"""Optional binary bench framing and finite 1200-baud 2-FSK; no SDRB imports.

Not a flight waveform. No FEC or retransmission. Original packet is opaque.
"""
import struct
import zlib
import numpy as np

SYNC = bytes.fromhex('1acffc1d')
PREAMBLE = b'\x55' * 16
BAUD = 1200
DEVIATION = 2400
BASEBAND_OFFSET = -100000


def frame(payload, sequence):
    if not 1 <= len(payload) <= 240:
        raise ValueError('binary payload must be 1..240 bytes')
    body = struct.pack('>BIH', 2, sequence, len(payload)) + payload
    return PREAMBLE + SYNC + body + struct.pack('>I', zlib.crc32(body))


def waveform(payload, sequence, rate=1500000, peak=.08):
    raw = frame(payload, sequence)
    bits = np.unpackbits(np.frombuffer(raw, dtype=np.uint8))
    # At an integral samples/symbol rate, compute two short tone tables and
    # one phase per symbol instead of an expensive exponential per RF sample.
    # Preserve continuous phase and the original first-sample phase convention.
    sps = int(round(rate / BAUD))
    if sps > 0 and abs(rate / BAUD - sps) < 1e-9:
        increments = 2*np.pi*(BASEBAND_OFFSET + DEVIATION*np.array([-1., 1.]))/rate
        tones = np.exp(1j*increments[:,None]*np.arange(1,sps+1)).astype(np.complex64)
        starts = np.r_[0.,np.cumsum(increments[bits[:-1]]*sps)]
        rotations = (peak*np.exp(1j*starts)).astype(np.complex64)
        samples = (tones[bits]*rotations[:,None]).reshape(-1)
    else:
        count = int(np.ceil(len(bits) * rate / BAUD))
        indices = np.minimum((np.arange(count) * BAUD / rate).astype(int), len(bits)-1)
        freq = BASEBAND_OFFSET + DEVIATION * (2 * bits[indices].astype(float)-1)
        phase = np.cumsum(freq) * (2*np.pi/rate)
        samples = (peak * np.exp(1j*phase)).astype(np.complex64)
    guard = np.zeros(int(rate*.03), dtype=np.complex64)
    return np.concatenate((guard, samples, guard))


def decode_iq(iq, rate=40000):
    """Recover finite bursts after offset mixing/low-pass decimation.

Search symbol timing, both polarities and measured carrier bias; require outer
CRC32 before returning opaque payload. No ideal carrier/timing is supplied.
"""
    iq = np.asarray(iq, dtype=np.complex64)
    if len(iq) < rate*.1:
        return []
    power = np.abs(iq)**2
    # Smooth power over 1ms; silence/noise baseline must precede/follow burst.
    smooth = np.convolve(power, np.ones(40)/40, 'same')
    threshold = max(float(np.median(smooth))*8, float(np.max(smooth))*.04, 1e-12)
    active = smooth > threshold
    edges = np.diff(np.r_[False, active, False].astype(np.int8))
    starts, stops = np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)
    results = []; seen = set()
    for start, stop in zip(starts, stops):
        if stop-start < rate*.15:
            continue
        a = iq[max(0,start-50):min(len(iq),stop+50)]
        disc = np.angle(a[1:] * np.conj(a[:-1])) * rate/(2*np.pi)
        if len(disc) < 100:
            continue
        low, high = np.percentile(disc[50:-50], [20,80])
        bias = (low+high)/2
        cumulative = np.r_[0,np.cumsum(disc-bias)]
        positions = np.arange(len(cumulative))
        sps = rate/BAUD
        for phase in np.linspace(0,sps,48,endpoint=False):
            boundaries = np.arange(phase,len(disc),sps)
            means = np.diff(np.interp(boundaries,positions,cumulative))/sps
            for inverse in (False,True):
                bits = (means > 0).astype(np.uint8) ^ inverse
                if len(bits) < 32+7*8+4*8:
                    continue
                # 32-bit sync search is inexpensive at the symbol rate.
                windows = np.lib.stride_tricks.sliding_window_view(bits,32)
                syncbits = np.unpackbits(np.frombuffer(SYNC,dtype=np.uint8))
                matches = np.flatnonzero(np.all(windows==syncbits,axis=1))
                for match in matches:
                    at = match+32
                    header = np.packbits(bits[at:at+56]).tobytes()
                    if len(header)!=7:
                        continue
                    version,sequence,size = struct.unpack('>BIH',header)
                    if version!=2 or not 1<=size<=240:
                        continue
                    end=at+(7+size+4)*8
                    if end>len(bits):
                        continue
                    body=np.packbits(bits[at:end]).tobytes()
                    if zlib.crc32(body[:-4])!=int.from_bytes(body[-4:],'big'):
                        continue
                    key=(sequence,body[7:-4])
                    if key not in seen:
                        seen.add(key)
                        results.append(dict(sequence=sequence,payload=body[7:-4],
                                            carrier_bias_hz=float(bias),start_sample=int(start)))
    return results


def decode_iq_coherent(iq, rate=40000):
    """Noncoherent two-tone matched integration for weak finite FSK bursts.

Estimate carrier candidates from received spectra, then search timing. No packet
bytes, sequence or expected telemetry values participate in detection.
"""
    iq=np.asarray(iq,dtype=np.complex64)
    if len(iq)<rate*.2:return []
    power=np.convolve(abs(iq)**2,np.ones(1600)/1600,'same')
    # The matched tone detector can recover bursts below the former broad-band
    # 1.8x envelope gate. Envelope admission is only a candidate: sync, framing
    # and CRC32 remain mandatory, followed by the application's inner validator.
    threshold=max(float(np.median(power))*1.35,1e-12)
    active=power>threshold
    # Bridge short envelope dips without knowing packet content.
    active=np.convolve(active.astype(float),np.ones(4000)/4000,'same')>.25
    edges=np.diff(np.r_[False,active,False].astype(np.int8))
    starts,stops=np.flatnonzero(edges==1),np.flatnonzero(edges==-1)
    rows=[];seen=set();syncbits=np.unpackbits(np.frombuffer(SYNC,dtype=np.uint8))
    for start,stop in zip(starts,stops):
        if stop-start<rate*.2:continue
        a=iq[max(0,start-int(rate*.15)):min(len(iq),stop+int(rate*.15))]
        # Candidate count and burst length bound software work on interference.
        if len(a)>rate*8:continue
        nfft=2048;used=len(a)//nfft*nfft
        spectrum=np.mean(abs(np.fft.fftshift(np.fft.fft(a[:used].reshape(-1,nfft)*np.hanning(nfft),axis=1),axes=1))**2,axis=0)
        freq=np.fft.fftshift(np.fft.fftfreq(nfft,1/rate))
        local=(spectrum>np.roll(spectrum,1))&(spectrum>=np.roll(spectrum,-1))&(abs(freq)<10000)
        peaks=np.flatnonzero(local);peaks=peaks[np.argsort(spectrum[peaks])[-10:]]
        candidates=[]
        for f in freq[peaks]:
            for bias in (f-DEVIATION,f+DEVIATION):
                if abs(bias)<7000 and all(abs(bias-x)>60 for x in candidates):candidates.append(float(bias))
        n=np.arange(len(a));positions=np.arange(len(a)+1);sps=rate/BAUD
        for bias in candidates:
            plus=np.r_[0,np.cumsum(a*np.exp(-2j*np.pi*(bias+DEVIATION)*n/rate))]
            minus=np.r_[0,np.cumsum(a*np.exp(-2j*np.pi*(bias-DEVIATION)*n/rate))]
            for phase in np.linspace(0,sps,48,endpoint=False):
                boundaries=np.arange(phase,len(a),sps)
                ep=abs(np.diff(np.interp(boundaries,positions,plus)))**2
                em=abs(np.diff(np.interp(boundaries,positions,minus)))**2
                for inverse in (False,True):
                    bits=(ep>em).astype(np.uint8)^inverse
                    if len(bits)<120:continue
                    windows=np.lib.stride_tricks.sliding_window_view(bits,32)
                    for match in np.flatnonzero(np.all(windows==syncbits,axis=1)):
                        at=match+32;header=np.packbits(bits[at:at+56]).tobytes()
                        if len(header)!=7:continue
                        version,sequence,size=struct.unpack('>BIH',header)
                        end=at+(7+size+4)*8
                        if version!=2 or not 1<=size<=240 or end>len(bits):continue
                        body=np.packbits(bits[at:end]).tobytes()
                        if zlib.crc32(body[:-4])!=int.from_bytes(body[-4:],'big'):continue
                        key=(sequence,body[7:-4])
                        if key not in seen:
                            seen.add(key);rows.append(dict(sequence=sequence,payload=body[7:-4],carrier_bias_hz=bias,start_sample=int(start),detector='two_tone_integration'))
    return rows
