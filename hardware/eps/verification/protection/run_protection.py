#!/usr/bin/env python3
"""Run complete LTC4364 development circuits in installed LTspice.
ADI controller/IRLR2908 models remain in the user's LTspice installation.
Models are typical. Explicit sensitivity cases are not qualified worst cases.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import numpy as np

HERE = Path(__file__).resolve().parent
LIBRARY = Path.home()/'Library/Application Support/LTspice/lib'
EXECUTABLE = '/Applications/LTspice.app/Contents/MacOS/LTspice'


def deck(c):
    source = c.get('stage') == 'source'
    normal = c.get('normal', 32.164 if source else 5.074753)
    fault = c.get('fault', 40 if source else 35)
    rise = c.get('rise', 1e-6)
    stop = c.get('stop', 1.0 if source else .15)
    t_fault = .12 if source else .08
    # Source is PV limited with an explicitly bounded upstream reservoir.
    feed = (f'Vvoc voc 0 PWL(0 0 1m {normal} {t_fault} {normal} '
            f'{t_fault+rise} {fault} {stop} {fault})\n'
            f'Bpv 0 raw I=limit((V(voc)-V(raw))/.1,0,{c.get("pv_current",1)})\n'
            'Cpv raw 0 1u Rser=100m\nRpv raw 0 10meg\n'
            'Lfeed raw input 1u\nRbleed input 0 10meg') if source else (
            f'Vrail drive 0 PWL(0 0 1m {normal} {t_fault} {normal} '
            f'{t_fault+rise} {fault} {stop} {fault})\n'
            f'Rfeed drive wire R=if(time<{t_fault},.001,{c.get("feed_r", .1)})\n'
            f'Lfeed wire input {c.get("feed_l",3.808e-6)}\n'
            'Cprebulk input 0 160u Rser=267m Lser=5n\nCprecer input 0 24u Rser=2m Lser=1n')
    if c.get('stiff'):
        feed = feed.replace('Cprebulk input 0 160u Rser=267m Lser=5n\nCprecer input 0 24u Rser=2m Lser=1n', '')
    if c.get('finite_energy'):
        # Finite charged-source reservoir; the regulator fixture disconnects
        # when the modeled input-to-output bridge closes. Not native hardware.
        feed = (f'Vgood command 0 PWL(0 0 1m {normal} {stop} {normal})\n'
                f'Bgood 0 input I=if(time<{t_fault},limit((V(command)-V(input))/.001,-10,10),0)\n'
                f'Bpv 0 high I=limit((35-V(high))/.1,0,1)\n'
                f'Cenergy high 0 {c["finite_energy"]} Rser=5m Lser=5n\n'
                f'Vbridge bridge 0 PWL(0 0 {t_fault} 0 {t_fault+1e-9} 5)\n'
                'Sbridge high wire bridge 0 swbridge\n'
                '.model swbridge SW(Ron=10m Roff=1e12 Vt=2)\n'
                'Lfeed wire input 10n\n'
                'Cprebulk input 0 160u Rser=267m Lser=5n\n'
                'Cprecer input 0 24u Rser=2m Lser=1n')
    top, bottom = (25800, 1000) if source else (3200, 1000)
    err = .002625
    corner = c.get('threshold', 0)
    top *= 1 + corner*err
    bottom *= 1 - corner*err
    reference = 1.25 + corner*.03
    fb = f'Rfb output div {top}\nRb div 0 {bottom}\n'
    fb += f'Ileak div 0 {corner*1e-6}\nBfb fb 0 V=delay(V(div),{c.get('detect_extra_delay',0)})*{1.25/reference}\n'
    guard = ('Vguard input pin 0\nRsnub pin snub 1\nCsnub snub 0 2u Rser=20m\nDguard 0 pin tv60\n.model tv60 D(Bv=73.7 Ibv=1m Rs=3.73 Cjo=500p)\n' if source else 'Vguard input pin 0\n') if source or c.get('no_guard') else (f'Lguard input pin {c.get("barrier_l",2.5e-6)} Rser=10m\nCpin pin 0 2u Rser=2m Lser=1n\nDguard 0 pin tv36\n.model tv36 D(Bv=44.2 Ibv=1m Rs=1.35 Cjo=500p)\n')
    parallel = not source
    mos = ('Mpass pin gh common common IRLR2908\n'
           'Mdiode sense gd common common IRLR2908\n')
    if parallel:
        mos += ('Mpass2 pin gh common common IRLR2908\n'
                'Mdiode2 sense gd common common IRLR2908\n'
                'Mpass3 pin gh common common IRLR2908\n'
                'Mdiode3 sense gd common common IRLR2908\n')
    if source and c.get('package_parasitics'):
        # Datasheet typical LD/LS. These are package parasitics, not new parts.
        mos = ('Ldp pin dp 4.5n\nLsp sp common 7.5n\n'
               'Ldd sense dd 4.5n\nLsd sd common 7.5n\n'
               'Mpass dp gh sp sp IRLR2908\nMdiode dd gd sd sd IRLR2908\n')
    cap = 1e-9 if source else 68e-9
    ct = 100e-9 if source else 220e-12
    cbulk = c.get('bulk', 38e-6 if source else 112e-6)
    ccer = c.get('ceramic', 10e-6 if source else 48e-6)
    esr = .4
    load = c.get('load', .5 if source else 2)
    startup = c.get('startup', .1 if source else .5)
    t_load = .09 if source else .06
    if c.get('mode') == 'source_recover':
        feed=feed.replace(f'{stop} {fault}', f'.18 {fault} .180001 {normal} {stop} {normal}')
    if c.get('mode') == 'startup':
        feed = feed.replace(f'R=if(time<{t_fault},.001,{c.get("feed_r", .1)})','1m')
        feed = feed.replace(f'{t_fault+rise} {fault}', f'{t_fault+rise} {normal}').replace(f'{stop} {fault}',f'{stop} {normal}')
    if c.get('mode') == 'load_release':
        feed = feed.replace(f'{t_fault+rise} {fault}',f'{t_fault+rise} {normal}').replace(f'{stop} {fault}',f'{stop} {normal}')
    if c.get('mode') == 'prebias':
        load = startup = 0
    loadnet = f'Bload output 0 I=min(max(V(output),0)/.1,if(time<{t_load},{startup},{load}))\n'
    if c.get('mode') == 'load_release':
        loadnet = f'Bload output 0 I=min(max(V(output),0)/.1,if(time<{t_load},.5,if(time<{t_fault},2,0)))\n'
    if c.get('mode') == 'short':
        loadnet += (f'Vsw sc 0 PWL(0 0 {t_fault} 0 {t_fault+1e-8} 5)\n'
                    'Sshort output short sc 0 sw\nRshort short 0 10m\n.model sw SW(Ron=1m Roff=1e12 Vt=2)\n')
        # No simultaneous input OV in the load-short scenario.
        feed = feed.replace(f'{t_fault+rise} {fault}', f'{t_fault+rise} {normal}').replace(f'{stop} {fault}',f'{stop} {normal}')
    if c.get('mode') == 'input_short':
        feed = feed.replace(f'{t_fault+rise} {fault}', f'{t_fault+rise} 0').replace(f'{stop} {fault}',f'{stop} 0')
    if c.get('mode') == 'reset':
        loadnet = 'Bload output 0 I=min(max(V(output),0)/.1,if(time<60m,.5,if(time<81m,2,if(time<140m,.5,2))))\n'
    reset = ''
    if c.get('mode') == 'reset':
        feed = feed.replace(f'{stop} {fault}', f'0.095 {fault} 0.095001 {normal} {stop} {normal}')
        feed = feed.replace(f'R=if(time<{t_fault},.001,{c.get("feed_r", .1)})',
                            f'R=if(time<{t_fault},.001,if(time<.095001,{c.get("feed_r", .1)},.001))')
        stop = .16
        reset = ('Vreset reset 0 PWL(0 0 .105 0 .105001 3.3 .107 3.3 .107001 0)\n'
                 'Rreset reset base 47k\nRbase base 0 100k\n'
                 'Qreset uv base 0 2N3904\n.model 2N3904 NPN(Is=6.734f Bf=100 Vaf=74)\n')
    # Gate clamps are selected SMBJ8.5A; this simple zener model is an
    # explicit approximation, not the manufacturer's dynamic model.
    zeners = ('Dz1 common gh dz12\nDz2 common gd dz12\n'
              '.model dz12 D(Bv=10.4 Ibv=1m Rs=.15 Cjo=10n)\n')
    uvtop = 50000 if source else 20000
    bias = ('Rbias pin biasraw 100\nDbias biasraw vcc dfast\nCbias vcc 0 4.7u Rser=20m\n'
            'Rov pin ov 27.8k\nRovb ov 0 1k\nCov ov 0 1n\nCuv uv 0 10n\n') if source else 'Rbias pin vcc 100\nCbias vcc 0 100n\n'
    ovnode='ov' if source else '0'
    # Source reservoir is diode isolated so a PV short cannot instantly kill
    # gate bias and trap the pass FET in repeated slow linear operation.
    return f'''EMBER LTC4364 {'source' if source else 'rail'} {c['name']}
{feed}
{guard}{bias}
{mos}Rg hg gh 4.7k
Qpull qcollector hg gh pullpnp
Rpull qcollector common 100
Dpull hg gh dfast
.model pullpnp PNP(Is=1.4f Bf=60 Vaf=20 Ikf=.05 Tf=100n Tr=100n)
.model dfast D(Is=4n Rs=1 Cjo=2p Tt=8n Bv=100)
Cgate gh cg {cap}
Rcg cg 0 2.2k
{zeners}Rs sense output 20m
{fb}Ruv vcc uv {uvtop}
Ruvb uv 0 10k
Ct tmr 0 {ct}
Cbulk output 0 {cbulk} Rser={esr} Lser=5n {'IC=5' if c.get('mode')=='prebias' else ''}
Ccer output 0 {ccer} Rser=2m Lser=1n {'IC=5' if c.get('mode')=='prebias' else ''}
{loadnet}{reset}Vlogic logic 0 3.3
Rflt logic fault 47k
* ENOUT is intentionally unused; no off-rail pull-up
X1 output sense gd common hg vcc shdn uv {ovnode} 0 fault enout tmr fb LTC4364-{'2' if source else '1'}
.lib "{LIBRARY/'sub'/('LTC4364-2.sub' if source else 'LTC4364-1.sub')}"
.lib "{LIBRARY/'cmp/standard.mos'}"
.temp {c.get('temperature', 27)}
.tran 0 {stop} 0 {c.get('maxstep', 2e-6 if source else 500e-9)} {'uic' if c.get('mode')=='prebias' else ''}
.options plotwinsize=0
.save V(pin) V(input) V(output) V(common) V(sense) V(gh) V(gd) V(tmr) V(fault) I(Rs) I(Rpull) I(Rbias) Ic(Qpull) Id(Mpass) Id(Mdiode) {'V(dp) V(sp) V(dd) V(sd)' if c.get('package_parasitics') else ''} {'Id(Mpass2) Id(Mdiode2) Id(Mpass3) Id(Mdiode3) I(Dguard) I(Lguard)' if parallel and not c.get('no_guard') else 'Id(Mpass2) Id(Mdiode2) Id(Mpass3) Id(Mdiode3)' if parallel else 'I(Dguard)'}
.end
'''


def read_raw(path):
    b = path.read_bytes()
    marker = 'Binary:\n'.encode('utf-16le')
    k = b.index(marker) + len(marker)
    head = b[:k].decode('utf-16le')
    n = int(re.search(r'No. Variables:\s*(\d+)',head)[1])
    names = re.findall(r'^\s*\d+\s+(\S+)\s+\S+\s*$',head,re.M)
    count = int(re.search(r'No. Points:\s*(\d+)',head)[1])
    data = np.frombuffer(b[k:],dtype=np.dtype([('t','<f8'),('v','<f4',(n-1,))]))
    assert len(data) == count and len(names) == n
    return data['t'], {name.lower():data['v'][:,i] for i,name in enumerate(names[1:])}


def summarize(c, t, v):
    fault = .12 if c.get('stage')=='source' else .08
    m = t >= fault
    vf = v['v(dp)']-v['v(sp)'] if c.get('package_parasitics') else v['v(pin)']-v['v(common)']
    current = sum(v[key] for key in ['id(mpass)','id(mpass2)','id(mpass3)'] if key in v)
    power = np.maximum(vf*current,0)
    reverse_current = sum(v[key] for key in ['id(mdiode)','id(mdiode2)','id(mdiode3)'] if key in v)
    vr = v['v(dd)']-v['v(sd)'] if c.get('package_parasitics') else v['v(sense)']-v['v(common)']
    reverse_power = np.maximum(vr*reverse_current,0)
    dt = np.diff(t)
    integrate = lambda a, mask: float(np.sum((a[1:]+a[:-1])/2*dt*mask[1:]*mask[:-1]))
    at = lambda tt: int(np.argmin(abs(t-tt)))
    active = m & (power > .1)
    stress_start = t[np.where(active)[0][0]] if active.any() else None
    stress_stop = t[np.where(active)[0][-1]] if active.any() else None
    # Conservative comparison with Fig. 11, not a fitted manufacturer model.
    # This Foster step curve lies above visually read 1us/10us/100us/1ms/10ms
    # single-pulse points; the application case temperature is an assumption.
    # Follow the actual adaptive samples so sub-us faults are not discarded
    # by fixed-grid interpolation. Trapezoidal power per interval is assumed.
    pu = (power[1:]+power[:-1])/2
    theta = np.zeros_like(pu)
    for resistance,tau in [(0.03,1e-6),(.12,30e-6),(.35,.8e-3),(.8,8e-3)]:
        alpha=np.exp(-dt/tau)
        state=0.0
        response=np.empty_like(pu)
        for i,value in enumerate(pu):
            state=alpha[i]*state+resistance*(1-alpha[i])*float(value)
            response[i]=state
        theta += response
    linear = m & (vf >= 10)
    extra = {
        'PNP_collector_abs_peak_A':float(np.max(abs(v['ic(qpull)']))),
        'gate_pull_resistor_peak_W':float(np.max(v['i(rpull)']**2*100)),
        'bias_resistor_peak_W':float(np.max(v['i(rbias)']**2*100)),
        'shunt_peak_W':float(np.max(v['i(rs)']**2*.020)),
        'shunt_fault_energy_J':integrate(v['i(rs)']**2*.020,m),
        'reverse_FET_total_fault_energy_J':integrate(reverse_power,m),
        'reverse_FET_total_peak_W':float(reverse_power.max()),
        'reverse_FET_abs_VDS_V':float(np.max(abs(v['v(sense)']-v['v(common)']))),
        'pass_FET_abs_VDS_V':float(np.max(abs(vf))),
        'pass_min_VGS_V':float(np.min(v['v(gh)']-v['v(common)'])),
        'reverse_min_VGS_V':float(np.min(v['v(gd)']-v['v(common)'])),
        'reverse_channel_abs_current_A':float(np.max(abs(reverse_current))),
        'fault_time_above_16p7W_s':float(np.sum(dt*((power[1:]>16.7)&m[1:]))),
        'fault_time_above_66p7W_s':float(np.sum(dt*((power[1:]>66.7)&m[1:]))),
        'fault_time_above_333W_s':float(np.sum(dt*((power[1:]>333)&m[1:]))),
    }
    if c.get('package_parasitics'):
        extra.update(internal_pass_abs_VDS_V=float(np.max(abs(v['v(dp)']-v['v(sp)']))),
                     internal_reverse_abs_VDS_V=float(np.max(abs(v['v(dd)']-v['v(sd)']))),
                     internal_pass_abs_VGS_V=float(np.max(abs(v['v(gh)']-v['v(sp)']))),
                     internal_reverse_abs_VGS_V=float(np.max(abs(v['v(gd)']-v['v(sd)']))))
    if 'i(dguard)' in v:
        extra.update(TVS_abs_peak_A=float(np.max(abs(v['i(dguard)']))),
                     TVS_energy_J=integrate(np.maximum(-v['v(pin)']*v['i(dguard)'],0),m))
    if 'i(lguard)' in v:
        extra['guard_inductor_abs_peak_A']=float(np.max(abs(v['i(lguard)'])))
    return {**extra,'name':c['name'], 'conditions':c,
            'startup_peak_A':float(current[t<fault].max()),
            'startup_pre_load_V':float(v['v(output)'][at(.085 if c.get('stage')=='source' else .059)]),
            'pre_fault_output_V':float(v['v(output)'][at(fault-.001)]),
            'fault_output_peak_V':float(v['v(output)'][m].max()),
            'fault_input_peak_V':float(v['v(input)'][m].max()),
            'fault_guarded_input_peak_V':float(v['v(pin)'][m].max()),
            'fault_current_peak_A':float(current[m].max()),
            'fault_total_pass_peak_W':float(power[m].max()),
            'fault_total_pass_energy_J':integrate(power,m),
            'fault_total_pass_P2t_W2s':integrate(power**2,m),
            'fault_stress_duration_s':None if stress_start is None else float(stress_stop-stress_start),
            'max_pass_VDS_V':float(vf.max()),
            'pair_peak_current_when_VDS_ge_10V_A':float(current[linear].max()) if linear.any() else 0,
            'estimated_full_pair_power_temperature_rise_K':float(theta.max()),
            'thermal_comparison_case_C':[85,125],
            'max_pass_VGS_V':float((v['v(gh)']-v['v(common)']).max()),
            'max_diode_VGS_V':float((v['v(gd)']-v['v(common)']).max()),
            'minimum_series_current_A':float(current.min()),
            'final_output_V':float(v['v(output)'][-1]),
            'max_timer_V':float(v['v(tmr)'].max()),
            'scope':'Typical ADI model plus stated sensitivities; not a guaranteed electrical/SOA result'}


def main():
    p=argparse.ArgumentParser();p.add_argument('--work',type=Path,required=True)
    p.add_argument('--filter',default='');args=p.parse_args();args.work.mkdir(parents=True,exist_ok=True)
    cases=json.loads((HERE/'cases.json').read_text())
    results=[]
    for c in cases:
        if args.filter and args.filter not in c['name']:continue
        path=args.work/(c['name']+'.cir')
        content=deck(c)
        # Exact-deck reuse permits interrupted serial sweeps to resume safely.
        if path.exists() and path.read_text()==content and path.with_suffix('.raw').exists() and path.with_suffix('.log').exists():
            log=path.with_suffix('.log').read_text(errors='replace')
            if 'Total elapsed time:' in log and 'Fatal Error' not in log:
                t,v=read_raw(path.with_suffix('.raw'));result=summarize(c,t,v)
                results.append(result)
                path.with_suffix('.json').write_text(json.dumps(result,indent=2)+'\n')
                print(c['name'],'reused exact deck',flush=True)
                continue
        path.write_text(content)
        for suffix in ['.raw','.log']:
            path.with_suffix(suffix).unlink(missing_ok=True)
        subprocess.run([EXECUTABLE,'-b',str(path)],check=True,timeout=90,capture_output=True)
        log=path.with_suffix('.log').read_text(errors='replace')
        assert 'Total elapsed time:' in log and 'Fatal Error' not in log,log
        t,v=read_raw(path.with_suffix('.raw'));result=summarize(c,t,v)
        results.append(result)
        (args.work/(c['name']+'.json')).write_text(json.dumps(result,indent=2)+'\n')
        print(c['name'], 'pre',round(result['pre_fault_output_V'],4),
              'peak',round(result['fault_output_peak_V'],4),
              'E_mJ',round(result['fault_total_pass_energy_J']*1000,4),flush=True)
    provenance={str(f.relative_to(LIBRARY)):hashlib.sha256(f.read_bytes()).hexdigest()
                for f in [LIBRARY/'sub/LTC4364-1.sub',LIBRARY/'sub/LTC4364-2.sub',LIBRARY/'cmp/standard.mos']}
    (args.work/'results.json').write_text(json.dumps({'models_SHA256':provenance,'results':results},indent=2)+'\n')

if __name__=='__main__':main()
