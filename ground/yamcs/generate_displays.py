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


def generate(destination):
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

    for key, value in {'widget_type':'Display','name':'EMBER bench overview','width':1120,'height':750,'show_grid':False,'auto_zoom_to_fit_all':True}.items():
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
        defaults={'horizontal_alignment':0,'wrap_words':False,'tooltip':'','format_type':0,'image':'','push_action_index':0,'release_action_index':0,'toggle_button':False,'gradient':False,'fill_level':0,'horizontal_fill':False,'line_style':0}
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

    def value(name,x,y,w=270,h=42,size=26,fg=WHITE):
        e=widget('TextUpdate',name,x,y,w,h)
        for key,v in {'pv_name':'/ember/'+name,'text':'—','transparent':True,'show_units':True,'precision':0,'precision_from_pv':False,'vertical_alignment':1,'border_alarm_sensitive':True}.items():
            prop(e,key,v)
        color(e,'foreground_color',fg); font(e,size,True,True)
        return e

    def scripted(text,pv,script,x,y,w,h=26,size=12):
        e=label(text,x,y,w,h,size=size,fg=WHITE)
        scripts=e.find('scripts')
        path=ET.SubElement(scripts,'path',pathString='scripts/'+script,checkConnect='true',sfe='false',seoe='false')
        ET.SubElement(path,'pv',trig='true').text='/ember/'+pv

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

    label('EMBER',28,20,280,48,32,WHITE,True)
    label('GROUND OPERATIONS  /  BENCH v1',29,70,720,26,13,ORANGE,True)
    label('Latest received values • click a value for history / plotting',28,111,1000,24,12)
    # Three primary panels: state, transport counters, last command report.
    box(28,149,336,432); box(380,149,336,432); box(732,149,360,432)
    label('01  /  SPACECRAFT STATE',48,169,295,28,13,BLUE,True)
    label('Mode',48,215,275); value('SYSTEM_STATUS_mode',48,241)
    label('Configuration',48,300,275); value('SYSTEM_STATUS_configuration',48,326,size=22)
    label('Telemetry period',48,385,275); value('HEARTBEAT_telemetry_period_ms',48,411)
    label('Boot ID',48,478,275); value('source_boot_id',48,504,size=20)

    label('02  /  ENDPOINT COUNTERS',400,169,300,28,13,BLUE,True)
    for title,pv,y in [('Commands received','COMM_STATUS_rx_packets',215),('Packets handed to USB','COMM_STATUS_tx_packets',286),('CRC errors','COMM_STATUS_crc_errors',357),('Dropped frames / packets','COMM_STATUS_dropped_packets',428)]:
        label(title,400,y,290); value(pv,400,y+25,size=24)
    label('RSSI',400,509,120); scripted('No sample received','COMM_STATUS_rssi_dbm','rssi.js',475,509,217,size=13)
    label('Counters reset on Pico reboot',400,547,285,h=20,size=11)

    label('03  /  LAST COMMAND REPORT',752,169,317,28,13,BLUE,True)
    label('Stage',752,215,300); value('COMMAND_RESPONSE_stage',752,241,315,size=24,fg=ORANGE)
    label('Reason',752,297,300); value('COMMAND_RESPONSE_reason',752,323,315,size=17)
    label('Command ID',752,378,140); value('COMMAND_RESPONSE_command_id',918,378,150,28,size=17)
    label('Parameter ID',752,421,150); value('COMMAND_RESPONSE_parameter_id',918,421,150,28,size=17)
    label('Result value',752,464,140); value('COMMAND_RESPONSE_value',918,464,150,28,size=17)
    scripted('No command report received','COMMAND_RESPONSE_stage','sample-time.js',752,512,315,size=11)
    label('Per-command outcome: open command history.',752,547,315,h=20,size=10)

    label('Last heartbeat received',28,603,215,h=24,size=12)
    scripted('No sample received','HEARTBEAT_telemetry_period_ms','sample-time.js',242,603,387,size=13)
    label('Uptime',745,603,90,h=24,size=12); value('uptime_ms',835,599,250,34,size=17)
    button('System details','System.par',28,164)
    button('Comms details','Comms.par',208,164)
    button('Command reports','Command-reports.par',388,164)
    # Navigation opens native commanding/history pages without issuing commands.
    for text,url,x,w in [('Command console','/commanding/send?c=ember__realtime&system=%2Fember',568,164),('Command history','/commanding/history?c=ember__realtime',748,164),('Link status','/links?c=ember__realtime',928,164)]:
        e=widget('ActionButton',text,x,652,w,42); prop(e,'text',text)
        color(e,'background_color','#30445e'); color(e,'foreground_color',WHITE); font(e,12,True)
        actions=e.find('actions'); a=ET.SubElement(actions,'action',type='OPEN_WEBPAGE'); prop(a,'hyperlink',url)
    label('BENCH DATA • values can remain cached after link loss; compare heartbeat time with mission time.',28,707,1070,h=24,size=11)
    ET.indent(display)
    ET.ElementTree(display).write(destination/'Overview.opi',encoding='utf-8',xml_declaration=True)
    header=['source_boot_id','uptime_ms','transaction_epoch','transaction_id','packet_sequence_raw']
    groups={'System.par':['HEARTBEAT','SYSTEM_STATUS'], 'Comms.par':['COMM_STATUS'], 'Command-reports.par':['COMMAND_RESPONSE']}
    for filename,names in groups.items():
        parameters=[] if filename=='Command-reports.par' else ['/ember/'+n for n in header]
        for m in D['messages']:
            if m['name'] in names:
                parameters += ['/ember/'+m['name']+'_'+f['name'] for f in m['fields']]
        # The common header is replaced by every packet. Omit it from response
        # tables: only native command history provides correlated outcomes.
        obj={'$schema':'https://yamcs.org/schema/parameter-table.schema.json','scroll':filename=='Command-reports.par','bufferSize':40,'parameters':parameters}
        (destination/filename).write_text(json.dumps(obj,indent=2)+'\n')
    scripts=destination/'scripts'; scripts.mkdir(exist_ok=True)
    for p in (ROOT/'display-scripts').glob('*.js'):
        shutil.copy2(p,scripts/p.name)
    print('Generated EMBER overview and three native parameter tables:',destination)


if __name__=='__main__':
    generate(sys.argv[1])
