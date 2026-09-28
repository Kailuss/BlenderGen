"""Perforaciones por pared con semilla propia y respeto de anclajes."""
import random
import zlib
import numpy as np
from mathutils import Vector
from .. import meta
from ..geometry import primitives
from . import openings


def local_bounds(ob,w):
    'IA: Caja local del muro calculada en bloque; no confundir izquierda/derecha con los ejes globales.'
    co=primitives.coords(ob);a=w['axis'];o=w['origin'];dx=co[:,0]-o[0];dy=co[:,1]-o[1]
    local=np.column_stack((dx*a[0]+dy*a[1],-dx*a[1]+dy*a[0],co[:,2]))
    return local.min(axis=0),local.max(axis=0)


def apply(coll,p,scene,walls):
    'IA: Huecos por pared sobre mampostería ya montada; reserva madera y sus contactos, recorta cantos y registra centros efectivos.'
    records=[];discard=[];used=set()
    for w in walls:
        if p.hole_count==0:break
        entries=[]
        for ob in coll.objects:
            key=primitives.piece_key(ob)
            if ob.get('wall_id','front')!=w['id'] or ob.get('escombro') or ob.get('protected_sill'):continue
            if not key.startswith(('Piedra','Mortero')) or 'dintel' in key:continue
            if not ob.data.vertices:continue
            lo,hi=local_bounds(ob,w)
            if lo[2]<3:continue
            entries.append((ob,lo,hi,(lo+hi)/2,key.startswith('Piedra')))
        rng=random.Random(p.seed+p.hole_seed*104729+zlib.crc32(w['id'].encode()))
        candidates=[e for e in entries if e[4] and not e[0].get('protected_support')]
        rng.shuffle(candidates);made=[]
        for ob,lo,hi,mid,is_stone in candidates:
            if len(made)>=p.hole_count:break
            if ob.as_pointer() in used:continue
            cx=float(mid[0]+rng.uniform(-.2,.2)*(hi[0]-lo[0]));cz=float(mid[2]+rng.uniform(-.15,.15)*(hi[2]-lo[2]))
            rx=p.hole_size/2;rz=rx*.85
            if cx-rx<w['start']+1 or cx+rx>w['end']-1 or cz-rz<3 or cz+rz>p.height-2:continue
            if any(abs(cx-h['x'])<rx*2 and abs(cz-h['z'])<rz*2 for h in made):continue
            selected=[];border=[]
            for obj,a,b,m,stone in entries:
                if obj.as_pointer() in used or obj.get('protected_support'):continue
                q=((m[0]-cx)/rx)**2+((m[2]-cz)/rz)**2
                if q<.85:selected.append((obj,a,b,m,stone))
                elif q<1.8:border.append((obj,a,b,m,stone))
            if not any(e[4] for e in selected):continue
            for obj,a,b,m,stone in selected:used.add(obj.as_pointer());discard.append(obj)
            for obj,a,b,m,stone in border:
                if p.hole_damage<=0:continue
                direction=Vector((w['axis'][0]*(cx-m[0]),w['axis'][1]*(cx-m[0]),cz-m[2]))
                if direction.length<.1:continue
                direction.normalize()
                center=Vector(openings.wall_point(w,float(m[0]),float(m[1]),float(m[2])))
                distance=min(b[0]-a[0],b[2]-a[2])*(.48-.3*p.hole_damage)
                primitives.clip_closed(obj,center+direction*distance,direction)
                obj['borde_agujero']=True;used.add(obj.as_pointer())
            item={'wall':w['id'],'x':cx,'z':cz,'x0':cx-rx,'x1':cx+rx,'z0':cz-rz,'z1':cz+rz,'removed':len(selected),'border':len(border)}
            made.append(item);records.append(item)
    primitives.remove_objects(discard)
    meta.put(scene,'huecos_generados',records);meta.put(scene,'huecos_solicitados',p.hole_count*len(walls))
