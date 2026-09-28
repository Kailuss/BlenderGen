"""Daño localizado de cubierta y restos asentados, sin simulación ni booleanos masivos."""
import math,random
from .. import meta
from ..geometry import primitives,timber,terrain


def plan(p,bounds):
    'IA: Dos elipses reproducibles en faldones opuestos; tamaño continuo según daño, fuera de la cumbrera.'
    xa,xb,ya,yb=bounds['cover'];span=xb-xa;depth=yb-ya;rng=random.Random(p.seed+46301)
    amount=p.roof_damage
    if amount<=0:return []
    return [{'x':xa+span*f,'y':ya+depth*(.28+.42*rng.random()),'rx':span*(.045+.13*amount),'ry':depth*(.045+.17*amount)} for f in (.23,.76)]


def distance(x,y,patches):
    'IA: Distancia elíptica mínima; infinito sin daño para conservar cubierta íntegra.'
    return min((((x-h['x'])/h['rx'])**2+((y-h['y'])/h['ry'])**2 for h in patches),default=1000)


def segments(a,b,fixed,patches,axis):
    'IA: Resta intervalos elípticos de un rastrel/par; devuelve tramos anclados al extremo original, con longitud mínima.'
    ranges=[(min(a,b),max(a,b))]
    for h in patches:
        pos=h['x'] if axis=='y' else h['y'];rad=h['rx'] if axis=='y' else h['ry']
        d=(fixed-pos)/rad
        if abs(d)>=1:continue
        center=h[axis];radius=h['ry'] if axis=='y' else h['rx'];half=radius*math.sqrt(1-d*d)*.76
        lo,hi=center-half,center+half;next_ranges=[]
        for x,y in ranges:
            if hi<=x or lo>=y:next_ranges.append((x,y));continue
            if lo-x>2:next_ranges.append((x,lo))
            if y-hi>2:next_ranges.append((hi,y))
        ranges=next_ranges
    return [(x,y) for x,y in ranges if abs(x-min(a,b))<.001 or abs(y-max(a,b))<.001]


def debris(coll,p,scene,bounds,missing):
    'IA: Deposita fragmentos de teja y palos junto al faldón perdido sobre tierra real; coste máximo de 64 tejas y 12 palos.'
    meta.put(scene,'escombros_cubierta',{})
    if not missing or p.rubble_amount<=0:return
    xa,xb,ya,yb=bounds['cover'];rng=random.Random(p.seed+48200)
    clay=primitives.material('Tejas · arcilla',(.40,.20,.115));wood=primitives.material('Madera · cubierta',(.31,.22,.13));soil=primitives.material('Tierra · arena',(.36,.31,.24))
    total=0;sticks=0
    for side in (0,1):
        points=[q for q in missing if (q[0]<(xa+xb)/2)==(side==0)]
        if not points:continue
        cx=(bounds['walls'][0]-2 if side==0 else bounds['walls'][1]+2);cy=sum(q[1] for q in points)/len(points)
        _,surface=terrain.earth_patch(coll,soil,'Tierra · caída de cubierta',cx,cy,10,13,1.3+p.rubble_amount*1.2,p.seed+side+48210,p.ground_roughness)
        count=min(32,max(2,round(len(points)*.3*p.rubble_amount)))
        for j in range(count):
            x=cx+rng.uniform(-5,5);y=cy+rng.uniform(-9,9);angle=rng.uniform(0,math.tau)
            w=rng.uniform(1.8,4.3);d=rng.uniform(2,5.5)
            ob=primitives.block('Teja caída · fragmento',-w/2,w/2,-d/2,d/2,0,.7,coll,clay)
            primitives.clip_closed(ob,(w*.25,d*.25,.4),(1,1,.15))
            from mathutils import Euler
            import numpy as np
            co=primitives.coords(ob)@np.array(Euler((rng.uniform(-.4,.4),rng.uniform(-.4,.4),angle)).to_matrix()).T
            co[:,0]+=x;co[:,1]+=y;primitives.set_coords(ob,co);terrain.settle_rubble(ob,surface)
            ob['escombro']=True;ob['roof_debris']=True;total+=1
        for j in range(min(6,1+count//5)):
            x=cx+rng.uniform(-4,4);y=cy+rng.uniform(-8,8);ang=rng.random()*math.tau;length=rng.uniform(5,13)
            ob=timber.timber_beam(coll,wood,'Madera · palo caído',(x,y,1),(x+math.cos(ang)*length,y+math.sin(ang)*length,1.5),1.4,1.3,p.seed+48400+side*100+j,coarse=True)
            terrain.settle_rubble(ob,surface);ob['escombro']=True;ob['roof_debris']=True;sticks+=1
        terrain.gravel_batch(coll,soil,'Arena · cubierta caída',cx,cy,10,13,surface,round(18+25*p.rubble_amount),p.seed+48600+side,radius_scale=.45)
    meta.put(scene,'escombros_cubierta',{'tiles':total,'sticks':sticks,'source_missing':len(missing)})
