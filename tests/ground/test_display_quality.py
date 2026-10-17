"""Operator semantics: missing identity, expired samples and valid navigation."""
import json,os,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'ground/yamcs'))
from generate_displays import generate,D

class DisplayQuality(unittest.TestCase):
    def test_four_pages_use_known_parameters_and_environment_routes(self):
        known={m['name']+'_'+f['name'] for m in D['messages'] for f in m['fields']}
        known|={m['name']+'_'+f for m in D['messages'] for f in ('source_boot_id','uptime_ms')}
        for instance in ('ember','ember-bench'):
            with tempfile.TemporaryDirectory() as temp:
                generate(temp,instance)
                self.assertEqual({p.name for p in Path(temp).glob('*.opi')},{'Overview.opi','EPS.opi','Payload.opi','Devices.opi'})
                for path in Path(temp).glob('*.opi'):
                    root=ET.parse(path).getroot()
                    for pv in root.findall('.//pv'):
                        self.assertIn(pv.text.removeprefix('/ember/'),known)
                    for action in root.findall('.//actions/action'):
                        target=action.findtext('path')
                        if target:self.assertTrue((Path(temp)/target).exists(),target)
                        url=action.findtext('hyperlink')
                        if url:
                            self.assertIn('c='+instance+'__realtime',url)
                            self.assertIn(instance+'__realtime',url)
                    for widget in root.findall('widget'):
                        for start,size,bound in [('x','width','width'),('y','height','height')]:
                            self.assertLessEqual(int(widget.findtext(start))+int(widget.findtext(size)),int(root.findtext(bound)),path.name)

    def run_script(self,name,values):
        node=shutil.which('node')
        if not node:self.skipTest('Node.js required for display script semantics')
        source=(ROOT/'ground/yamcs/display-scripts'/name).read_text()
        program='''const pvs=JSON.parse(process.argv[1]);let result;
const Packages={org:{csstudio:{opibuilder:{scriptUtil:{}}}}};const importPackage=()=>{};
const widget={setPropertyValue:(key,value)=>{if(key==='text')result=value}};
const PVUtil={getTimeInMilliseconds:p=>p.time,getSeverity:p=>p.severity,getLong:p=>p.value,
getDouble:p=>p.value,getString:p=>String(p.value),getUnits:p=>p.unit||''};
'''+source+'\nprocess.stdout.write(String(result));'
        return subprocess.check_output([node,'-e',program,json.dumps(values)],text=True)

    def test_unreceived_identity_is_not_zero_release_or_zero_sha(self):
        missing=[{'time':0,'severity':-1,'value':0}]*5
        self.assertEqual(self.run_script('comms-version.js',missing[:4]),'No identity')
        self.assertEqual(self.run_script('comms-git.js',missing),'No identity received')
        live=[{'time':1000,'severity':0,'value':v} for v in (0,30,0,0)]
        self.assertEqual(self.run_script('comms-version.js',live),'0.30.0 clean')

    def test_expired_value_hidden_and_identity_marked_expired(self):
        stale={'time':1000,'severity':-1,'value':7.5,'unit':'V'}
        self.assertEqual(self.run_script('observed-value.js',[stale]),'—')
        self.assertEqual(self.run_script('observation-status.js',[stale]),'EXPIRED / UNAVAILABLE')
        identity=[dict(stale,value=v) for v in (1,2,3,0)]
        self.assertIn('expired',self.run_script('comms-version.js',identity))
        self.assertEqual(self.run_script('boolean-value.js',[stale]),'—')
        self.assertEqual(self.run_script('boolean-value.js',[{'time':1000,'severity':0,'value':1}]),'Yes')
        cached={'time':1000,'severity':0,'value':3}
        self.assertEqual(self.run_script('last-observation.js',[cached]),'LAST RECEIVED · CHECK TIME')

if __name__=='__main__':unittest.main()
