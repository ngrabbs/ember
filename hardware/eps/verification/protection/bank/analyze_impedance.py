#!/usr/bin/env python3
"""Explicit two-bank averaged-loop sensitivities, not switching qualification.
TI's current-mode approximation is extended with the passive series network.
RHP zero remains a single-stage approximation; transition/PFM are excluded.
"""
import itertools
import json
from pathlib import Path
import numpy as np
from numpy.polynomial import Polynomial as P

HERE=Path(__file__).resolve().parent
F=np.geomspace(1,1e6,6000)
S=2j*np.pi*F

def yc(s,c,r,l):return s*c/(1+s*r*c+s*s*l*c)

def model(vin,current,pre,post,guard,comp,with_barrier=True):
    cb,cc,rb=pre;db,dc,rd=post;lguard,rguard=guard;rc,cs,cp=comp
    load=5/current
    ypre=yc(S,cb,rb,1e-9)+yc(S,cc,.00025,.125e-9)
    if with_barrier:
        zd=1/(1/load+yc(S,db,rd,1e-9)+yc(S,dc,.002,1e-9))
        path=rguard+S*lguard+zd
        sense=path/(.02+path)
        # Reproduce TI's factor-two output damping with an additional DC
        # conductance, retaining the actual downstream capacitor admittance
        # and guard resonance rather than doubling the whole passive branch.
        zout=1/(ypre+1/(.02+path)+1/(load+.02+rguard))
    else:
        path=np.full_like(S,load,dtype=complex)
        sense=load/(load+.02)
        zout=1/(ypre+2/(load+.02))
    duty=max(0,1-vin/(5+current*.02))
    plant=zout*(1-duty)/.055
    if vin<5+current*.02:
        rhpz=(load+.02)*(1-duty)**2/(2*np.pi*8.16e-6)
        plant*=1-S/(2*np.pi*rhpz)
    impedance=(1+S*rc*cs)/(S*(cs+cp)+S*S*rc*cs*cp)
    loop=plant*190e-6*impedance*(1.2/5)*sense
    return loop,zout,path

def closed_poles(vin,current,pre,post,guard,comp):
    # Analytic polynomial of the same averaged network, scaled s=10000*q.
    # Used to distinguish multiple unity crossings from actual model instability.
    scale=1e4;s=P([0,scale]);load=5/current
    def yparts(cb,cc,rb,rc,lb,lc):
        d1=1+s*rb*cb+s*s*lb*cb;d2=1+s*rc*cc+s*s*lc*cc
        return s*cb*d2+s*cc*d1,d1*d2
    npre,dpre=yparts(*pre[:2],pre[2],.00025,1e-9,.125e-9)
    npost,dpost=yparts(*post[:2],post[2],.002,1e-9,1e-9)
    zd_den=dpost/load+npost
    npth=(guard[1]+s*guard[0])*zd_den+dpost
    apth=.02*zd_den+npth;rdc=load+.02+guard[1]
    denout=npre*apth*rdc+zd_den*dpre*rdc+dpre*apth
    numout=dpre*npth*rdc
    rc,cs,cp=comp
    cnum=1+s*rc*cs;cden=s*(cs+cp)+s*s*rc*cs*cp
    duty=max(0,1-vin/(5+current*.02));rhp=P([1])
    if duty:
        omega=(load+.02)*(1-duty)**2/8.16e-6
        rhp=1-s/omega
    num=numout*cnum*rhp*((1-duty)/.055*190e-6*1.2/5)
    den=denout*cden
    return (den+num).roots()*scale

def main():
    e=.001+25e-6*65;ce=.05+30e-6*65
    # Nominal and deliberately wider-than-data combinations. These do not
    # establish frequency-independent ESR or guaranteed cold capacitance.
    pres=[(cb,cc,r) for cb,cc,r in itertools.product([160e-6,340e-6,530.4e-6],[8e-6,24e-6,88e-6],[.0005,.006,.08])]
    posts=[(112e-6,48e-6,.4),(200e-6,176e-6,.005),(312e-6,311.2e-6,.0005)]
    guards=[(l,r) for l,r in itertools.product([2.5e-6,4.7e-6,5.64e-6],[.05,.07])]
    comps=list(itertools.product([3740*(1-e),3740*(1+e)],[75e-9*(1-ce),75e-9*(1+ce)],[300e-12*(1-ce),300e-12*(1+ce)]))
    results=[]
    for barrier in [False,True]:
      for vin,current,pre,post,guard,comp in itertools.product([4.5,6,8.4,35],[.5,2],pres,posts if barrier else [posts[0]],guards if barrier else [guards[0]],comps):
        loop,_,_=model(vin,current,pre,post,guard,comp,barrier)
        mag=abs(loop);phase=np.unwrap(np.angle(loop))*180/np.pi
        crossings=np.where((mag[:-1]>=1)&(mag[1:]<1))[0]+1
        rising=np.where((mag[:-1]<1)&(mag[1:]>=1))[0]+1
        assert len(crossings)>0
        all_cross=np.sort(np.concatenate([crossings,rising]))
        margins=[float(180+phase[k]) for k in all_cross]
        distance=float(np.min(abs(1+loop)))
        if len(crossings)>1 or len(rising) or min(margins)<45:
            poles=closed_poles(vin,current,pre,post,guard,comp) if barrier else np.array([])
            results.append(dict(barrier=barrier,vin=vin,load=current,pre=pre,post=post,guard=guard,comp=comp,
                                down_crossings_Hz=F[crossings].tolist(),rising_crossings_Hz=F[rising].tolist(),phase_margins_deg=margins,
                                closed_poles_real_per_s=poles.real.tolist(),closed_poles_imag_per_s=poles.imag.tolist(),
                                right_half_plane_closed_poles=int(np.sum(poles.real>=0))))
        key='integrated' if barrier else 'converter_only'
        entry=summary[key];entry['cases']+=1
        if min(margins)<entry['minimum_estimated_phase_margin_deg']:
            entry.update(minimum_estimated_phase_margin_deg=min(margins),worst_case=dict(vin=vin,load=current,pre=pre,post=post,guard=guard,comp=comp,crossings_Hz=F[crossings].tolist()))
        entry['minimum_crossover_Hz']=min(entry['minimum_crossover_Hz'],float(F[crossings].min()))
        entry['maximum_crossover_Hz']=max(entry['maximum_crossover_Hz'],float(F[crossings].max()))
        entry['multiple_or_rising_crossing_cases']+=bool(len(crossings)>1 or len(rising))
        entry['minimum_Nyquist_distance']=min(entry['minimum_Nyquist_distance'],distance)
    out={'scope':'Averaged development approximation with explicit RLC networks; excludes switching/PFM/transition, nonlinear clamps and constant-power loads',
         'upstream_nominal_F':420e-6,'upstream_tolerance_only_max_F':496e-6,'upstream_endurance_plus_tolerance_F':618.4e-6,
         'upstream_C16_bypass_max_F':.11e-6,'proposed_upstream_analysis_allocation_F':650e-6,
         'bulk_room_temperature_initial_and_endurance_lower_F':340e-6*.8*.7,
         'bulk_160uF_requirement_remaining_temperature_factor':160e-6/(340e-6*.8*.7),
         'startup_current_A_650uF_5p08V_2p5ms':650e-6*5.08/.0025,
         'startup_direct_all_banks_at_once_A':.5+(650e-6+623.2e-6)*5.08/.0025,
         'cold_100kHz_bulk_ESR_bank_ohm':.4/5,
         'nominal_bulk_100kHz_ESR_bank_max_ohm':.030/5,
         'summary':summary,'flagged_cases':results}
    (HERE/'evidence/impedance.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k!='flagged_cases'},indent=2));print('Flagged cases',len(results))

summary={k:dict(cases=0,minimum_estimated_phase_margin_deg=999,minimum_crossover_Hz=1e9,maximum_crossover_Hz=0,multiple_or_rising_crossing_cases=0,minimum_Nyquist_distance=1e9) for k in ['converter_only','integrated']}
if __name__=='__main__':main()
