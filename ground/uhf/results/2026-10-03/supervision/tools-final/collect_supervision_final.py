from pathlib import Path
import subprocess,json,shutil,shlex
p=Path('/Users/nick/Documents/ChatGPT/EMBER/work/sdrb-can-adapter/ground/uhf/results/2026-10-03/supervision')
for number,local in [(3,'supervision-proof-02'),(4,'supervision-proof-03')]:
 d=p/f'attempt-{number}';d.mkdir(exist_ok=True)
 for f in (Path('/tmp/ember-uhf-tools')/local).iterdir():
  if f.is_file():shutil.copyfile(f,d/f.name)
 if number==3:
  sr='/home/petalinux/ember-uhf-supervised/20240228T041230Z-58fe2465810c';gr='/home/ngrabbs/work/ember-uhf-supervised/20261003T211919Z-b96595c4d3bd'
 else:
  r=json.loads((d/'session.json').read_text())['runs'][0];sr=r['sdrb']['run'];gr=r['ground']['run']
 dest=p/f'run-{number}';dest.mkdir(exist_ok=True)
 subprocess.run(['scp','-r','ngrabbs@192.168.1.251:'+gr,str(dest/'ground')],check=True,capture_output=True)
 source=sr.removeprefix('/home/petalinux/')
 for name in ('','/radio','/can','/forward'):
  subprocess.run(['python3','/tmp/ember-uhf-tools/collect_supervision_short.py',source+name,str(dest/'sdrb')+name],check=True)
 if number==4:
  (dest/'ihu').mkdir(exist_ok=True)
  for name in ('packets.jsonl','result.json','ihu.txt'):
   subprocess.run(['scp','ngrabbs@192.168.1.252:/home/ngrabbs/work/ember-sdrb-adapter-20261003/system/sdrb/evidence/supervision-native-4/'+name,str(dest/'ihu'/name)],check=True,capture_output=True)
 print('COLLECTED_RUN',number,flush=True)
(p/'archive.json').write_text(subprocess.run(['curl','-fsS','http://192.168.1.251:8090/api/archive/ember-uhf/packets?limit=100'],check=True,capture_output=True,text=True).stdout+'\n')
cmd='ip -details link show can0; ip -details link show can1; test ! -S ~/.cache/ember-binary-radio/control.sock && echo RADIO_CONTROL_CLOSED; uhd_find_devices --args type=sdrb,mgmt_addr=127.0.0.1; systemctl --user show ember-uhf-sdrb.service -p ActiveState -p UnitFileState; loginctl show-user petalinux -p Linger; sha256sum ~/ember-uhf-20261003/radio_service.py ~/ember-uhf-20261003/headroom_mix.so ~/ember-uhf-20261003/supervisor.py'
r=subprocess.run(['ssh','ngrabbs@192.168.1.252','python3 /tmp/console.py --command '+shlex.quote(cmd)+' --wait 8'],check=True,capture_output=True,text=True)
cleanup=r.stdout
cmd='test -z "$(fuser /dev/bus/usb/004/003 2>/dev/null)" && echo LIBRESDR_FREE; sha256sum ~/work/ember-lte/images/usrp_b210_fpga.bin ~/work/ember-uhf-20261003/libresdr_live_rx.py ~/work/ember-uhf-20261003/supervisor.py; systemctl --user show ember-uhf-ground.service -p ActiveState -p UnitFileState; loginctl show-user ngrabbs -p Linger'
r=subprocess.run(['ssh','ngrabbs@192.168.1.251',cmd],check=True,capture_output=True,text=True)
(p/'cleanup-final.txt').write_text(cleanup+r.stdout)
cmd='journalctl -b --since "2026-10-03 21:05:20 UTC" --until "2026-10-03 21:05:35 UTC" --no-pager'
r=subprocess.run(['ssh','ngrabbs@192.168.1.251',cmd],check=True,capture_output=True,text=True)
(p/'logout-diagnosis.txt').write_text(r.stdout)
cmd='git -C /media/ngrabbs/BACKUP-A/sdrb-can-20260917/source-checkout status --porcelain'
r=subprocess.run(['ssh','ngrabbs@192.168.1.252',cmd],check=True,capture_output=True,text=True)
(p/'amsat-git-status-final.txt').write_text(r.stdout)
print('FINAL_EVIDENCE_COLLECTED',flush=True)
