"""Mallas por tramo/material para edición, conservando la identidad de cada pieza."""
import json
import numpy as np
from . import primitives
from ..services import profiling


@profiling.timed('agrupacion')
def pack_preview(coll):
    """IA: agrupa después del daño sin fusionar sólidos; conserva caras, UV, materiales, suavizado e IDs para futura selección por pieza."""
    groups={}
    for ob in list(coll.objects):
        if ob.get('ruin_instances'):
            continue
        key=(ob.get('wall_id','front'),tuple(m.name for m in ob.data.materials))
        groups.setdefault(key,[]).append(ob)
    created=[]
    for (wall,materials),objects in groups.items():
        if len(objects)<2:continue
        vertices=[];loops=[];starts=[];totals=[];smooth=[];slots=[];ids=[];parts=[];uvs=[]
        has_uv=any(o.data.uv_layers.active for o in objects)
        vo=lo=0
        for index,ob in enumerate(objects):
            me=ob.data
            co=primitives.coords(ob)
            matrix=np.array(ob.matrix_world,dtype=np.float64)
            co=co@matrix[:3,:3].T+matrix[:3,3]
            vertices.append(co)
            face_count=len(me.polygons)
            loop_ids=np.empty(len(me.loops),dtype=np.int32)
            me.loops.foreach_get('vertex_index',loop_ids)
            face_starts=np.empty(face_count,dtype=np.int32)
            face_totals=np.empty(face_count,dtype=np.int32)
            face_smooth=np.empty(face_count,dtype=np.bool_)
            face_slots=np.empty(face_count,dtype=np.int32)
            me.polygons.foreach_get('loop_start',face_starts)
            me.polygons.foreach_get('loop_total',face_totals)
            me.polygons.foreach_get('use_smooth',face_smooth)
            me.polygons.foreach_get('material_index',face_slots)
            uv=np.zeros((len(me.loops),2),dtype=np.float32)
            if me.uv_layers.active:me.uv_layers.active.data.foreach_get('uv',uv.ravel())
            uvs.append(uv)
            loops.append(loop_ids+vo);starts.append(face_starts+lo);totals.append(face_totals)
            smooth.append(face_smooth);slots.append(face_slots);ids.append(np.full(face_count,index,dtype=np.int32))
            parts.append({'key':primitives.piece_key(ob),'name':ob.name,'vertex_start':vo,'vertex_count':len(co),
                          'rubble':bool(ob.get('escombro')),
                          'partition':{k:ob[k] for k in ('partition_section','partition_id','rests_on') if k in ob}})
            vo+=len(co);lo+=len(me.loops)
        ob=primitives.mesh_obj('Tramo · '+wall+' · '+(materials[0] if materials else 'sin material'),[],[],coll,objects[0].data.materials[0])
        me=ob.data
        for mat in objects[0].data.materials[1:]:me.materials.append(mat)
        me.vertices.add(vo);me.loops.add(lo);me.polygons.add(sum(len(x) for x in starts))
        me.vertices.foreach_set('co',np.concatenate(vertices).astype(np.float32).ravel())
        me.loops.foreach_set('vertex_index',np.concatenate(loops))
        me.polygons.foreach_set('loop_start',np.concatenate(starts))
        me.polygons.foreach_set('loop_total',np.concatenate(totals))
        me.polygons.foreach_set('use_smooth',np.concatenate(smooth))
        me.polygons.foreach_set('material_index',np.concatenate(slots))
        me.update(calc_edges=True)
        if has_uv:
            layer=me.uv_layers.new(name='Fibra longitudinal')
            layer.data.foreach_set('uv',np.concatenate(uvs).ravel())
        attr=me.attributes.new('ruin_piece_id','INT','FACE')
        attr.data.foreach_set('value',np.concatenate(ids))
        ob['ruin_batch']=True;ob['wall_id']=wall;ob['ruin_parts']=json.dumps(parts,ensure_ascii=False)
        created.append(ob)
        primitives.remove_objects(objects)
    return created
