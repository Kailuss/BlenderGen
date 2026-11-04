"""Derrumbe espacial común de retornos y pilares, previo a ventanas y vigas."""
import math
import random
import zlib
from mathutils import Vector
from ..geometry import primitives
from .. import meta
from ..services import removal_events
from ..construction_core import stacking
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
                removal_events.clip(ob,corner,Vector((.25,.3,1)),'COLLAPSE_EDGE')
                ob['borde_agujero']=True  # No sustituir esta forma única por una caja GN.
    removal_events.remove(discard,'GLOBAL_COLLAPSE')
    for ob in cores:
        co=primitives.coords(ob);mid=(co.min(axis=0)+co.max(axis=0))/2
        tops=[height for center,height in supports if abs(center[0]-mid[0])<1 and abs(center[1]-mid[1])<1]
        if tops:
            before=removal_events.fingerprint(ob)
            co[:,2]=co[:,2].clip(max= max(tops)-1)
            primitives.set_coords(ob,co)
            removal_events.cut_confirmed(ob,before,'PILLAR_CORE_LOWERED',{'max_z_mm':max(tops)-1})
    counts['sin_apoyo']=prune_support(coll)
    meta.put(scene,'derrumbe_global',counts)


def prune_support(coll):
    'IA: Tras bajar pilares, retira piedras de fachada sin apoyo vertical y sus juntas; la regla vive en construction_core.stacking (C5-4).'
    stones=[];mortar=[];objects={}
    for ob in coll.objects:
        name=primitives.piece_key(ob)
        if ob.get('escombro'):continue
        stone=name.startswith('Piedra') or (name.startswith('Pilar') and 'sillar' in name)
        if not stone and not name.startswith('Mortero'):continue
        co=primitives.coords(ob);lo=tuple(co.min(axis=0));hi=tuple(co.max(axis=0))
        objects[ob.name]=ob
        # El dintel de puerta se apoya en sus jambas de madera, fuera de esta lista de piedra.
        (stones if stone else mortar).append((ob.name,lo,hi,'dintel' in name))
    _,discard=stacking.prune(stones,mortar)
    discard=[objects[key] for key in discard]
    removal_events.remove(discard,'PRUNE_SUPPORT')
    return len(discard)
