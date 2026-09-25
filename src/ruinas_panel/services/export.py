"""services /export — ver docs/ARCHITECTURE.md para contratos y dependencias."""

from .. import config
from ..services import generation
from ..services import profiling
import bpy
import math
import time


def discard_objects(names):
    'IA: Elimina por nombre objetos temporales de una fusión fallida y sus mallas sin usuarios; ignora los ya borrados.'
    for name in names:
        ob=bpy.data.objects.get(name)
        if not ob:
            continue
        mesh=ob.data
        bpy.data.objects.remove(ob,do_unlink=True)
        if mesh and mesh.users==0:
            bpy.data.meshes.remove(mesh)


@profiling.timed("fusion")
def make_solid(context, voxel=None):
    'IA: Fusiona copias y valida componentes; si falla, borra copias y sólido parcial y deja la fuente intacta.'
    start=time.perf_counter()
    if voxel is None:
        voxel=config.QUALITY[context.scene.ruin_settings.export_quality][1]
    src=bpy.data.collections.get(config.COLLECTION)
    if not src or not src.objects:
        raise ValueError('Genera primero el muro.')
    old=bpy.data.objects.get(config.SOLID_NAME)
    if old:
        bpy.data.objects.remove(old,do_unlink=True)
    bpy.ops.object.select_all(action='DESELECT')
    copies=[]
    try:
        for obj in src.objects:
            ob=obj.copy()
            ob.data=obj.data.copy()
            context.scene.collection.objects.link(ob)
            ob.hide_set(False)
            ob.select_set(True)
            copies.append(ob.name)
        context.view_layer.objects.active=bpy.data.objects[copies[0]]
        bpy.ops.object.join()
        obj=context.object
        obj.name=config.SOLID_NAME
        copies.append(obj.name)
        obj['voxel_mm']=voxel
        mod=obj.modifiers.new('Unión volumétrica maciza', 'REMESH')
        mod.mode='VOXEL'
        mod.voxel_size=voxel
        mod.use_smooth_shade=False
        bpy.ops.object.modifier_apply(modifier=mod.name)
        mod=obj.modifiers.new('Suavizado mínimo de voxel','SMOOTH')
        mod.factor=.28
        mod.iterations=2
        bpy.ops.object.modifier_apply(modifier=mod.name)
        mod=obj.modifiers.new('Reducir caras coplanares','DECIMATE')
        mod.ratio=.28
        bpy.ops.object.modifier_apply(modifier=mod.name)
        # Limpiar residuos del remallado; conservar cualquier fragmento de volumen apreciable.
        import bmesh
        bm=bmesh.new()
        bm.from_mesh(obj.data)
        remaining=set(bm.verts)
        parts=[]
        while remaining:
            group={remaining.pop()}
            stack=list(group)
            while stack:
                v=stack.pop()
                for e in v.link_edges:
                    w=e.other_vert(v)
                    if w in remaining:
                        remaining.remove(w)
                        group.add(w)
                        stack.append(w)
            parts.append(group)
        parts.sort(key=len,reverse=True)
        removed=0
        for group in parts[1:]:
            span=[max(v.co[i] for v in group)-min(v.co[i] for v in group) for i in range(3)]
            dust=max(span)<=2.5 and math.prod(span)<=1.0
            needle=max(span)<=4 and min(span)<voxel*.5 and math.prod(span)<.2
            if not (dust or needle):
                position=[round(min(v.co[i] for v in group),1) for i in range(3)]
                bm.free()
                raise ValueError('Fragmento suelto de %s mm en %s: prueba otra semilla o menos derrumbe/daño.'
                                 %('×'.join('%.1f'%s for s in span),position))
            removed+=1
            bmesh.ops.delete(bm,geom=list(group),context='VERTS')
        bm.to_mesh(obj.data)
        bm.free()
    except Exception:
        discard_objects(copies)
        raise
    obj['particulas_submilimetricas_eliminadas']=removed
    for face in obj.data.polygons:
        face.use_smooth=True
    for ob in src.objects:
        ob.hide_set(True)
        ob.hide_render=True
    generation.metrics(context,src,{'fusion':time.perf_counter()-start,'total':time.perf_counter()-start},False,solid=obj)
    return obj
