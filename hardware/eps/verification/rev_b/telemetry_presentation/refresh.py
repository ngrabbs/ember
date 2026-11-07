"""Export and render saved sources; no native-file writes."""
from pathlib import Path
import json
import subprocess
import math
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
SOURCE = ROOT / 'hardware/eps/rev_b/eps_rev_b.kicad_sch'
logs = []
for args in [
    ['kicad-cli', 'sch', 'export', 'netlist', '--format', 'kicadxml', '-o', str(HERE / 'after.xml'), str(SOURCE)],
    ['kicad-cli', 'sch', 'export', 'svg', '-o', str(HERE / 'svg') + '/', str(SOURCE)],
    ['kicad-cli', 'sch', 'erc', '--format', 'json', '-o', str(HERE / 'erc.json'), str(SOURCE)],
]:
    run = subprocess.run(args, capture_output=True, text=True)
    logs.append({'args': args, 'exit': run.returncode, 'stdout': run.stdout, 'stderr': run.stderr})
    assert run.returncode == 0
(HERE / 'cli_log.json').write_text(json.dumps(logs, indent=2) + '\n')
subprocess.run(['rsvg-convert', '-w', '5100', '-o', str(HERE / 'after.png'),
                str(HERE / 'svg/eps_rev_b-Rail Telemetry.svg')], capture_output=True, check=True)
image = Image.open(HERE / 'after.png')
regions = [('sys_channel', (23, 51, 374, 98)), ('5v_channel', (23, 99, 374, 132)),
           ('3v3_channel', (23, 134, 374, 167)), ('batt_channel', (23, 169, 374, 203)),
           ('supply_detail', (23, 208, 190, 256)), ('footer_detail', (23, 258, 305, 266))]
for name, (x1, y1, x2, y2) in regions:
    image.crop((round(x1 / 431.8 * image.width), round(y1 / 279.4 * image.height),
                round(x2 / 431.8 * image.width), round(y2 / 279.4 * image.height))).save(HERE / (name + '.png'))
print('Fresh full-root exports and six telemetry detail crops completed.')
symbols = json.loads((HERE / 'fields_after.json').read_text())['symbols']
for kind, width, height, columns in [('R', 24, 13, 4), ('C', 20, 14, 3)]:
    selected = [s for s in symbols if s['lib_id'] == 'Device:' + kind]
    cw, ch = round(width / 431.8 * image.width), round(height / 279.4 * image.height)
    montage = Image.new('RGB', (columns * cw, math.ceil(len(selected) / columns) * ch), 'white')
    for index, symbol in enumerate(selected):
        x, y = symbol['x'] - width / 2, symbol['y'] - 5
        box = (round(x / 431.8 * image.width), round(y / 279.4 * image.height),
               round((x + width) / 431.8 * image.width), round((y + height) / 279.4 * image.height))
        montage.paste(image.crop(box).convert('RGB'), (index % columns * cw, index // columns * ch))
    montage.resize((montage.width * 2, montage.height * 2)).save(HERE / (kind + '_field_details.png'))
