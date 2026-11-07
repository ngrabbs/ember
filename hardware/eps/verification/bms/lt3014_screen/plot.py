"""Render diagnostic waveforms with ReportLab's standard LinePlot chart."""
from pathlib import Path
import csv
from reportlab.pdfgen.canvas import Canvas
from reportlab.graphics.shapes import Drawing,String
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics import renderPDF
from reportlab.lib.colors import HexColor
HERE=Path(__file__).resolve().parent
colors=['#2166ac','#b2182b','#1b7837']
def rows(name):
 with (HERE/(name+'.csv')).open() as f:return list(csv.DictReader(f))
def chart(c,title,names,window,yrange,ykey='output_V',ytitle='Output (V)'):
 d=Drawing(520,210);p=LinePlot();p.x=55;p.y=30;p.width=445;p.height=150
 p.data=[]
 for n in names:
  rs=rows(n);p.data.append([(float(r['time_s'])*1000,float(r[ykey])) for r in rs if window[0]<=float(r['time_s'])*1000<=window[1]])
 for j in range(len(names)):p.lines[j].strokeColor=HexColor(colors[j]);p.lines[j].strokeWidth=1
 p.xValueAxis.valueMin,p.xValueAxis.valueMax=window
 p.yValueAxis.valueMin,p.yValueAxis.valueMax=yrange
 p.xValueAxis.labelTextFormat='%.2f' if window[1]-window[0]<1 else '%.0f'
 p.yValueAxis.labelTextFormat='%.2f';p.xValueAxis.labels.fontSize=8;p.yValueAxis.labels.fontSize=8
 d.add(p);d.add(String(55,193,title,fontSize=11));d.add(String(235,8,'Time (ms)',fontSize=9));d.add(String(0,185,ytitle,fontSize=9))
 renderPDF.draw(d,c,36,c._pagesize[1]-260)
 c.setFont('Helvetica',8)
 for j,n in enumerate(names):c.setFillColor(HexColor(colors[j]));c.drawString(55,280-j*14,n)
 c.setFillColor(HexColor('#222222'));c.setFont('Helvetica',9)
 c.drawString(40,210,'Nominal LT3014 macromodel; imposed 4.8 V source and synthetic 3.5 / 8.5 mA load.')
 c.drawString(40,195,'No UCC33020, ISO1540, PVT, PCB parasitics or hardware qualification model.')
 c.showPage()
c=Canvas(str(HERE/'waveforms.pdf'),pagesize=(595,600))
base=['cout1u_prebias0','cout4.7u_prebias0','cout10u_prebias0']
chart(c,'Startup, input collapse and restart',base,(0,120),(0,3.5))
chart(c,'Rising load step: 3.5 to 8.5 mA in 1 us',base,(19.95,20.5),(3.20,3.34))
chart(c,'Falling load step: 8.5 to 3.5 mA in 1 us',base,(39.95,40.5),(3.20,3.34))
chart(c,'Finite-ramp externally prebiased output, then normal startup',['cout10u_prebias2'],(0,12),(0,3.5))
c.save()
