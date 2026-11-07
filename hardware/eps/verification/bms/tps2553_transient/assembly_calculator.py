"""Read-only TI calculator translation with selected assembly inputs."""
from pathlib import Path
import argparse, hashlib, json, sys, warnings
import openpyxl
HERE = Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'ucc33020_startup'))
from check_calculator import startup, burst

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source',type=Path,required=True)
    a=ap.parse_args()
    digest=hashlib.sha256(a.source.read_bytes()).hexdigest()
    assert digest=='6001da9f256856a29aa73adbbccd0972da93cc199bcabfb3478e128e3e6531e3'
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        wb=openpyxl.load_workbook(a.source,data_only=False)
        cache=openpyxl.load_workbook(a.source,data_only=True)
    caps=json.loads((HERE.parent/'isolated_input_branch/capacitors.json').read_text())['banks']['isolated_5V']
    assembly=json.loads((HERE/'assembly_screen.json').read_text())
    c0=caps['zero_bias_upper_tolerance_temperature_and_reference_bias_peak_uF']+.115*1.1*1.15
    c5=caps['conditional_low_uF']
    rows=[]
    for vin in [3.0,3.3]:
        for load in [assembly['intermediate_allocation_with_bleed_A']*1000,50,100]:
            rs=startup(wb,vin=vin,c0=c0,c5=c5,load_type='Constant Current Load',load=load,threshold=0)
            reached=next((x['elapsed'] for x in rs if x['output']==5),None)
            rows.append(dict(vin_V=vin,load_mA=load,rise_us=reached,before16ms=reached is not None and reached<16000,
                             burst_at_allocated_load=burst(cache,vin,c5,3,assembly['intermediate_allocation_with_bleed_A']*1000)))
    result={'source_sha256':digest,'C0_upper_sensitivity_uF':c0,'C5_conditional_low_uF':c5,'cases':rows,
            'status':'TI calculator aid with selected capacitor/load inputs; not coupled startup qualification',
            'remaining':['LDO output-capacitor charging and current limit not modeled explicitly',
                         'Imposed constant loads are scenarios, not guaranteed maxima',
                         'Real source and TPS ramp/current-limit/timer not coupled to calculator',
                         'Cold full-power limits and arbitrary prebias unresolved']}
    (HERE/'assembly_calculator.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Six calculator cases:',[(r['vin_V'],round(r['load_mA'],3),r['rise_us']) for r in rows])

if __name__=='__main__':
    main()
