"""Independent whole-root CAN branch contract check on fresh CLI exports."""
import argparse
from collections import Counter
import copy
import fnmatch
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[1]/'rev_b/isolated_bms_integration'


def graph(path):
    root = ET.parse(path).getroot()
    comps = {c.get('ref'):c for c in root.findall('./components/comp')}
    assert len(comps)==len(root.findall('./components/comp'))
    pins={}
    nets={}
    for n in root.findall('./nets/net'):
        name=n.get('name');assert name not in nets
        nodes={(v.get('ref'),v.get('pin')) for v in n.findall('node')}
        assert len(nodes)==len(n.findall('node'))
        nets[name]=nodes
        for key in nodes:
            assert key not in pins,key
            pins[key]=name
    return comps,pins,nets


def fields(comp):
    return {f.get('name'):f.text for f in comp.findall('./fields/field')}


def component_bytes(comp):
    # The formerly last component gets a different outer XML indent when
    # components are appended; its contents/fields/UUIDs remain exact.
    comp=copy.deepcopy(comp)
    comp.tail=None
    return ET.tostring(comp)


def normalized_erc(path):
    data=json.loads(path.read_text())
    rows=[]
    for sheet in data['sheets']:
        for v in sheet['violations']:
            rows.append((sheet['path'],v['type'],v['severity'],v['description'],
                         tuple(sorted(i['description'] for i in v['items']))))
    return sorted(rows),data['ignored_checks']


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--netlist',type=Path,required=True)
    parser.add_argument('--erc',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--classes',type=Path,required=True)
    args=parser.parse_args()
    old,oldpins,oldnets=graph(BASE/'eps_rev_b.xml')
    comps,pins,nets=graph(args.netlist)
    assert len(comps)==305 and len(pins)==826 and len(nets)==166
    assert sum(not n.startswith('unconnected-') for n in nets)==150
    for ref,c in old.items():
        assert component_bytes(c)==component_bytes(comps[ref]),('old metadata/UUID changed',ref)
    new=set(comps)-set(old)
    assert len(new)==30
    assert Counter(r.rstrip('0123456789') for r in new)=={'U':4,'R':20,'C':4,'TP':2}
    moved={(r,p) for r in ['U101','U102'] for p in ['1','3','4','5','8']}
    moved.update((r,'1') for r in ['C104','C105','C106','C107','C108','C109'])
    assert len(moved)==16
    for key,net in oldpins.items():
        if key not in moved:assert pins[key]==net,('unexpected old terminal migration',key,net,pins[key])
    def net(ref,pin):return pins[(ref,str(pin))]
    def resistor(a,b,mpn):
        matches=[r for r in new if r.startswith('R') and {net(r,1),net(r,2)}=={a,b}
                 and fields(comps[r]).get('MFG P/N')==mpn]
        assert len(matches)==1,(a,b,mpn,matches)
        ref=matches[0]
        expected={'TNPW0603210KBEEA':210000,'CRCW12061R00FKEAHP':1,
                  'TNPW06031K00BEEA':1000,'TNPW0603100KBEEA':100000,
                  'TNPW060310K0BEEA':10000,'TNPW060347K0BEEA':47000}[mpn]
        match=re.fullmatch(r'([\d.]+)([kMR]?)',comps[ref].findtext('value'))
        assert match and float(match[1])*{'':1,'R':1,'k':1000,'M':1000000}[match[2]]==expected,ref
        f=fields(comps[ref])
        assert f['Tolerance']==('1%' if expected==1 else '0.1%'),ref
        assert f['PackageSize']==('1206' if expected==1 else '0603'),ref
        power=re.fullmatch(r'([\d.]+) W (general P70|P70)',f['Power'])
        assert power and float(power[1])==(.75 if expected==1 else .11),ref
        assert power[2]==('P70' if expected==1 else 'general P70'),ref
        return ref
    checked={}
    used=set()
    for ch,tcan,tps,inv,caps in [('A','U101','U1100','U1101',['C104','C105','C106']),
                                ('B','U102','U1102','U1103',['C107','C108','C109'])]:
        assert fields(comps[tps])['MFG P/N']=='TPS2553DBVR-1'
        assert comps[tps].findtext('footprint')==old['U900'].findtext('footprint')
        assert comps[tps].find('libsource').attrib==old['U900'].find('libsource').attrib
        assert fields(comps[inv])['MFG P/N']=='SN74LVC1G14DBVR'
        assert comps[inv].findtext('footprint')=='Package_TO_SOT_SMD:SOT-23-5_HandSoldering'
        rail='3V3_CAN'+ch
        assert net(tcan,3)==net(tcan,5)==rail
        assert net(tcan,2)==net(tps,2)==net(inv,3)=='GND'
        assert net(tps,1)==net(inv,5)=='+3V3'
        assert net(inv,2)=='EPS_CAN_'+ch+'_STB'
        assert net(inv,1).startswith('unconnected-') and nets[net(inv,1)]=={(inv,'1')}
        assert all(net(c,1)==rail and net(c,2)=='GND' for c in caps)
        ids=[]
        ids.append(resistor(net(tps,5),'GND','TNPW0603210KBEEA'))
        ids.append(resistor(net(tps,6),rail,'CRCW12061R00FKEAHP'))
        ids.append(resistor(net(inv,4),net(tps,3),'TNPW06031K00BEEA'))
        ids.append(resistor(net(tps,3),'GND','TNPW0603100KBEEA'))
        ids.append(resistor(net(tps,4),'+3V3','TNPW060310K0BEEA'))
        ids.append(resistor(rail,'GND','TNPW060310K0BEEA'))
        ids.append(resistor('EPS_CAN_'+ch+'_RX','+3V3','TNPW060347K0BEEA'))
        for label,pin in [('TX',1),('RX',4),('STB',8)]:
            ids.append(resistor('EPS_CAN_'+ch+'_'+label,net(tcan,pin),'TNPW06031K00BEEA'))
        assert len(ids)==10 and not set(ids)&used
        used.update(ids)
        tps_fault_points=[r for r in new if r.startswith('TP') and net(r,1)==net(tps,4)]
        assert len(tps_fault_points)==1
        # Neither channel's switched positive rail can be the other or the shared rail.
        assert rail not in ['+3V3','3V3_CAN'+('B' if ch=='A' else 'A')]
        assert not any(n[0]=='U100' for n in nets[net(tps,4)]),'invented MCU FAULT allocation'
        checked[ch]={'TPS':tps,'inverter':inv,'rail':rail,'new_resistors':sorted(ids),
                     'fault_testpoint':tps_fault_points[0],
                     'old_terminal_migrations':[(r,p,pins[(r,p)]) for r,p in sorted(moved) if r in [tcan]+caps]}
    assert len(used)==20
    addedcaps=[r for r in new if r.startswith('C')]
    assert len(addedcaps)==4
    for r in addedcaps:
        f=fields(comps[r])
        assert f['MFG P/N']=='GRM188R72A104KA35D'
        assert f['Dielectric']=='X7R' and f['Tolerance']=='10%' and f['Voltage']=='100 V' and f['PackageSize']=='0603'
        assert {net(r,1),net(r,2)}=={'+3V3','GND'}
    current,ignored=normalized_erc(args.erc)
    baseline,oldignored=normalized_erc(BASE/'erc.json')
    assert current==baseline and ignored==oldignored,'ERC signature/exclusions changed'
    assert Counter(row[2] for row in current)=={'error':10}
    classdata=json.loads(args.classes.read_text())
    membership={n:[c['name'] for c in classdata['netclasses']
                   if any(fnmatch.fnmatchcase(n,p) for p in c.get('patterns',[]))]
                for n in nets if not n.startswith('unconnected-')}
    assert all(len(v)==1 for v in membership.values()),membership
    result={'status':'INDEPENDENT_EXPORTED_GRAPH_CONTRACT_PASS_NOT_ELECTRICAL_OR_VISUAL_QUALIFICATION',
            'physical_parts':len(comps),'physical_endpoints':len(pins),'nets':len(nets),'functional_nets':150,
            'preserved_old_physical_parts':len(old),'new_parts':len(new),
            'old_terminal_migrations':len(moved),'channels':checked,
            'ERC_errors':10,'ERC_warnings':0,'unchanged_ERC_signature':True,
            'functional_net_classes':membership,
            'netlist_sha256':hashlib.sha256(args.netlist.read_bytes()).hexdigest(),
            'erc_sha256':hashlib.sha256(args.erc.read_bytes()).hexdigest()}
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(result['status'])


if __name__=='__main__':main()
