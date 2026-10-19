"""Primera cubierta de torreón: terraza modular, parapeto y almenas."""
import math
from .. import meta
from ..geometry import primitives,timber
from . import stairs,spatial


def outside_opening(rect,hole):
    'IA: Divide una losa rectangular en hasta cuatro rectángulos disjuntos fuera del acceso, sin booleanas ni tiras menores de 0,1 mm.'
    a,b,c,d=rect
    if not hole or b<=hole[0] or a>=hole[1] or d<=hole[2] or c>=hole[3]:return [rect]
    x0=max(a,hole[0]);x1=min(b,hole[1]);y0=max(c,hole[2]);y1=min(d,hole[3])
    return [r for r in ((a,x0,c,d),(x1,b,c,d),(x0,x1,c,y0),(x0,x1,y1,d)) if r[1]-r[0]>.1 and r[3]-r[2]>.1]


def loss_at(p,x,y):
    'IA: Combina pérdida de muro y daño propio de cubierta en el mismo campo localizado, en milímetros.'
    strength=max(max(0,1-((x-cx)/rx)**2-((y-cy)/ry)**2)**.65 for cx,cy,rx,ry in spatial.impacts(p))
    return max(p.height-spatial.collapse_height(p,x,y),30*p.roof_damage**1.6*strength)


def build(coll,p,scene,walls):
    'IA: Terraza modular con acceso y parapeto; el derrumbe compartido recorta coronación y retira módulos con pérdida local superior a 6 mm, sin booleanas globales.'
    before=set(coll.objects)
    x0=walls['left']['origin'][0]-p.thickness/2;x1=walls['right']['origin'][0]+p.thickness/2
    y0=-p.thickness/2;y1=walls['back']['origin'][1]+p.thickness/2
    z=p.height;t=min(6,p.thickness);joint=.12
    bounds=(x0+p.thickness-.6,x1-p.thickness+.6,y0+p.thickness-.6,y1-p.thickness+.6)
    settings,access=stairs.terrace_plan(p,bounds);hole=None
    if access and 'error' not in access:
        opening=access['opening'];landing=access['landing']
        hole=[min(opening[0],landing[0]),max(opening[1],landing[1]),opening[2],opening[3]]
    stone=primitives.material('Piedra · torreón',(.52,.50,.46));wood=primitives.material('Madera · cubierta',(.31,.22,.13))
    bays=max(2,math.ceil((y1-y0)/16));step=(y1-y0)/bays
    for i in range(bays+1):
        y=y0+(y1-y0)*i/bays
        y=max(y0+2,min(y1-2,y))
        spans=[(x0+1,x1-1)]
        if hole and hole[2]-2<y<hole[3]+2:spans=[(x0+1,hole[0]-2),(hole[1]+2,x1-1)]
        for a,b in spans:
            if b-a<1:continue
            beam=timber.timber_beam(coll,wood,'Madera · viga terraza',(a,y,z+2),(b,y,z+2),4,4,p.seed+31000+i,coarse=True)
            beam['roof_timber']=True
    if hole:
        for x in (hole[0]-2,hole[1]+2):
            beam=timber.timber_beam(coll,wood,'Madera · brochal terraza',(x,hole[2]-step,z+2),(x,min(y1-2,hole[3]+step),z+2),4,4,p.seed+31900,coarse=True);beam['roof_timber']=True
    nx=max(2,math.ceil((x1-x0)/18));dx=(x1-x0)/nx;deck=0
    for j in range(bays):
        for i in range(nx):
            rect=(x0+i*dx+joint/2,x0+(i+1)*dx-joint/2,y0+j*step+joint/2,y0+(j+1)*step-joint/2)
            for part in outside_opening(rect,hole):
                ob=primitives.block('Piedra · losa terraza',*part,z+4,z+7,coll,stone)
                ob['tower_part']='deck';deck+=1
    base=z+7;course=4;count=0
    # Las caras frontal y trasera poseen las esquinas; los laterales terminan en ellas.
    spans=[('front',x0,x1,y0,y0+t,False),('back',x0,x1,y1-t,y1,False),('left',y0+t,y1-t,x0,x0+t,True),('right',y0+t,y1-t,x1-t,x1,True)]
    for side,a,b,c,d,swap in spans:
        n=max(2,math.ceil((b-a)/10));pitch=(b-a)/n
        for row in range(4):
            cuts=sorted({a,b,*[a+(i+(.5 if row%2 else 0))*pitch for i in range(n+1) if a<a+(i+(.5 if row%2 else 0))*pitch<b]})
            for i,(lo,hi) in enumerate(zip(cuts,cuts[1:])):
                if row>=2 and i%2:continue
                # Las almenas mantienen la misma huella en sus dos hiladas.
                if row==3:continue
                za=base+row*course;zb=za+(2*course if row==2 else course)-joint/2
                args=(c+joint/2,d-joint/2,lo+joint/2,hi-joint/2) if swap else (lo+joint/2,hi-joint/2,c+joint/2,d-joint/2)
                ob=primitives.block('Piedra · '+('almena' if row==2 else 'parapeto')+' '+side,*args,za,zb,coll,stone)
                ob['tower_part']='merlon' if row==2 else 'parapet';count+=1
    removed=[]
    for ob in set(coll.objects)-before:
        if max(p.collapse,p.roof_damage)<=0:continue
        co=primitives.coords(ob);center=(co.min(axis=0)+co.max(axis=0))/2
        loss=loss_at(p,float(center[0]),float(center[1]))
        if ob.name.startswith('Madera · viga terraza'):
            loss=max(loss,loss_at(p,x0+1,float(center[1])),loss_at(p,x1-1,float(center[1])))
        if loss>6:removed.append(ob)
        elif loss>.05 and ob.get('tower_part') in ('merlon','parapet'):
            limit=base+16-loss*3
            if co[:,2].min()>=limit:removed.append(ob)
            elif co[:,2].max()>limit:primitives.clip_closed(ob,(0,0,limit),(0,0,1))
    primitives.remove_objects(removed)
    if max(p.collapse,p.roof_damage)>0:
        supports=[(primitives.coords(o).min(axis=0),primitives.coords(o).max(axis=0)) for o in set(coll.objects)-before if o.get('roof_timber')]
        unsupported=[]
        for ob in set(coll.objects)-before:
            if ob.get('tower_part')!='deck':continue
            co=primitives.coords(ob);lo=co.min(axis=0);hi=co.max(axis=0)
            if not any(all(min(hi[k],b[k])>=max(lo[k],a[k]) for k in (0,1)) for a,b in supports):unsupported.append(ob)
        primitives.remove_objects(unsupported)
        seats=[(primitives.coords(o).min(axis=0),primitives.coords(o).max(axis=0)) for o in set(coll.objects)-before if o.get('tower_part')=='deck']
        parapets=sorted((o for o in set(coll.objects)-before if o.get('tower_part') in ('parapet','merlon')),key=lambda o:float(primitives.coords(o)[:,2].min()))
        unsupported=[]
        for ob in parapets:
            co=primitives.coords(ob);lo=co.min(axis=0);hi=co.max(axis=0)
            if any(abs(lo[2]-b[2])<.3 and all(min(hi[k],b[k])-max(lo[k],a[k])>.01 for k in (0,1)) for a,b in seats):seats.append((lo,hi))
            else:unsupported.append(ob)
        primitives.remove_objects(unsupported)
    deck=sum(o.get('tower_part')=='deck' for o in coll.objects)
    count=sum(o.get('tower_part') in ('merlon','parapet') for o in coll.objects)
    meta.put(scene,'cubierta_generada',[{'index':0,'type':'TOWER','z':z+7,'ridge':base+16}])
    stairs.build_terrace(coll,p,scene,settings,access)
    meta.put(scene,'cubierta_detalles',{'profile':'tower','deck_slabs':deck,'parapet_blocks':count,'tiles':0,'access_opening':hole,'access_error':access.get('error') if access else None,'bounds':{'walls':[x0,x1,y0,y1],'cover':[x0,x1,y0,y1]},'eave_height':z+7})
