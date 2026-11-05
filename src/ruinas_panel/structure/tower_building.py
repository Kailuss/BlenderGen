"""Torreón, paso 2: mallas cerradas desde el aparejo puro de tower_plan (circular y cuadrado).

Cada piedra es una pieza cerrada; un núcleo de mortero por hilada, embebido como en los muros, rellena las
juntas por dentro para que la pieza impresa quede unida. Medidas en mm y marcas de aparejo (C5-5) desde el inicio.
"""
import math
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
        verts,faces=ring_mesh(r_in+CORE_INSET*t,r_out-CORE_INSET*t,oz+course['z0']-.85 if course['row'] else oz+course['z0'],oz+course['z1']-.7)
        verts=[(x+ox,y+oy,z) for x,y,z in verts]
        ob=primitives.mesh_obj('Mortero · torreón %s'%course['row'],verts,faces,coll,core)
        identifiers.tag(ob,'mortar',course['row'],0);ob['wall_id']='torreon';made.append(ob)
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
        xs=[v for s in course['stones'] for v in s['x']];ys=[v for s in course['stones'] for v in s['y']]
        half=max(max(xs),-min(xs));inner=min(abs(v) for s in course['stones'] if s['wall'] in ('left','right') for v in s['x'])
        t=half-inner;a,b=half-CORE_INSET*t,inner+CORE_INSET*t
        zc0=oz+course['z0']-.85 if course['row'] else oz+course['z0'];zc1=oz+course['z1']-.7
        for k,(x0,x1,y0,y1) in enumerate(((-a,a,-a,-b),(-a,a,b,a),(-a,-b,-b,b),(b,a,-b,b))):
            ob=primitives.block('Mortero · torreón %s'%course['row'],ox+x0,ox+x1,oy+y0,oy+y1,zc0,zc1,coll,core)
            identifiers.tag(ob,'mortar',course['row'],k);ob['wall_id']='torreon';made.append(ob)
    return made
