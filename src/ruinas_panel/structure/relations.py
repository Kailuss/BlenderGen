"""Relaciones explícitas entre piezas: roles, contactos y reservas de anclaje."""
import numpy as np
from .. import meta
from ..geometry import primitives


def register(coll,scene):
    'IA: Clasifica piezas antes de daño/GN y reserva mampostería en contacto con carpintería; conserva relaciones en metadatos de escena.'
    masonry=[];wood=[]
    for i,ob in enumerate(coll.objects):
        key=primitives.piece_key(ob)
        role='masonry' if key.startswith(('Piedra','Mortero','Pilar','Asiento')) and not ob.get('escombro') else ('wood' if ob.get('madera') else 'other')
        ob['element_role']=role;ob['element_id']='%s:%s:%s'%(ob.get('wall_id','front'),key,i)
        if role not in ('masonry','wood') or not ob.data.vertices:continue
        co=primitives.coords(ob);entry=(ob,co.min(axis=0),co.max(axis=0))
        (masonry if role=='masonry' else wood).append(entry)
    relations=[]
    if masonry:
        low=np.array([r[1] for r in masonry]);high=np.array([r[2] for r in masonry])
        for ob,a,b in wood:
            contact=np.nonzero(np.all((high>=a-1.0)&(low<=b+1.0),axis=1))[0]
            supports=[]
            for i in contact:
                stone=masonry[i][0];stone['protected_support']=True;supports.append(stone['element_id'])
            if supports:relations.append({'element':ob['element_id'],'role':'wood','supported_by':supports,'policy':'reserve_contact'})
    meta.put(scene,'relaciones_estructura',relations)
    return relations
