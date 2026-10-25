"""Read-only STEP solid inventory; requires cadquery-ocp 8.0.1.1.0.

Run from any directory. The source STEP is never written. Solid indices are
explorer traversal indices for this exact source hash, not component identities.
"""
import hashlib
import json
from pathlib import Path

from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.IFSelect import IFSelect_RetDone
from OCP.STEPControl import STEPControl_Reader
from OCP.TopAbs import TopAbs_SOLID
from OCP.TopExp import TopExp_Explorer
from OCP.BRep import BRep_Tool
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.TopAbs import TopAbs_FACE
from OCP.TopLoc import TopLoc_Location
from OCP.TopoDS import TopoDS

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parents[2] / 'design/cubesat_eps_rev_b_v0.4.step'
EXPECTED = '8a2c58b82846ccdaa0d035bd6143571d50c54ee90a3e1322008fbfcc44b8554a'
digest = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
assert digest == EXPECTED, 'STEP changed: re-establish geometry identity'
reader = STEPControl_Reader()
assert reader.ReadFile(str(SOURCE)) == IFSelect_RetDone
assert reader.TransferRoots() > 0
explorer = TopExp_Explorer(reader.OneShape(), TopAbs_SOLID)
rows = []
shapes = []
while explorer.More():
    shape = explorer.Current()
    shapes.append(shape)
    box = Bnd_Box()
    BRepBndLib.AddOptimal_s(shape, box)
    lo, hi = box.CornerMin(), box.CornerMax()
    bounds = [lo.X(), lo.Y(), lo.Z(), hi.X(), hi.Y(), hi.Z()]
    props = GProp_GProps()
    BRepGProp.VolumeProperties_s(shape, props)
    rows.append({'solid_index': len(rows) + 1,
                 'bounds_mm': bounds,
                 'size_mm': [bounds[i + 3] - bounds[i] for i in range(3)],
                 'volume_mm3': props.Mass()})
    explorer.Next()
result = {'source': str(SOURCE.relative_to(HERE.parents[4])),
          'sha256': digest, 'user_confirmed_export_selection': True,
          'holder_clearance_verified': False,
          'confirmation_date': '2026-10-24',
          'kernel': 'cadquery-ocp 8.0.1.1.0',
          'coordinate_unit': 'mm (STEP transfer output)',
          'solid_count': len(rows), 'solids': rows}
(HERE / 'solids.json').write_text(json.dumps(result, indent=2) + '\n')
print('solids:', len(rows))
for row in rows:
    if row['volume_mm3'] > 500 or max(row['size_mm']) > 65:
        print(row['solid_index'], [round(v, 4) for v in row['bounds_mm']],
              'volume', round(row['volume_mm3'], 3))

# Tessellate only for a human geometry review. These triangles do not establish
# clearance, manufacturing dimensions or a validated assembly registration.
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

meshes = []
for index, shape in enumerate(shapes, 1):
    BRepMesh_IncrementalMesh(shape, 0.15, False, 0.3, True)
    faces = TopExp_Explorer(shape, TopAbs_FACE)
    triangles = []
    while faces.More():
        face = TopoDS.Face(faces.Current())
        loc = TopLoc_Location()
        tri = BRep_Tool.Triangulation_s(face, loc)
        if tri is not None:
            transform = loc.Transformation()
            nodes = {i: tri.Node(i).Transformed(transform)
                     for i in range(1, tri.NbNodes() + 1)}
            for i in range(1, tri.NbTriangles() + 1):
                pts = [nodes[j] for j in tri.Triangle(i).Get()]
                triangles.append([(p.X(), p.Y(), p.Z()) for p in pts])
        faces.Next()
    meshes.append((index, triangles))
fig = plt.figure(figsize=(14, 9), layout='constrained')
all_triangles, all_colors = [], []
for index, triangles in meshes:
    color = '#438f6c' if index == 1 else '#c58a40' if index in (102, 276) else '#788895'
    all_triangles.extend(triangles)
    all_colors.extend([color] * len(triangles))
for panel, (title, elev, azim) in enumerate([
        ('Top / connectors', 55, -65), ('Underside', -55, -65),
        ('Side: STEP X-Z', 0, -90), ('Side: STEP Y-Z', 0, 0)], 1):
    ax = fig.add_subplot(2, 2, panel, projection='3d')
    ax.add_collection3d(Poly3DCollection(all_triangles, facecolors=all_colors,
                       edgecolor='none', linewidth=0))
    ax.set(xlim=(-2, 98), ylim=(-2, 92), zlim=(-14, 13),
           xlabel='STEP X / mm', ylabel='STEP Y / mm', zlabel='STEP Z / mm',
           title=title)
    ax.set_box_aspect((100, 94, 27))
    ax.view_init(elev=elev, azim=azim)
fig.suptitle('User-confirmed May STEP export: geometry inspection only\n'
             'cubesat_eps_rev_b_v0.4.step; no holder clearance inferred')
fig.savefig(HERE / 'assembly_views.png', dpi=150)
plt.close(fig)
