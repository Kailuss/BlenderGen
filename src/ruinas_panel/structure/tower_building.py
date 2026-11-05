"""Torreón, paso 2: mallas cerradas desde el aparejo puro de tower_plan (circular y cuadrado).

Cada piedra es una pieza cerrada; un núcleo de mortero por hilada, embebido como en los muros, rellena las
juntas por dentro para que la pieza impresa quede unida. Medidas en mm y marcas de aparejo (C5-5) desde el inicio.
"""
import math
import bpy
from .. import config_masonry as masonry
from ..construction_core import identifiers
from ..geometry import primitives
from . import tower_plan

SEGMENT_MM=1.6      # cuerda máxima de las caras curvas
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
        r_in,r_out=course['r_in'],course['r_out'];t=r_out-r_in
        for index,(a0,a1) in enumerate(course['stones']):
            gap=tower_plan.JOINT_MM/2/r_out
            verts,faces=sector_mesh(r_in,r_out,a0+gap,a1-gap,z0,z1)
            verts=[(x+ox,y+oy,z) for x,y,z in verts]
            ob=primitives.mesh_obj('Piedra · torreón %s.%s'%(course['row'],index),verts,faces,coll,stone)
            identifiers.tag(ob,'stone',course['row'],index);ob['wall_id']='torreon';made.append(ob)
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
        # Núcleo por muro, solo a lo largo de las piedras vivas de esa hilada y dentro del grosor.
        zc0=oz+course['z0']-.85 if course['row'] else oz+course['z0'];zc1=oz+course['z1']-.7
        for k,wall in enumerate(('front','back','left','right')):
            own=[s for s in course['stones'] if s['wall']==wall]
            if not own:continue
            along=0 if wall in ('front','back') else 1;across=1-along
            lo=min(s['x' if along==0 else 'y'][0] for s in own);hi=max(s['x' if along==0 else 'y'][1] for s in own)
            c0=own[0]['y' if along==0 else 'x'][0];c1=own[0]['y' if along==0 else 'x'][1];t=c1-c0
            c0,c1=c0+CORE_INSET*t,c1-CORE_INSET*t;lo,hi=lo+CORE_INSET*t,hi-CORE_INSET*t
            if hi-lo<tower_plan.MIN_STONE_MM:continue
            x0,x1,y0,y1=(lo,hi,c0,c1) if along==0 else (c0,c1,lo,hi)
            ob=primitives.block('Mortero · torreón %s'%course['row'],ox+x0,ox+x1,oy+y0,oy+y1,zc0,zc1,coll,core)
            identifiers.tag(ob,'mortar',course['row'],k);ob['wall_id']='torreon';made.append(ob)
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
    thickness=min(p.thickness,p.tower_size*.3)
    if p.tower_shape=='ROUND':
        plan=tower_plan.round_plan(p.tower_size/2,thickness,p.tower_height,p.stone_size,seed=p.seed,variation=p.stone_variation,slits=p.tower_slits,floors=p.tower_floors)
        plan,removed=tower_plan.ruin_round(plan,p.tower_height,seed=p.seed,amount=p.tower_ruin)
        made=build_round(coll,plan,stone,core)
    else:
        plan=tower_plan.square_plan(p.tower_size,thickness,p.tower_height,p.stone_size,seed=p.seed,variation=p.stone_variation,slits=min(1,p.tower_slits),floors=p.tower_floors)
        plan,removed=tower_plan.ruin_square(plan,p.tower_height,seed=p.seed,amount=p.tower_ruin)
        made=build_square(coll,plan,stone,core)
    return {'stones':sum(o.name.startswith('Piedra') for o in made),'removed':removed,'pieces':len(made)}
