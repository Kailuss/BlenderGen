"""Primera cubierta de torreón: terraza modular, parapeto y almenas."""
import math
from .. import meta
import random
import zlib
from ..geometry import primitives,timber
from ..construction_core import roof_support
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


def box(ob):
    'IA: Caja (lo, hi) en mm de las coordenadas reales de la malla, tras derrumbe y recortes.'
    co=primitives.coords(ob)
    return tuple(float(v) for v in co.min(axis=0)),tuple(float(v) for v in co.max(axis=0))


def settle(coll,p,parts,x0,x1,hole):
    'IA: Apoyo real de la terraza (0.32.31): cada viga entrega en piedra superviviente en sus dos cabezas, cada losa asienta en vigas a ambos lados de su centro y cada bloque de parapeto o almena sobre losa o bloque aceptado sin volcar; lo que no apoya cae a escombro (fall) en la proporción de Escombros y el resto se retira. Devuelve recuentos.'
    stones=[];surfaces=[];grounded=[]
    for ob in coll.objects:
        if ob in parts or ob.type!='MESH' or not len(ob.data.vertices):continue
        b=box(ob);surfaces.append(b)
        key=primitives.piece_key(ob)
        # El cimiento no eleva terreno ni escombro: lo que cae encima debe quedarse a su cota.
        grounded.append(bool(ob.get('escombro')) or any(tag in key.lower() for tag in ('tierra','grava','peana')))
        if key.startswith(('Piedra','Pilar')) and not ob.get('escombro') and not ob.get('stair'):stones.append(b)
    boxes={ob:box(ob) for ob in parts}
    beams=[ob for ob in parts if ob.get('roof_timber')]
    def full(ob):
        'IA: Viga de lado a lado (o tramo junto al acceso), frente a brochal.'
        return primitives.piece_key(ob).startswith('Madera · viga terraza')
    kept=set(beams);missing=0
    for _ in range(6):
        changed=False
        for ob in sorted(kept,key=lambda o:o.name):
            lo,hi=boxes[ob]
            if full(ob):
                ends=[]
                for end,side in ((lo[0],-1),(hi[0],1)):
                    if (side<0 and end<=x0+1.5) or (side>0 and end>=x1-1.5):
                        foot=(end,x0+p.thickness,lo[1],hi[1]) if side<0 else (x1-p.thickness,end,lo[1],hi[1])
                        ends.append(roof_support.bearing(foot,lo[2],stones)[0])
                    else:
                        # Cabeza junto al acceso: apoya en el brochal que la recibe.
                        ends.append(any(not full(o) and boxes[o][0][0]-.5<=end+side*2<=boxes[o][1][0]+.5 and boxes[o][0][1]<=lo[1] and hi[1]<=boxes[o][1][1] for o in kept))
                ok=all(ends)
            else:
                # Brochal: necesita una viga entera que lo cruce a cada lado del acceso.
                crossing=[boxes[o] for o in kept if full(o) and boxes[o][0][0]<=lo[0] and hi[0]<=boxes[o][1][0] and lo[1]<=boxes[o][0][1] and boxes[o][1][1]<=hi[1]]
                ok=bool(hole) and any(b[1][1]<=hole[2] for b in crossing) and any(b[0][1]>=hole[3] for b in crossing)
            if not ok:kept.discard(ob);changed=True;missing+=1
        if not changed:break
    seats=[boxes[o] for o in kept];fallen=[o for o in beams if o not in kept]
    slabs=0
    for ob in sorted((o for o in parts if o.get('tower_part')=='deck'),key=lambda o:o.name):
        if roof_support.seated(boxes[ob],seats,roof_support.MIN_SLAB_CONTACT)[0]:continue
        fallen.append(ob);slabs+=1
    accepted=[boxes[o] for o in parts if o.get('tower_part')=='deck' and o not in fallen];blocks=0
    for ob in sorted((o for o in parts if o.get('tower_part') in ('parapet','merlon')),key=lambda o:(boxes[o][0][2],o.name)):
        if roof_support.seated(boxes[ob],accepted,roof_support.MIN_BLOCK_CONTACT)[0]:accepted.append(boxes[ob])
        else:fallen.append(ob);blocks+=1
    standing=[boxes[o] for o in parts if o not in fallen]
    # Escombros: parte proporcional a Escombros; el resto se da por pulverizado o disperso fuera.
    lost=[o for o in fallen if random.Random(p.seed+zlib.crc32(primitives.piece_key(o).encode())).random()>=p.rubble_amount]
    fall([o for o in fallen if o not in lost],boxes,surfaces+standing,grounded+[False]*len(standing),p)
    primitives.remove_objects(lost)
    return {'beams_without_bearing':missing,'slabs_unseated':slabs,'blocks_unseated':blocks,'fallen':len(fallen)-len(lost),'lost':len(lost)}


def fall(pieces,boxes,surfaces,grounded,p):
    'IA: Las piezas sin apoyo caen en vertical, de abajo arriba y con un giro en planta sembrado, hasta la superficie real más alta bajo su huella (se apilan entre sí) y se hunden 0,1 mm para fundirse al exportar. Quedan como escombro de cubierta (roof_debris, tower_fallen); llevan la marca escombro solo si reposan en terreno o escombro, para que el cimiento eleve las que caen sobre suelos y deje en su sitio las que llegan al terreno.'
    landed=[];flags=list(grounded)
    for index,ob in enumerate(sorted(pieces,key=lambda o:(boxes[o][0][2],o.name))):
        rng=random.Random(p.seed+31700+index)
        co=primitives.coords(ob);center=(co.min(axis=0)+co.max(axis=0))/2;angle=rng.uniform(-.5,.5)
        c,s=math.cos(angle),math.sin(angle);x=co[:,0]-center[0];y=co[:,1]-center[1]
        co[:,0]=center[0]+c*x-s*y;co[:,1]=center[1]+s*x+c*y
        lo=co.min(axis=0);hi=co.max(axis=0)
        rest,hit=roof_support.landing((lo[0],hi[0],lo[1],hi[1]),float(boxes[ob][0][2]),surfaces+landed)
        on_ground=hit<0 or flags[hit]
        co[:,2]+=rest-lo[2]-.1
        primitives.set_coords(ob,co)
        landed.append((tuple(co.min(axis=0)),tuple(co.max(axis=0))));flags.append(on_ground)
        part=ob.get('tower_part')
        if part:ob['tower_part_fallen']=part;del ob['tower_part']
        if 'roof_timber' in ob:del ob['roof_timber']
        ob['roof_debris']=True;ob['tower_fallen']=True
        if on_ground:ob['escombro']=True


def build(coll,p,scene,walls):
    'IA: Terraza modular con acceso y parapeto; el derrumbe compartido recorta coronación y retira módulos con pérdida local superior a 6 mm, sin booleanas globales; después settle exige apoyo real sobre la piedra que queda y deja caer lo que no apoya.'
    before=set(coll.objects)
    x0=walls['left']['origin'][0]-p.thickness/2;x1=walls['right']['origin'][0]+p.thickness/2
    y0=-p.thickness/2;y1=walls['back']['origin'][1]+p.thickness/2
    z=p.height;t=min(6,p.thickness);joint=.12
    from . import construction_plan
    # Productor único: la reserva del plan; aquí solo se derivan los ajustes locales.
    settings=stairs.terrace_settings(p);access=construction_plan.stair(scene,'terrace');hole=None
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
    support={'beams_without_bearing':0,'slabs_unseated':0,'blocks_unseated':0,'fallen':0,'lost':0}
    if max(p.collapse,p.roof_damage)>0:
        support=settle(coll,p,set(coll.objects)-before,x0,x1,hole)
    deck=sum(o.get('tower_part')=='deck' for o in coll.objects)
    count=sum(o.get('tower_part') in ('merlon','parapet') for o in coll.objects)
    meta.put(scene,'cubierta_generada',[{'index':0,'type':'TOWER','z':z+7,'ridge':base+16}])
    stairs.build_terrace(coll,p,scene,settings,access)
    meta.put(scene,'cubierta_detalles',{'profile':'tower','deck_slabs':deck,'parapet_blocks':count,'tiles':0,'access_opening':hole,'access_error':access.get('error') if access else None,'bounds':{'walls':[x0,x1,y0,y1],'cover':[x0,x1,y0,y1]},'eave_height':z+7,'support':support})
