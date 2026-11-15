"""Generate native Yamcs OPI overview and editable parameter tables."""
import json
from pathlib import Path
import shutil
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
D = json.loads((ROOT.parent / 'ember/dictionary.json').read_text())
BG = '#111b2a'
CARD = '#1c293b'
WHITE = '#f4f6f9'
MUTED = '#aab9ca'
ORANGE = '#ffac60'
BLUE = '#88c9df'


def generate(destination, instance="ember"):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    display = ET.Element('display', typeId='org.csstudio.opibuilder.Display', version='1.0.0')

    def prop(parent, name, value):
        child = parent.find(name)
        if child is None:
            child = ET.SubElement(parent, name)
        child.text = str(value).lower() if isinstance(value, bool) else str(value)

    def color(parent, name, value):
        c = ET.SubElement(parent, name)
        ET.SubElement(c, 'color', red=str(int(value[1:3],16)), green=str(int(value[3:5],16)), blue=str(int(value[5:7],16)))

    def font(parent, size, bold=False, mono=False):
        f = ET.SubElement(parent, 'font')
        ET.SubElement(f, 'opifont.name', fontName='Liberation Mono' if mono else 'Liberation Sans', height=str(size), style='1' if bold else '0').text = 'EMBER'

    for key, value in {'widget_type':'Display','name':'EMBER bench overview','width':1000,'height':640,'show_grid':False,'auto_zoom_to_fit_all':True}.items():
        prop(display,key,value)
    color(display,'background_color',BG)
    for tag in ('scripts','rules','actions'):
        ET.SubElement(display,tag,**({'hook':'false','hook_all':'false'} if tag=='actions' else {}))
    macros=ET.SubElement(display,'macros'); prop(macros,'include_parent_macros',True)
    auto=ET.SubElement(display,'auto_scale_widgets')
    for key,v in {'auto_scale_widgets':False,'min_width':-1,'min_height':-1}.items(): prop(auto,key,v)

    def widget(kind, name, x, y, w, h):
        e = ET.SubElement(display,'widget',typeId='org.csstudio.opibuilder.widgets.'+kind,version='1.0.0')
        for key,value in {'widget_type':{'TextUpdate':'Text Update','ActionButton':'Action Button'}.get(kind,kind),'name':name,'x':x,'y':y,'width':w,'height':h,'visible':True,'enabled':True,'border_style':0,'border_width':0}.items():
            prop(e,key,value)
        prop(e,'wuid','ember-'+str(len(display)))
        defaults={'horizontal_alignment':0,'wrap_words':False,'tooltip':'','format_type':0,'image':'','push_action_index':0,'release_action_index':0,'toggle_button':False,'gradient':False,'border_alarm_sensitive':False,'foreground_alarm_sensitive':False,'background_alarm_sensitive':False,'fill_level':0,'horizontal_fill':False,'line_style':0}
        for key,v in defaults.items(): prop(e,key,v)
        for tag in ('scripts','rules','actions'):
            ET.SubElement(e,tag,**({'hook':'false','hook_all':'false'} if tag=='actions' else {}))
        scale=ET.SubElement(e,'scale_options')
        for key,v in {'width_scalable':True,'height_scalable':True,'keep_wh_ratio':False}.items(): prop(scale,key,v)
        return e

    def label(text, x, y, w=1000, h=24, size=13, fg=MUTED, bold=False):
        e=widget('Label',text,x,y,w,h)
        prop(e,'text',text); prop(e,'transparent',True); prop(e,'vertical_alignment',1)
        color(e,'foreground_color',fg); font(e,size,bold)
        return e

    def box(x,y,w,h):
        e=widget('Rectangle','Panel',x,y,w,h)
        color(e,'background_color',CARD); color(e,'foreground_color',CARD)
        prop(e,'line_width',0); prop(e,'fill',True)

    def button(text,path,x,w=196):
        e=widget('ActionButton',text,x,652,w,42)
        prop(e,'text',text); color(e,'background_color','#30445e'); color(e,'foreground_color',WHITE); font(e,12,True)
        actions=e.find('actions')
        a=ET.SubElement(actions,'action',type='OPEN_DISPLAY')
        macros=ET.SubElement(a,'macros'); prop(macros,'include_parent_macros',True)
        prop(a,'path',path); prop(a,'mode',0); prop(a,'description',text)

    def new(title, subtitle):
        nonlocal display
        for child in list(display.findall('widget')):display.remove(child)
        prop(display,'name',title)
        label('EMBER  /  '+title.upper(),22,16,950,36,24,WHITE,True)
        label(('FLIGHT · UHF / LTE' if instance=='ember' else 'BENCH · IHU SERIAL')+'   /   '+subtitle,22,56,950,22,11,BLUE)
        pages=[('Overview','Overview.opi'),('Power','EPS.opi'),('Payload','Payload.opi'),
               ('Devices & firmware','Devices.opi')]
        if instance=='ember':
            pages.append(('IHU Faults','IHU-Faults.opi'))
        step=160 if instance=='ember' else 196
        for i,(text,path) in enumerate(pages):
            button(text,path,22+i*step,step-10)
            prop(display.findall('widget')[-1],'y',90)
            prop(display.findall('widget')[-1],'height',32)
        link_x=22+len(pages)*step
        web('Links','/links',link_x,90,978-link_x)
    def web(text,path,x,y,w):
        e=widget('ActionButton',text,x,y,w,32);prop(e,'text',text)
        color(e,'background_color','#30445e');color(e,'foreground_color',WHITE);font(e,11,True)
        a=ET.SubElement(e.find('actions'),'action',type='OPEN_WEBPAGE')
        prop(a,'hyperlink',path+('?c='+instance+'__realtime')+('&system=%2Fember' if path=='/commanding/send' else ''))
    def nav(text,path,x,y,w=210):
        button(text,path,x,w);prop(display.findall('widget')[-1],'y',y);prop(display.findall('widget')[-1],'height',32)
    def script(text,pvs,filename,x,y,w,h=24,size=12):
        e=label(text,x,y,w,h,size,WHITE)
        path=ET.SubElement(e.find('scripts'),'path',pathString='scripts/'+filename,checkConnect='false',sfe='false',seoe='false')
        for pv in pvs:ET.SubElement(path,'pv',trig='true').text=pv if pv.startswith('sim://') else '/ember/'+pv
        return e
    def observed(pv,x,y,w=270,size=20):
        return script('No observation',[pv],'boolean-value.js' if pv in ('PAYLOAD_STATUS_ready','PAYLOAD_PING_RESULT_echo_ok','POWER_STATUS_adc_valid','POWER_STATUS_conversion_valid') else 'observed-value.js',x,y,w,32,size)
    def stamp(pv,x,y,w=280):
        script('No observation',[pv],'sample-time.js',x,y,w,22,10)
    def fresh(pv,x,y,w=280):
        script('NO OBSERVATION',[pv],'last-observation.js' if pv.startswith(('HEARTBEAT_','SYSTEM_STATUS_')) else 'observation-status.js',x,y,w,24,11)
    def eps(pv,x,y,w=260,size=21):
        script('Unavailable',['POWER_STATUS_'+pv,'POWER_STATUS_conversion_valid'],'eps-value.js',x,y,w,34,size)
    def save(name):
        page=ET.fromstring(ET.tostring(display))
        # Fit the full page beside the Yamcs sidebar at 1280x720.
        for key in ('width','height'):prop(page,key,round(int(page.findtext(key))*.95))
        for e in page.findall('widget'):
            for key in ('x','y','width','height'):prop(e,key,round(int(e.findtext(key))*.95))
            for f in e.findall('font/opifont.name'):f.set('height',str(max(10,round(int(f.get('height'))*.95))))
        ET.indent(page);ET.ElementTree(page).write(destination/name,encoding='utf-8',xml_declaration=True)
    def footer(text):label(text,22,608,950,22,10,MUTED)

    new('Overview','Last observations in this environment')
    for x in (22,348,674):box(x,140,304,292)
    if instance=='ember':
        label('HEARTBEAT / PRODUCER',40,154,270,24,12,BLUE,True)
        fresh('HEARTBEAT_mode',40,184,270)
        label('Producer boot ID',40,217,270,20,11);observed('HEARTBEAT_source_boot_id',40,239)
        label('Producer uptime',40,281,270,20,11);observed('HEARTBEAT_uptime_ms',40,303)
        label('Last packet received',40,365,270,20,10);stamp('HEARTBEAT_mode',40,388)
        label('SYSTEM / IHU',366,154,270,24,12,BLUE,True)
        fresh('SYSTEM_STATUS_mode',366,184,270)
        label('Last reported mode',366,217,270,20,11);observed('SYSTEM_STATUS_mode',366,239)
        label('Last reported configuration',366,281,270,20,11);observed('SYSTEM_STATUS_configuration',366,303,size=17)
        stamp('SYSTEM_STATUS_mode',366,388)
    else:
        label('SERIAL / EPS READOUT',40,154,270,24,12,BLUE,True)
        fresh('POWER_STATUS_readout_valid',40,184,270)
        label('ADC conversion valid',40,217,270,20,11);observed('POWER_STATUS_conversion_valid',40,239)
        label('Readout age at packet',40,281,270,20,11);observed('POWER_STATUS_readout_age_ms',40,303)
        stamp('POWER_STATUS_readout_valid',40,388)
        label('PAYLOAD / LAST REPLY',366,154,270,24,12,BLUE,True)
        fresh('PAYLOAD_STATUS_ready',366,184,270)
        label('Ready at reply',366,217,270,20,11);observed('PAYLOAD_STATUS_ready',366,239)
        label('Reported payload boot ID',366,281,270,20,11);observed('PAYLOAD_STATUS_reported_boot_id',366,303,size=17)
        stamp('PAYLOAD_STATUS_ready',366,388)
    label('POWER / EPS',692,154,270,24,12,BLUE,True)
    fresh('POWER_STATUS_readout_valid',692,184,270)
    for title,pv,y in [('Charger input','input_mv',217),('Battery pack','battery_mv',281),('Power-path output','output_mv',345)]:
        label(title,692,y,260,20,11);eps(pv,692,y+21,260,20)
    box(22,450,956,105)
    if instance == 'ember':
        script('UHF schedule · waiting for current IHU status', [
            'UHF_SCHEDULE_STATUS_enabled', 'UHF_SCHEDULE_STATUS_listen_seconds',
            'UHF_SCHEDULE_STATUS_telemetry_seconds', 'UHF_SCHEDULE_STATUS_cycle_offset_ms',
            'UHF_SCHEDULE_STATUS_source_boot_id', 'IHU_STATUS_source_boot_id', 'sim://ramp(0,10,1)',
        ], 'uhf-countdown.js', 40, 460, 920, 24, 13)
        label('LAST UHF GPS SAMPLE',40,489,350,20,11,BLUE,True)
        stamp('GPS_STATUS_status',572,489,370)
        script('No GPS observation', ['GPS_STATUS_'+field for field in
            ('status','latitude_deg','longitude_deg','altitude_msl_m','satellites')],
            'gps-summary.js',40,514,920,24,12)
        nav('System raw / history','System.par',22,568)
        web('UHF commands','/commanding/send',250,568,210)
    else:
        label('EPS is polled through the IHU USB bridge. Payload replies are requested.',40,475,914,21,11)
        label('EPS packet times reflect ground reception.',40,508,914,21,11)
        nav('Power raw / quality','EPS.par',22,568)
        web('Payload commands','/commanding/send',250,568,210)
    web('Command history','/commanding/history',478,568,210)
    footer('Times are ground reception times. NO OBSERVATION and EXPIRED do not mean a device is healthy or failed.')
    save('Overview.opi')

    new('Power','EPS readout · charger state · measurement quality')
    script('No EPS observation',['POWER_STATUS_readout_valid','POWER_STATUS_conversion_valid','POWER_STATUS_link'],'eps-quality.js',22,139,956,30,14)
    stamp('POWER_STATUS_readout_valid',22,174,465)
    script('No readout',['POWER_STATUS_readout_age_ms'],'eps-age.js',22,199,956,24,10)
    for x,y,title,pv in [(22,239,'Charger VIN','input_mv'),(348,239,'Battery pack','battery_mv'),(674,239,'Power-path output','output_mv'),(22,345,'Input current *','input_ua'),(348,345,'Battery current *','battery_ua'),(674,345,'Charger die temperature','die_temp_mc')]:
        box(x,y,304,93);label(title,x+16,y+12,270,20,11,BLUE,True);eps(pv,x+16,y+40,270)
    for x,title,pv in [(22,'Charger state bits','raw_charger_state'),(348,'JEITA region','raw_jeita_region'),(674,'ADC valid flag','adc_valid')]:
        label(title,x,454,285,21,11);observed('POWER_STATUS_'+pv,x,478,285,17)
    label('* Currents use provisional sense-resistor values; confirm calibration before relying on them.',22,520,956,22,10,ORANGE)
    label('No battery thermistor fitted. Charger die temperature is not battery temperature.',22,545,956,22,10,ORANGE)
    nav('Power raw / quality','EPS.par',22,574,218)
    label('Read-only telemetry. No charger controls are sent by these displays.',260,579,715,22,10)
    footer('Voltage and current are hidden when packet quality/conversion is invalid. Packet age is not ADC conversion age.')
    save('EPS.opi')

    new('Payload','Fire check results · STATIC_STUB means no algorithm has run')
    for x in (22,510):box(x,140,468,330)
    label('LAST STATUS / HEARTBEAT',40,154,430,22,12,BLUE,True)
    fresh('PAYLOAD_STATUS_ready',40,184,430)
    for title,pv,y in [('Ready at reply','ready',215),('Payload boot ID','reported_boot_id',256),('Payload uptime (ms)','reported_uptime_ms',297),('Fragment errors','fragment_errors',338),('Detector profile','detector_profile_id',379)]:
        label(title,40,y,240,22,11);observed('PAYLOAD_STATUS_'+pv,290,y-3,170,17)
    stamp('PAYLOAD_STATUS_ready',40,435,430)
    label('LAST VERIFIED PING',528,154,430,22,12,BLUE,True)
    fresh('PAYLOAD_PING_RESULT_echo_ok',528,184,430)
    for title,pv,y in [('Bytes','bytes',222),('Echo matched','echo_ok',276),('Round-trip time (ms)','round_trip_ms',330)]:
        label(title,528,y,240,22,11);observed('PAYLOAD_PING_RESULT_'+pv,778,y-3,178,17)
    stamp('PAYLOAD_PING_RESULT_echo_ok',528,435,430)
    label('LAST FIRE CHECK',22,483,180,24,12,BLUE,True)
    observed('PAYLOAD_FIRE_RESULT_result',205,479,180,17)
    observed('PAYLOAD_FIRE_RESULT_execution_mode',395,479,200,17)
    stamp('PAYLOAD_FIRE_RESULT_result',610,481,360)
    label('STATIC_STUB returns NO_FIRE without running the detector. Missing replies remain UNKNOWN.',22,513,956,24,11,ORANGE)
    if instance == 'ember':
        label('CAPTURE GPS',22,540,140,20,11,BLUE,True)
        script('No GPS observation', ['PAYLOAD_FIRE_TAGGED_'+field for field in
            ('gps_status','latitude_deg','longitude_deg','altitude_msl_m','satellites','check_id')],
            'gps-summary.js',165,538,813,23,11)
    else:
        label('Bench path: Ground Pi Yamcs → local USB → IHU → CAN A → payload Pi.',22,541,956,20,10)
    nav('Payload raw / history','Payload.par',22,568)
    web('Send payload command','/commanding/send',250,568,235);web('Command history','/commanding/history',503,568,210)
    footer('Payload firmware identity and source commit are consolidated on Devices & firmware.')
    save('Payload.opi')

    new('Devices & firmware','IHU discovery snapshot and last reported build identities')
    script('No discovery snapshot',['DEVICE_STATUS_payload_version'],'device-freshness.js',22,138,956,24,11)
    for text,x,w in [('Device / interface',22,290),('State at snapshot',344,200),('Age at snapshot',564,200),('Timeouts',804,174)]:label(text,x,176,w,22,11,BLUE,True)
    for i,(prefix,title) in enumerate([('eps','EPS / I2C1'),('eps_next','EPS_NEXT / CAN (planned)'),('comms','Transceiver / CAN A'),('lte','LTE / CAN A'),('payload','Payload / CAN A')]):
        y=208+i*31;label(title,22,y,300,24,11)
        observed('DEVICE_STATUS_'+prefix+'_state',344,y,200,12)
        script('No observation',['DEVICE_STATUS_'+prefix+'_seen','DEVICE_STATUS_'+prefix+'_age_ms'],'device-age.js',564,y,210,24,11)
        observed('DEVICE_STATUS_'+prefix+'_timeouts',804,y,174,12)
    stamp('DEVICE_STATUS_payload_version',22,366,450)
    label('Snapshot states are sampled by IHU; NOT_SEEN can be expected for planned or unconnected devices.',22,392,956,21,10)
    # Single compact fleet identity table replaces three dedicated firmware pages.
    for text,x,w in [('Firmware component',22,230),('Release / build',258,220),('Full source commit',490,488)]:label(text,x,426,w,22,11,BLUE,True)
    identities = [('COMMS_FIRMWARE','Transceiver MCU'),('LTE_CAN_FIRMWARE','LTE CAN MCU'),
                  ('LTE_MODEM_FIRMWARE','Walter MCU'),('PAYLOAD_FIRMWARE','Payload Pi')]
    if instance == 'ember':
        identities.insert(0, ('IHU_FIRMWARE','IHU MCU'))
    for i,(prefix,title) in enumerate(identities):
        y=450+i*24;label(title,22,y,225,24,11)
        script('No identity',[prefix+'_'+n for n in ('version_major','version_minor','version_patch','dirty')],'firmware-version.js',258,y,225,24,10)
        script('No identity',[prefix+'_git_sha_'+str(n) for n in range(5)],'firmware-git.js',490,y,488,24,10)
    nav('Discovery raw / boot IDs','Devices.par',22,578,230)
    nav('All firmware / timestamps','Firmware.par',270,578,250)
    footer('Firmware rows are last-known reports, not live attestation. Raw table includes each identity’s receive time and boot ID.')
    if instance=='ember':
        nav('Radio configuration','Radio-Config.opi',538,578,230)
    save('Devices.opi')

    if instance=='ember':
        new('Radio configuration','Last transceiver readback over UHF')
        web('Request radio configuration','/commanding/send/ember/REQUEST_RADIO_CONFIG',748,142,230)
        box(22,140,710,116)
        for i,(title,key) in enumerate((('Radio boot ID','radio_boot_id'),('Behavior','behavior'),
                                        ('Supported profiles','supported_profiles'))):
            x=38+230*i
            label(title,x,151,215,24)
            observed('RADIO_CONFIG_'+key,x,177,222,16)
        stamp('RADIO_CONFIG_radio_boot_id',38,218,410)
        label('Setting',44,276,330,24,13,WHITE,True)
        label('Factory default',396,276,270,24,13,WHITE,True)
        label('Active',694,276,270,24,13,WHITE,True)
        for i,(title,key) in enumerate((('Profile','profile'),('Nominal RX LO','rx_lo_hz'),
                                        ('Nominal TX carrier','tx_carrier_hz'),('Symbol rate','symbol_rate'))):
            y=308+i*54
            box(22,y,956,48)
            label(title,44,y+10,335,24)
            observed('RADIO_CONFIG_default_'+key,396,y+7,270,16)
            observed('RADIO_CONFIG_active_'+key,694,y+7,270,16)
        for i,(title,key) in enumerate((('Trial state','trial_state'),('Candidate','candidate_profile'),
                                        ('Confirmation token','confirmation_token'),('Time remaining at report','remaining_ms'))):
            x=22+240*i
            label(title,x,539,230,22)
            observed('RADIO_CONFIG_'+key,x,563,230,15)
        footer('Confirm only with the token in a fresh TRIAL readback. A token of zero means no confirmation is available.')
        save('Radio-Config.opi')

        new('IHU Faults','Last fault history received over UHF')
        web('Request fault history','/commanding/send/ember/REQUEST_IHU_FAULTS',784,142,194)
        box(22,140,748,94)
        for index, (caption, pv) in enumerate([
            ('IHU boot ID','source_boot_id'), ('Snapshot uptime','uptime_ms'),
            ('Retained faults','count'), ('Faults this boot','total'),
        ]):
            x=38+index*182
            label(caption,x,150,170,22)
            observed('IHU_FAULTS_'+pv,x,175,170,17)
        stamp('IHU_FAULTS_count',38,204,410)
        label('Fault',64,248,510,23,13,WHITE,True)
        label('Fault uptime (ms)',714,248,250,23,13,WHITE,True)
        for row in range(1,17):
            y=274+(row-1)*19
            if row % 2: box(22,y,956,19)
            script('',[f'IHU_FAULTS_fault{row}_code'],'ihu-fault-value.js',64,y,620,19,11)
            script('',[f'IHU_FAULTS_fault{row}_code',f'IHU_FAULTS_fault{row}_uptime_ms'],
                   'ihu-fault-value.js',714,y,250,19,11)
        footer('Fault history is retained in IHU RAM for the current boot. Entries are oldest first.')
        save('IHU-Faults.opi')


    groups={'Payload.par':['PAYLOAD_STATUS','PAYLOAD_PING_RESULT','PAYLOAD_FIRE_RESULT'], 'Devices.par':['DEVICE_STATUS'],
            'Firmware.par':['COMMS_FIRMWARE','LTE_CAN_FIRMWARE','LTE_MODEM_FIRMWARE','PAYLOAD_FIRMWARE'],
            'System.par':['HEARTBEAT','SYSTEM_STATUS','COMM_STATUS'],
            'Command-reports.par':['COMMAND_RESPONSE'], 'EPS.par':['POWER_STATUS']}
    if instance == 'ember':
        groups['Payload.par'].append('PAYLOAD_FIRE_TAGGED')
        groups['Firmware.par'].insert(0, 'IHU_FIRMWARE')
        groups['System.par'] += ['GPS_STATUS','UHF_SCHEDULE_STATUS']
    for filename,names in groups.items():
        parameters=[]
        for m in D['messages']:
            if m['name'] in names:
                parameters += ['/ember/'+m['name']+'_'+f['name'] for f in m['fields']]
                if filename not in ('EPS.par','Command-reports.par'):
                    parameters += ['/ember/'+m['name']+'_'+n for n in ('source_boot_id','uptime_ms')]
        obj={'$schema':'https://yamcs.org/schema/parameter-table.schema.json','scroll':filename=='Command-reports.par','bufferSize':40,'parameters':parameters}
        (destination/filename).write_text(json.dumps(obj,indent=2)+'\n')
    scripts=destination/'scripts';scripts.mkdir(exist_ok=True)
    retired = retired_assets(instance)
    for p in (ROOT/'display-scripts').glob('*.js'):
        if f'scripts/{p.name}' not in retired and (instance=='ember' or p.name!='ihu-fault-value.js'):
            shutil.copy2(p,scripts/p.name)
    for name in retired:
        path=destination/name
        if path.exists():path.unlink()
    print('Generated EMBER operator displays and native diagnostic tables:',destination)


RETIRED_DISPLAYS=('Telemetry.opi','LTE.opi','Comms-Firmware.opi','LTE-CAN-Firmware.opi','LTE-Modem-Firmware.opi',
                  'Payload-Ground-Build.opi','payload-ground-build.json','Comms.par','LTE-Firmware.par')

def retired_assets(instance):
    if instance == 'ember-bench':
        return RETIRED_DISPLAYS + ('scripts/gps-summary.js', 'scripts/uhf-countdown.js')
    return RETIRED_DISPLAYS


if __name__=='__main__':generate(sys.argv[1])
