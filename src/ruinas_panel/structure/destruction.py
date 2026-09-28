"""Derrumbe espacial común de retornos y pilares, previo a ventanas y vigas."""
import math
import random
import zlib
from mathutils import Vector
from ..geometry import primitives
from .. import meta
from . import spatial


def height_at(p,x,y):
    'IA: Campo continuo determinista en XY; comparte altura entre el sillar de esquina y los dos paños que apoya.'
    return spatial.collapse_height(p,x,y)


def apply(coll,p,scene):
    'IA: Retira hiladas altas de retornos/columnas y recorta sus núcleos a la piedra superviviente; jamás toca marcos creados después.'
    meta.put(scene,'derrumbe_global',{})
    if p.collapse<=0:return
    discard=[];supports=[];cores=[];counts={}
    for ob in list(coll.objects):
        name=primitives.piece_key(ob)
        pillar=name.startswith('Pilar')
        wall=ob.get('wall_id','front')
        target=True
        if not target or not name.startswith(('Pilar','Piedra','Mortero')):continue
        if 'pie' in name:continue
        co=primitives.coords(ob);low=co.min(axis=0);high=co.max(axis=0);mid=(low+high)/2
        if pillar and 'núcleo' in name:
            cores.append(ob);continue
        top=height_at(p,mid[0],mid[1])
        if name.startswith('Mortero'):mid[2]+=.775
        if mid[2]>top and low[2]>3:
            discard.append(ob);counts[wall]=counts.get(wall,0)+1;continue
        if pillar:supports.append((mid.copy(),high[2]))
        ob['destruccion_global']=True
        # Rotura puntual del canto superior: conserva mayor parte del volumen y apoyo.
        if name.startswith(('Piedra','Pilar')) and high[2]>top-3 and p.collapse>.35:
            rng=random.Random(p.seed+zlib.crc32(name.encode()))
            if rng.random()<.45:
                corner=Vector((high[0],high[1],high[2]-.35))
                primitives.clip_closed(ob,corner,Vector((.25,.3,1)))
                ob['borde_agujero']=True  # No sustituir esta forma única por una caja GN.
    primitives.remove_objects(discard)
    for ob in cores:
        co=primitives.coords(ob);mid=(co.min(axis=0)+co.max(axis=0))/2
        tops=[height for center,height in supports if abs(center[0]-mid[0])<1 and abs(center[1]-mid[1])<1]
        if tops:
            co[:,2]=co[:,2].clip(max= max(tops)-1)
            primitives.set_coords(ob,co)
    counts['sin_apoyo']=prune_support(coll)
    meta.put(scene,'derrumbe_global',counts)


def prune_support(coll):
    'IA: Tras bajar pilares, retira piedras de fachada sin apoyo vertical y sus juntas; conserva escombros y al menos 12% de huella apoyada.'
    stones=[];mortar=[]
    for ob in coll.objects:
        name=primitives.piece_key(ob)
        if ob.get('escombro'):continue
        stone=name.startswith('Piedra') or (name.startswith('Pilar') and 'sillar' in name)
        if not stone and not name.startswith('Mortero'):continue
        co=primitives.coords(ob);lo=tuple(co.min(axis=0));hi=tuple(co.max(axis=0))
        (stones if stone else mortar).append((ob,lo,hi))
    kept=[];discard=[]
    for ob,lo,hi in sorted(stones,key=lambda item:item[1][2]):
        area=(hi[0]-lo[0])*(hi[1]-lo[1])
        support=0
        if lo[2]>3:
            for other,a,b in kept:
                if not lo[2]-1.8<=b[2]<=lo[2]+1.2:continue
                support+=max(0,min(hi[0],b[0])-max(lo[0],a[0]))*max(0,min(hi[1],b[1])-max(lo[1],a[1]))
        # El dintel de puerta se apoya en sus jambas de madera, fuera de esta lista de piedra.
        if lo[2]<=3 or support>=area*.12 or 'dintel' in primitives.piece_key(ob):
            kept.append((ob,lo,hi))
        else:discard.append(ob)
    for ob,lo,hi in mortar:
        mid=tuple((a+b)/2 for a,b in zip(lo,hi))
        if not any(a[2]-1<=mid[2]<=b[2] and a[0]-1<=mid[0]<=b[0]+1 and a[1]-1<=mid[1]<=b[1]+1 for other,a,b in kept):
            discard.append(ob)
    primitives.remove_objects(discard)
    return len(discard)
