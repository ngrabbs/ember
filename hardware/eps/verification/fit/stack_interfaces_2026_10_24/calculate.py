#!/usr/bin/env python3
"""Read exported/queried geometry; never modify board or library sources."""
import hashlib,json,math,xml.etree.ElementTree as ET
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((HERE/'konnect_readback.json').read_text())
def unpack(result):return json.loads(next(c['text'] for c in result['content'] if c['type']=='text'))
parts={board:{h:unpack(r[board][h]) for h in ['H1','H2']} for board in ['eps','comms']}
for board in parts:
 for h,p in parts[board].items():
  assert p['source']=='file' and p['pad_count']==52
  assert len(p['pads'])==52 and sorted(int(x['number']) for x in p['pads'])==list(range(1,53))
  assert all(x['net'] is not None for x in p['pads'])
centers={};maxdelta=0;rows=[]
for board in parts:
 centers[board]={}
 for h in ['H1','H2']:
  pads=parts[board][h]['pads']
  centers[board][h]={axis:sum(p[axis] for p in pads)/52 for axis in ['x','y']}
for h in ['H1','H2']:
 a={int(p['number']):p for p in parts['eps'][h]['pads']};b={int(p['number']):p for p in parts['comms'][h]['pads']}
 for n in range(1,53):
  delta=max(abs(a[n][axis]-b[n][axis]) for axis in ['x','y'])
  assert delta<1e-9,(h,n,delta)
  maxdelta=max(maxdelta,delta)
  rows.append({'header':h,'pin':n,'eps_xy_mm':[a[n]['x'],a[n]['y']],'comms_xy_mm':[b[n]['x'],b[n]['y']],'eps_net':a[n]['net'],'comms_net':b[n]['net']})
separation={k:math.dist(tuple(v['H1'].values()),tuple(v['H2'].values())) for k,v in centers.items()}
assert all(abs(v-5.08)<1e-9 for v in separation.values())
fp=unpack(r['existing_comms_library']);assert fp['pad_count']==52
padmap={int(p['number']):p for p in fp['pads']}
for n,p in padmap.items():
 assert p['x']==(-1.27 if n%2 else 1.27)
 assert abs(p['y']-(-31.75+((n-1)//2)*2.54))<1e-9
 assert p['drill']==['1.02'] and p['width']==p['height']==1.8
 assert p['layers']==['*.Cu','*.Mask']
# Drawing810-00253A5 uses inch dimensions as authority; converted metric labels round.
pumpkin_sep=(3.575-3.275)*25.4
assert abs(pumpkin_sep-7.62)<1e-9
# Confirmed user16mm is between facing surfaces. Thickness and +/- bounds below
# are explicit sensitivities, NOT accepted stack/fab/part tolerances.
C=11.05;D=23.24;tail=D-C;t=1.6;gap=16
insertion=tail-t-gap+C
hypothesis={'gap_mm':gap,'upper_pcb_mm':t,'socket_seating_height_mm':C,'upper_total_height_plus_tail_mm':D,'upper_tail_derived_mm':tail,'insertion_mm':insertion,'catalog_window_mm':[3.68,6.35]}
# Independent C/D +/-0.25, illustrative PCB and gap +/-0.10.
uncertainty=.25+.25+.25+.10+.10
hypothesis['independent_tolerance_sensitivity_mm']=[insertion-uncertainty,insertion+uncertainty]
hypothesis['same_face_16mm_interpretation_insertion_mm']=tail-gap+C
hypothesis['nominal_in_catalog_window']=3.68<=insertion<=6.35
hypothesis['sensitivity_in_catalog_window']=3.68<=insertion-uncertainty and insertion+uncertainty<=6.35
# Stock footprint reservation arithmetic only; no physical fit accepted.
width=5.95;length=67.55;spacing=5.08
area={'individual_courtyards_sum_mm2':2*width*length,'pair_courtyard_union_mm2':(width+spacing)*length,'courtyard_overlap_width_mm':width-spacing,'nominal_body_gap_mm':spacing-4.95,'body_width_source_status':'Reference dimension, not a guaranteed maximum. No body-clearance acceptance.'}
sources={
 'eps_board':'hardware/eps/kicad/eps.kicad_pcb',
 'comms_board':'hardware/comms/kicad/transceiver.kicad_pcb',
 'comms_footprint':'hardware/comms/kicad/lib/Ember_RF.pretty/Samtec_ESQ-126-39-G-D_2x26_P2.54mm.kicad_mod',
 'canonical_pinmap':'system/interfaces/cskb_pinmap.md',
}
report={'status':'GEOMETRY_RECONCILIATION_NOT_MATING_OR_FLIGHT_ACCEPTANCE','source_hashes':{k:{'path':v,'sha256':sha(ROOT/v)} for k,v in sources.items()},'matched_physical_pads':104,'maximum_coordinate_delta_mm':maxdelta,'centers_board_xy_mm':centers,'header_center_separation_mm':separation,'pumpkin_reference_separation_mm':pumpkin_sep,'user_decisions':{'date':'2026-10-24','clear_gap_mm':16,'retain_ember_header_spacing_mm':5.08,'mechanical_compatibility_exception_approved':True},'height_hypothesis':hypothesis,'footprint_reservation':area,'peer_CAN_mismatch':{'actual_comms_H1':{str(n):next(x['comms_net'] for x in rows if x['header']=='H1' and x['pin']==n) for n in [1,2,3,4,51,52]},'actual_comms_H2':{str(n):next(x['comms_net'] for x in rows if x['header']=='H2' and x['pin']==n) for n in [49,50]},'eps_rev_b_required':{'H1.51':'CAN_H','H1.52':'CAN_L','H2.49':'CAN_B_H','H2.50':'CAN_B_L'},'disposition':'Preserve canonical EPS RevB bus pins. COMMS electrical migration/peer verification required; no COMMS native change authorized or made.'},'pads':rows}
(HERE/'results.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS:104 physical pad positions match;5.08mm EMBER geometry preserved by explicit user decision. Height corners and peerCAN remain open.')
