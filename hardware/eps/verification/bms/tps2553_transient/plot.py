"""Standard ReportLab LinePlot charts of decimated diagnostic waveforms."""
from pathlib import Path
import csv
from reportlab.pdfgen.canvas import Canvas
from reportlab.graphics.shapes import Drawing, String
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics import renderPDF
from reportlab.lib.colors import HexColor

HERE = Path(__file__).resolve().parent
OUT = HERE/'output'/'pdf'
OUT.mkdir(parents=True,exist_ok=True)
COLORS = ['#2166ac','#b2182b','#1b7837']

def chart(canvas, title, cases, window, yrange, key, units, notes):
    d = Drawing(520,240)
    p = LinePlot()
    p.x, p.y, p.width, p.height = 55, 35, 445, 170
    p.data = []
    for case in cases:
        with (HERE/(case+'.csv')).open() as f:
            rows = list(csv.DictReader(f))
        p.data.append([(float(r['time_s'])*1000,float(r[key])) for r in rows if window[0]<=float(r['time_s'])*1000<=window[1]])
    for i in range(len(cases)):
        p.lines[i].strokeColor = HexColor(COLORS[i])
        p.lines[i].strokeWidth = 1
    p.xValueAxis.valueMin,p.xValueAxis.valueMax = window
    p.yValueAxis.valueMin,p.yValueAxis.valueMax = yrange
    p.xValueAxis.labelTextFormat = '%.2f' if window[1]-window[0]<1 else '%.0f'
    p.yValueAxis.labelTextFormat = '%.2f'
    p.xValueAxis.labels.fontSize = p.yValueAxis.labels.fontSize = 8
    d.add(p)
    d.add(String(55,225,title,fontSize=11))
    d.add(String(230,10,'Time (ms)',fontSize=9))
    d.add(String(0,212,units,fontSize=9))
    renderPDF.draw(d,canvas,35,310)
    canvas.setFont('Helvetica',8)
    for i,case in enumerate(cases):
        canvas.setFillColor(HexColor(COLORS[i]))
        canvas.drawString(50,280-i*14,case)
    canvas.setFillColor(HexColor('#222222'))
    canvas.setFont('Helvetica',9)
    for i,line in enumerate(notes):
        canvas.drawString(40,210-i*15,line)
    canvas.setFont('Helvetica',8)
    canvas.drawString(40,55,'TI nominal switch model with XNOR syntax adapter; synthetic source and converter loads.')
    canvas.drawString(40,42,'Decimated plots. Extracted extrema use full raw data. No UCC or system qualification.')
    canvas.showPage()

c = Canvas(str(OUT/'waveforms.pdf'),pagesize=(595,600))
chart(c,'3.3 V source: upper-capacitance startup',
      ['startup_3v3_115k_upperC','startup_3v3_210k_upperC','startup_3v3_115k_100mA'],
      (0,12),(0,3.4),'reservoir_V','Reservoir (V)',
      ['All three nominal cases reach a steady reservoir above 3.0 V.',
       'The 210k setting works in this nominal case; it has less current/timing reserve.',
       'Neither trace establishes the complete UCC soft-start or PVT envelope.'])
chart(c,'Imposed bursts: 3.3 V source and conditional 54.38 uF bank',
      ['bursts_3v3_115k_lowC'],(12,12.8),(3.0,3.3),'reservoir_V','Reservoir (V)',
      ['Minimum in the settled full raw trace: 3.0936 V.',
       'Load is an imposed 0.8 A pulse pattern, not validated UCC behavior.',
       'The stiff-source assumption leaves actual essential-source response open.'])
chart(c,'5 V alternative: imposed bursts with a smaller bank',
      ['bursts_5v_115k_smallC'],(12,12.8),(4.0,5.0),'reservoir_V','Reservoir (V)',
      ['Minimum in the settled full raw trace: 4.1376 V.',
       'The smaller bank permits model current overshoot; RILIM is not a peak bound.',
       'This alternative would make BMS telemetry depend on recovery +5V.'])
chart(c,'Output short, latched state and commanded restart',
      ['short_latch_reset_3v3'],(8,60),(0,3.4),'reservoir_V','Reservoir (V)',
      ['Short applied at 10 ms and removed at 30 ms.',
       'EN low from 35 to 55 ms clears the latch; the output restarts.',
       'This demonstrates latch clearing, not a fully discharged UCC power cycle.'])
chart(c,'Output short: initial switch-current pulse',
      ['short_latch_reset_3v3'],(9.995,10.05),(0,2.8),'source_A','Switch input (A)',
      ['Full raw current peak: 2.605 A before limiting.',
       'Shared reservoir is imposed at 96 uF behind a stiff 50 milliohm source.',
       'No maximum response-time or MOSFET/resistor survival acceptance follows.'])
chart(c,'Output short: internal model timer and latch',
      ['short_latch_reset_3v3'],(8,60),(0,1.1),'timer_V','Model timer (V)',
      ['Internal model-node voltage is diagnostic; it is not an external test point.',
       'FAULT is low in the latched interval; EN toggling restores operation.',
       'Temperature, source collapse and a self-consistent UCC load remain open.'])
c.save()
print(OUT/'waveforms.pdf')
