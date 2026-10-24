#!/usr/bin/env python3
"""Crop actual CLI SVG exports; numbered overlay is evidence, not native artwork."""
from pathlib import Path
import re
import subprocess
from xml.sax.saxutils import escape

H = Path(__file__).resolve().parent


def crop(source, output, box, width, overlay=''):
    text = source.read_text()
    text = re.sub(r'width="[^"]+" height="[^"]+" viewBox="[^"]+"', f'width="{width}px" height="{round(width*box[3]/box[2])}px" viewBox="' + ' '.join(map(str, box)) + '"', text, count=1)
    text = text.replace('</svg>', overlay + '</svg>')
    output.write_text(text)
    subprocess.run(['/opt/homebrew/bin/rsvg-convert', '-o', str(output.with_suffix('.png')), str(output)], check=True)


for name in ['copper', 'paste', 'mask', 'mask_copper', 'fab', 'silk']:
    crop(H/f'board_{name}.svg', H/f'board_{name}_detail.svg', (46.7, 46.7, 6.6, 6.6), 1500)
xy = [(-1.3,-.95),(-1.3,0),(-1.3,.95),(1.3,.95),(1.3,0),(1.3,-.95)]
overlay = '<g fill="#ffffff" stroke="none" font-family="sans-serif" font-size="0.24" text-anchor="middle">'
for i,(x,y) in enumerate(xy, 1):
    overlay += f'<text x="{50+x}" y="{50+y+.08}">{escape(str(i))}</text>'
overlay += '</g>'
crop(H/'board_fab.svg', H/'board_numbered_fab_detail.svg', (46.7,46.7,6.6,6.6), 1500, overlay)
crop(H/'tps2553_check.svg', H/'symbol_detail.svg', (100,54,170,105), 2100)
