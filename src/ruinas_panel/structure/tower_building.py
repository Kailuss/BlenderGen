"""Torreón, paso 2: mallas cerradas desde el aparejo puro de tower_plan (circular y cuadrado).

Cada piedra es una pieza cerrada; un núcleo de mortero por hilada, embebido como en los muros, rellena las
juntas por dentro para que la pieza impresa quede unida. Medidas en mm y marcas de aparejo (C5-5) desde el inicio.
"""
import math
import bpy
from .. import config_masonry as masonry
from ..construction_core import identifiers
from ..geometry import primitives
from . import tower_plan,tower_floors

SEGMENT_MM=1.6      # cuerda máxima de las caras curvas
BEAM_SECTION=(tower_floors.BEAM_W,tower_floors.BEAM_H)
CORE_INSET=.18      # fracción del grosor que el núcleo queda dentro de cada paramento


def arc_steps(radius,a0,a1):
    'IA: Número de tramos para que la cuerda de un arco no supere SEGMENT_MM.'
    return max(2,math.ceil(radius*(a1-a0)/SEGMENT_MM))


def sector_mesh(r_in,r_out,a0,a1,z0,z1):
    'IA: Sector anular cerrado (vértices y caras con normales hacia fuera); a1>a0 en radianes.'
    n=arc_steps(r_out,a0,a1);verts=[]
    for i in range(n+1):
        a=a0+(a1-a0)*i/n;c,s=math.cos(a),math.sin(a)
        verts+=[(r_in*c,r_in*s,z0),(r_out*c,r_out*s,z0),(r_out*c,r_out*s,z1),(r_in*c,r_in*s,z1)]
    faces=[]
    for i in range(n):
        q=4*i;r=q+4
        faces+=[(q,r,r+1,q+1),(q+1,r+1,r+2,q+2),(q+2,r+2,r+3,q+3),(q+3,r+3,r,q)]
    last=4*n
    faces+=[(0,1,2,3),(last+3,last+2,last+1,last)]
    return verts,faces


def ring_mesh(r_in,r_out,z0,z1):
    'IA: Anillo completo cerrado (toro rectangular) para el núcleo de mortero de una hilada.'
    n=max(12,math.ceil(2*math.pi*r_out/SEGMENT_MM));verts=[]
    for i in range(n):
        a=2*math.pi*i/n;c,s=math.cos(a),math.sin(a)
        verts+=[(r_in*c,r_in*s,z0),(r_out*c,r_out*s,z0),(r_out*c,r_out*s,z1),(r_in*c,r_in*s,z1)]
    faces=[]
    for i in range(n):
        q=4*i;r=4*((i+1)%n)
        faces+=[(q,r,r+1,q+1),(q+1,r+1,r+2,q+2),(q+2,r+2,r+3,q+3),(q+3,r+3,r,q)]
    return verts,faces


def radial_prism(geo,depth,a0,a1,z0,z1,embed=0.):
    'IA: Prisma cerrado entre el paramento interior (más embed) y depth hacia dentro en el arco [a0,a1]; sigue el círculo o el cuadrado y quiebra en las esquinas.'
    reach=geo['inner'];n=arc_steps(reach,a0,a1);angles={a0+(a1-a0)*i/n for i in range(n+1)}
    if geo['shape']=='SQUARE':
        k=math.ceil((a0-math.pi/4)/(math.pi/2))
        while math.pi/4+k*math.pi/2<a1:angles.add(math.pi/4+k*math.pi/2);k+=1
    verts=[]
    for a in sorted(angles):
        c,s=math.cos(a),math.sin(a);r_in=tower_floors.boundary(geo,a,depth);r_out=tower_floors.boundary(geo,a)+embed
        verts+=[(r_in*c,r_in*s,z0),(r_out*c,r_out*s,z0),(r_out*c,r_out*s,z1),(r_in*c,r_in*s,z1)]
    m=len(verts)//4-1;faces=[]
    for i in range(m):
        q=4*i;r=q+4
        faces+=[(q,r,r+1,q+1),(q+1,r+1,r+2,q+2),(q+2,r+2,r+3,q+3),(q+3,r+3,r,q)]
    faces+=[(0,1,2,3),(4*m+3,4*m+2,4*m+1,4*m)]
    return verts,faces


def build_interior(coll,geo,frames,steps,stone,wood,origin=(0.,0.,0.)):
    'IA: Forjados (vigas sobre ménsulas, tablas y losas de terraza) y peldaños de la hélice ya asentados; devuelve las piezas creadas.'
    ox,oy,oz=origin;made=[]
    for lv,beams,boards,tiles in frames:
        f=lv['floor']
        for b in beams:
            ob=primitives.block('Madera · viga torreón %s.%s'%(f,b['id']),ox+b['x'][0],ox+b['x'][1],oy+b['y'][0],oy+b['y'][1],oz+lv['beam_z0'],oz+lv['beam_z1'],coll,wood)
            identifiers.tag(ob,'beam',f,b['id']);ob['wall_id']='torreon';made.append(ob)
        for t in boards:
            ob=primitives.block('Madera · tabla torreón %s.%s'%(f,t['id']),ox+t['x'][0],ox+t['x'][1],oy+t['y'][0],oy+t['y'][1],oz+lv['beam_z1'],oz+lv['board_top'],coll,wood)
            identifiers.tag(ob,'board',f,t['id']);ob['wall_id']='torreon';made.append(ob)
        for t in tiles:
            ob=primitives.block('Piedra · losa terraza torreón %s'%t['id'],ox+t['x'][0],ox+t['x'][1],oy+t['y'][0],oy+t['y'][1],oz+lv['board_top'],oz+lv['top'],coll,stone)
            identifiers.tag(ob,'slab',f,t['id']);ob['wall_id']='torreon';made.append(ob)
    for k,st in enumerate(steps):
        verts,faces=radial_prism(geo,st['depth'],st['a0'],st['a1'],oz+st['z0'],oz+st['z1'],tower_floors.STEP_EMBED)
        verts=[(x+ox,y+oy,z) for x,y,z in verts]
        ob=primitives.mesh_obj('Piedra · peldaño torreón %s'%k,verts,faces,coll,stone)
        identifiers.tag(ob,'stair',st['flight'],st['index']);ob['wall_id']='torreon';made.append(ob)
        primitives.bevel(ob,min(.3,(st['z1']-st['z0'])*.1))
    return made


def build_fallen(coll,pieces,stone,wood,origin=(0.,0.,0.)):
    'IA: Escombro interior caído desde tower_floors.fallen: cajas cerradas giradas en planta, marcadas escombro y tower_fallen.'
    ox,oy,oz=origin;made=[];names={'beam':'Madera · viga caída torreón','board':'Madera · tabla caída torreón','slab':'Piedra · losa caída torreón','step':'Piedra · peldaño caído torreón'}
    for k,piece in enumerate(pieces):
        length,width,height=piece['size'];corners=tower_floors.footprint(None,piece['x'],piece['y'],piece['yaw'],length,width)
        z0=oz+piece['z0'];z1=z0+height
        verts=[(x+ox,y+oy,z0) for x,y in corners]+[(x+ox,y+oy,z1) for x,y in corners]
        faces=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
        ob=primitives.mesh_obj('%s %s'%(names[piece['kind']],k),verts,faces,coll,wood if piece['wood'] else stone)
        identifiers.tag(ob,'fallen',0,k);ob['wall_id']='torreon';ob['escombro']=True;ob['tower_fallen']=True;made.append(ob)
        if not piece['wood']:primitives.bevel(ob,min(.25,height*.15))
    return made


def stone_runs(stones,tolerance=1e-6):
    'IA: Tramos angulares contiguos de piedras vivas; None representa la vuelta completa.'
    if not stones:return []
    spans=sorted(stones);runs=[list(spans[0])]
    for a,b in spans[1:]:
        if a<=runs[-1][1]+tolerance:runs[-1][1]=max(runs[-1][1],b)
        else:runs.append([a,b])
    total=sum(b-a for a,b in runs)
    if len(runs)==1 and total>=2*math.pi-1e-6:return [None]
    # Une el último tramo con el primero si cierran la vuelta por 2π.
    if len(runs)>1 and abs(runs[-1][1]-2*math.pi-runs[0][0])<tolerance*10:
        runs[0]=[runs[-1][0],runs[0][1]+2*math.pi];runs.pop()
        if runs[0][1]-runs[0][0]>=2*math.pi-1e-6:return [None]
    return [tuple(r) for r in runs]


def build_round(coll,plan,stone,core,origin=(0.,0.,0.)):
    'IA: Construye la torre circular del plan; devuelve piedras y núcleos. Juntas de JOINT_MM entre piedras y hiladas.'
    ox,oy,oz=origin;made=[]
    for course in plan:
        z0=oz+course['z0']+masonry.COURSE_BOTTOM_INSET;z1=oz+course['z1']-masonry.COURSE_TOP_INSET
        r_in,r_out=course['r_in'],course['r_out'];t=r_out-r_in;corbels=course.get('corbels',{})
        for index,(a0,a1) in enumerate(course['stones']):
            gap=tower_plan.JOINT_MM/2/r_out
            # Las ménsulas son perpiaños: la misma piedra atraviesa el muro y vuela hacia dentro.
            inner=r_in-course.get('corbel_reach',0.) if (a0,a1) in corbels else r_in
            verts,faces=sector_mesh(inner,r_out,a0+gap,a1-gap,z0,z1)
            verts=[(x+ox,y+oy,z) for x,y,z in verts]
            ob=primitives.mesh_obj('Piedra · torreón %s.%s'%(course['row'],index),verts,faces,coll,stone)
            identifiers.tag(ob,'stone',course['row'],index);ob['wall_id']='torreon';made.append(ob)
            if inner<r_in:ob['corbel']=True
            primitives.bevel(ob,min(.65,(z1-z0)*.12,r_out*(a1-a0)*.1,t*.1))
        # El núcleo solo existe bajo piedras vivas: un anillo si la hilada está completa, sectores si está en ruina.
        zc0=oz+course['z0']-.85 if course['row'] else oz+course['z0'];zc1=oz+course['z1']-.7
        for k,run in enumerate(stone_runs(course['stones'])):
            verts,faces=ring_mesh(r_in+CORE_INSET*t,r_out-CORE_INSET*t,zc0,zc1) if run is None else sector_mesh(r_in+CORE_INSET*t,r_out-CORE_INSET*t,run[0],run[1],zc0,zc1)
            verts=[(x+ox,y+oy,z) for x,y,z in verts]
            ob=primitives.mesh_obj('Mortero · torreón %s'%course['row'],verts,faces,coll,core)
            identifiers.tag(ob,'mortar',course['row'],k);ob['wall_id']='torreon';made.append(ob)
    return made


def build_square(coll,plan,stone,core,origin=(0.,0.,0.)):
    'IA: Construye la torre cuadrada del plan con primitives.block; núcleo por muro y hilada dentro del grosor.'
    ox,oy,oz=origin;made=[];j=tower_plan.JOINT_MM/2
    for course in plan:
        z0=oz+course['z0']+masonry.COURSE_BOTTOM_INSET;z1=oz+course['z1']-masonry.COURSE_TOP_INSET
        for index,s in enumerate(course['stones']):
            (x0,x1),(y0,y1)=s['x'],s['y']
            ob=primitives.block('Piedra · torreón %s.%s'%(course['row'],index),ox+x0+j,ox+x1-j,oy+y0+j,oy+y1-j,z0,z1,coll,stone)
            identifiers.tag(ob,'stone',course['row'],index);ob['wall_id']='torreon_'+s['wall'];made.append(ob)
            if s.get('corbels'):ob['corbel']=True
        # Núcleo por muro y por tramo continuo de piedras vivas, dentro del grosor común: no tapa saeteras ni huecos.
        zc0=oz+course['z0']-.85 if course['row'] else oz+course['z0'];zc1=oz+course['z1']-.7;k=0
        for wall in ('front','back','left','right'):
            along='x' if wall in ('front','back') else 'y';across='y' if along=='x' else 'x'
            own=sorted([s for s in course['stones'] if s['wall']==wall],key=lambda s:s[along][0])
            if not own:continue
            c0=max(s[across][0] for s in own);c1=min(s[across][1] for s in own);t=c1-c0
            runs=[[own[0][along][0],own[0][along][1]]]
            for s in own[1:]:
                if s[along][0]<=runs[-1][1]+1e-6:runs[-1][1]=max(runs[-1][1],s[along][1])
                else:runs.append([s[along][0],s[along][1]])
            for lo,hi in runs:
                lo,hi=lo+CORE_INSET*t,hi-CORE_INSET*t
                if hi-lo<tower_plan.MIN_STONE_MM:continue
                x0,x1,y0,y1=(lo,hi,c0+CORE_INSET*t,c1-CORE_INSET*t) if along=='x' else (c0+CORE_INSET*t,c1-CORE_INSET*t,lo,hi)
                ob=primitives.block('Mortero · torreón %s'%course['row'],ox+x0,ox+x1,oy+y0,oy+y1,zc0,zc1,coll,core)
                identifiers.tag(ob,'mortar',course['row'],k);ob['wall_id']='torreon';made.append(ob);k+=1
    return made


COLLECTION='Ruinas · Torreón'


def generate(scene,p):
    'IA: Torreón suelto desde los ajustes: grosor y hilada del tipo de construcción, semilla de la casa; sustituye el torreón anterior sin tocar la casa.'
    from .. import runtime
    old=bpy.data.collections.get(COLLECTION)
    if old:
        primitives.remove_objects(list(old.objects));bpy.data.collections.remove(old)
    coll=bpy.data.collections.new(COLLECTION);scene.collection.children.link(coll)
    runtime.quality=p.preview_quality
    stone=primitives.material('Piedra · neutro',(.52,.52,.52));core=primitives.material('Núcleo · neutro',(.44,.44,.44))
    thickness=min(p.thickness,p.tower_size*.3);geo=tower_floors.geometry(p.tower_shape,p.tower_size,thickness)
    wood=primitives.material('Madera · neutro',(.42,.32,.22));parapet=tower_floors.PARAPET_COURSES if p.tower_terrace else 0
    if p.tower_shape=='ROUND':
        intact=tower_plan.round_plan(p.tower_size/2,thickness,p.tower_height,p.stone_size,seed=p.seed,variation=p.stone_variation,slits=p.tower_slits,floors=p.tower_floors,parapet=parapet)
        if parapet:tower_plan.crenellate(intact)
        frames,steps=tower_floors.interior(geo,intact,p.tower_floors,p.tower_terrace)
        plan,removed=tower_plan.ruin_round(intact,p.tower_height,seed=p.seed,amount=p.tower_ruin)
        made=build_round(coll,plan,stone,core)
    else:
        intact=tower_plan.square_plan(p.tower_size,thickness,p.tower_height,p.stone_size,seed=p.seed,variation=p.stone_variation,slits=min(1,p.tower_slits),floors=p.tower_floors,parapet=parapet)
        if parapet:tower_plan.crenellate(intact,square=True)
        frames,steps=tower_floors.interior(geo,intact,p.tower_floors,p.tower_terrace)
        plan,removed=tower_plan.ruin_square(intact,p.tower_height,seed=p.seed,amount=p.tower_ruin)
        made=build_square(coll,plan,stone,core)
    kept,alive,lost=tower_floors.settle(geo,plan,frames,steps)
    inside=build_interior(coll,geo,kept,alive,stone,wood)
    # Lo que pierde apoyo no desaparece: cae sobre el piso vivo de abajo o el suelo («dejar a la naturaleza hacer»).
    debris,cleared=tower_floors.fallen(geo,frames,kept,steps,alive,p.seed)
    inside+=build_fallen(coll,debris,stone,wood)
    if getattr(p,'wear',0)>0:
        from ..geometry import weather
        for i,ob in enumerate(o for o in made if o.name.startswith('Piedra')):weather.weather_stone(ob,p.wear,p.seed*977+i)
    # Lo que no cabe dentro sale por las brechas al montón del pie: no se pierde material, se recoloca.
    heaps=tower_rubble(coll,p,stone,tower_plan.lost_angles(intact,plan,square=p.tower_shape!='ROUND'),removed,cleared,wood)
    interior={'beams':sum(len(f[1]) for f in kept),'boards':sum(len(f[2]) for f in kept),'slabs':sum(len(f[3]) for f in kept),
              'terrace':any(f[0]['terrace'] and f[3] for f in kept),'steps':len(alive),'lost':lost,'fallen':len(debris),'outside':cleared}
    return {'stones':sum(o.name.startswith('Piedra') for o in made),'removed':removed,'pieces':len(made)+len(inside),'heaps':heaps,'interior':interior}


def tower_rubble(coll,p,stone,angles,removed,interior=None,wood=None):
    'IA: Escombro al pie del torreón donde más coronación se perdió: montículo de tierra, piedras partidas asentadas y grava; una pieza por cada ~4 retiradas (máx. 14 por montón, 20 con el interior que no cupo dentro) y maderos asentados por cada ~3 piezas de madera interior (máx. 6 por montón) sin tocar piedras ni otros maderos en planta.'
    import random
    from ..geometry import terrain,fracture
    if not removed or not angles:return []
    soil=primitives.material('Tierra · arena',(.36,.31,.24));r=p.tower_size/2;h=p.stone_size;audit=[]
    directions=tower_plan.heap_directions(angles);interior=interior or {'wood':0,'stone':0}
    extra_stone=interior['stone']//(3*len(directions));timber=min(6,interior['wood']//(3*len(directions))) if wood else 0
    for k,(theta,count) in enumerate(directions):
        rr=random.Random(p.seed*7349+k);rx=h*(1.6+.08*min(count,30));ry=rx*.7
        d=r+rx*.55;x,y=d*math.cos(theta),d*math.sin(theta)
        pad,surface=terrain.earth_patch(coll,soil,'Tierra · cúmulo torreón %s'%k,x,y,rx,ry,1.2+h*.5,p.seed+5100+k,getattr(p,'ground_roughness',.3))
        pieces=min(20,min(14,max(1,count//4))+extra_stone);boxes=[]
        for j in range(pieces):
            before=set(coll.objects);a=rr.random()*math.tau;rad=.7*math.sqrt((j+.5)/pieces)
            cx=x+rx*rad*math.cos(a);cy=y+ry*rad*math.sin(a);scale=rr.uniform(.6,1.0)
            fracture.broken_stone(coll,stone,cx,cy,rr.uniform(-math.pi,math.pi),h*1.6*scale,h*.8*scale,h*.62*scale,p.seed+6200+k*131+j,getattr(p,'wear',0))
            for ob in set(coll.objects)-before:
                terrain.settle_rubble(ob,surface);ob['escombro']=True
                co=primitives.coords(ob);boxes.append((float(co[:,0].min()),float(co[:,0].max()),float(co[:,1].min()),float(co[:,1].max())))
        # Maderos del interior en el borde del montón (las piedras ocupan el centro): vigas partidas y tablas.
        # Cada madero busca un hueco (caja en planta con 0,3 mm de holgura) entre piedras y maderos ya puestos; si no lo hay, no se pone.
        placed=0
        for j in range(timber):
            beam=j%2==0;length=rr.uniform(8,14) if beam else rr.uniform(8,16)
            width,height=(BEAM_SECTION[0]*.85,BEAM_SECTION[1]*.85) if beam else (3.,1.);corners=None
            for attempt in range(24):
                a=rr.random()*math.tau;rad=rr.uniform(.6,1.05);cx=x+rx*rad*math.cos(a);cy=y+ry*rad*math.sin(a)
                yaw=rr.uniform(-math.pi,math.pi);c,sn=math.cos(yaw),math.sin(yaw)
                trial=[(cx+u*length/2*c-v*width/2*sn,cy+u*length/2*sn+v*width/2*c) for u,v in ((-1,-1),(1,-1),(1,1),(-1,1))]
                bx=(min(q[0] for q in trial)-.3,max(q[0] for q in trial)+.3,min(q[1] for q in trial)-.3,max(q[1] for q in trial)+.3)
                if math.hypot(cx,cy)-length/2<r+.5:continue
                if any(bx[0]<b[1] and b[0]<bx[1] and bx[2]<b[3] and b[2]<bx[3] for b in boxes):continue
                corners=trial;boxes.append(bx);break
            if corners is None:continue
            placed+=1;z0=surface(cx,cy)+height*.5
            verts=[(px,py,z0) for px,py in corners]+[(px,py,z0+height) for px,py in corners]
            ob=primitives.mesh_obj('Madera · %s del torreón %s.%s'%('viga partida' if beam else 'tabla caída',k,j),verts,
                                   [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],coll,wood)
            terrain.settle_rubble(ob,surface);ob['escombro']=True;ob['tower_heap']=True
        terrain.gravel_batch(coll,stone,'Grava · torreón %s'%k,x,y,rx,ry,surface,10+3*pieces,p.seed+9500+k)
        audit.append({'angle':theta,'lost':count,'pieces':pieces,'timber':placed})
    return audit
