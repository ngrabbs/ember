"""Read-only courtyard rectangle budgeting; no placement or routing claim."""
import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
data = json.loads((HERE / 'footprint_readback.json').read_text())
rows = []
for item in data['readbacks']:
    points = []
    for graphic in item['info']['graphics']:
        if graphic['layer'] != 'F.CrtYd':
            continue
        assert graphic['type'] in ('rect', 'line'), graphic
        points.extend((graphic['start'], graphic['end']))
    assert points, item['id']
    width = max(p['x'] for p in points) - min(p['x'] for p in points)
    height = max(p['y'] for p in points) - min(p['y'] for p in points)
    rows.append(dict(footprint=item['id'], count=item['count'], width_mm=width,
                     height_mm=height, rectangle_mm2=width*height,
                     extended_mm2=width*height*item['count']))
rows.sort(key=lambda r: -r['extended_mm2'])
assigned = sum(r['count'] for r in rows)
assert assigned == 155
result = dict(physical_parts=160, assigned_footprints=assigned, missing_footprints=5,
              summed_courtyard_bounding_rectangles_mm2=sum(r['extended_mm2'] for r in rows),
              illustrative_board_rectangle_mm2=96*90, rows=rows)
(HERE / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
with (HERE / 'courtyards.csv').open('w', newline='') as out:
    writer = csv.DictWriter(out, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
print(json.dumps({k:v for k,v in result.items() if k != 'rows'}, indent=2))
print(json.dumps(rows[:6], indent=2))
