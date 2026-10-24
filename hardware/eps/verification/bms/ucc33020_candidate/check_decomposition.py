"""Numerical illustration of proposed comb geometry; no native CAD writes."""
import json, math
from pathlib import Path
from PIL import Image, ImageDraw, ImageChops
HERE=Path(__file__).resolve().parent
S=1000 # 1um raster; arc sampling 0.5 degrees
R=.05
V=[(-2.7,-.475),(-2.1,-.475),(-2.1,1.125),(-2.7,1.125),(-2.7,.825),(-2.4,.825),(-2.4,.475),(-2.7,.475),(-2.7,.175),(-2.4,.175),(-2.4,-.175),(-2.7,-.175)]
def fillet(v):
    out=[]
    for i,b in enumerate(v):
        a=v[i-1];c=v[(i+1)%len(v)]
        u=((b[0]-a[0]),(b[1]-a[1]));l=math.hypot(*u);u=(u[0]/l,u[1]/l)
        w=(c[0]-b[0],c[1]-b[1]);l=math.hypot(*w);w=(w[0]/l,w[1]/l)
        sign=1 if u[0]*w[1]-u[1]*w[0]>0 else -1
        start=(b[0]-R*u[0],b[1]-R*u[1]);center=(start[0]-sign*R*u[1],start[1]+sign*R*u[0])
        theta=math.atan2(start[1]-center[1],start[0]-center[0])
        for j in range(181):
            t=theta+sign*math.pi/2*j/180
            out.append((center[0]+R*math.cos(t),center[1]+R*math.sin(t)))
    return out
def xy(p):return (round((p[0]+2.9)*S),round((p[1]+.7)*S))
def draw(poly,img):ImageDraw.Draw(img).polygon([xy(p) for p in fillet(poly)],fill=255)
def rect(x,y,w,h):return [(x-w/2,y-h/2),(x+w/2,y-h/2),(x+w/2,y+h/2),(x-w/2,y+h/2)]
a=Image.new('L',(1001,2101));draw(V,a)
b=Image.new('L',a.size)
for y in [-.325,.325,.975]:draw(rect(-2.4,y,.6,.3),b)
draw(rect(-2.25,.325,.3,1.6),b)
diff=ImageChops.difference(a,b); count=0;extent=0
for y in range(diff.height):
    row=diff.crop((0,y,diff.width,y+1)).tobytes()
    for x,p in enumerate(row):
        if not p:continue
        count+=1;pt=(x/S-2.9,y/S-.7)
        extent=max(extent,min(max(abs(pt[0]-v[0]),abs(pt[1]-v[1])) for v in V))
assert extent<=.052,extent
# Pixel/arc discretization, not an exact polygon manufacturing proof.
result={'status':'PROPOSAL_NUMERICAL_SCREEN','raster_mm':1/S,'arc_step_deg':.5,'left_comb_difference_mm2':count/S**2,'both_combs_difference_mm2':2*count/S**2,'maximum_difference_extent_from_a_sharp_corner_Linf_mm':extent,'bound_including_raster_error_mm':.052,'note':'Compares fully R0.05-filleted nominal comb against union of four R0.05 rounded rectangles. All differences confined to corner neighborhoods. Not native footprint acceptance.'}
(HERE/'decomposition.json').write_text(json.dumps(result,indent=2)+'\n')
view=Image.merge('RGB',(b,a,Image.new('L',a.size)))
view.crop((150,150,850,1900)).resize((560,1400)).save(HERE/'decomposition.png')
print(json.dumps(result,indent=2))
