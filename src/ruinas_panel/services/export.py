"""services /export — ver docs/ARCHITECTURE.md para contratos y dependencias."""

from .. import config
from .. import runtime
from ..services import generation
from ..services import profiling
from ..geometry import primitives
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


def shells(bm):
    'IA: Cáscaras conexas de un bmesh como (vértices, volumen con signo); volumen negativo indica un hueco interior.'
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
        faces={f for v in group for f in v.link_faces}
        volume=sum(f.calc_area()*f.normal.dot(f.calc_center_median()) for f in faces)/3
        parts.append((group,volume))
    return parts


def fuse_voxel(obj,voxel):
    'IA: Remallado vóxel + suavizado + colapso al 28 %; borra polvo y agujas y rechaza fragmentos apreciables.'
    import bmesh
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
    # Colapso uniforme al 28 %: desviación máx. ~0,04 mm. La disolución planar deja menos caras pero tarda ~25 veces más.
    mod=obj.modifiers.new('Reducir densidad (colapso 28 %)','DECIMATE')
    mod.decimate_type='COLLAPSE'
    mod.ratio=.28
    bpy.ops.object.modifier_apply(modifier=mod.name)
    # Limpiar residuos del remallado; conservar cualquier fragmento de volumen apreciable.
    bm=bmesh.new()
    bm.from_mesh(obj.data)
    parts=sorted((group for group,_ in shells(bm)),key=len,reverse=True)
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
    obj['particulas_submilimetricas_eliminadas']=removed
    for face in obj.data.polygons:
        face.use_smooth=True


def fuse_manifold(context,obj,names,validate=True):
    'IA: Une obj con el resto de copias mediante booleano Manifold exacto; limpia residuos y huecos interiores por volumen.'
    import bmesh
    union=bpy.data.collections.new('MURO · unión temporal')
    context.scene.collection.children.link(union)
    try:
        for name in names[1:]:
            ob=bpy.data.objects[name]
            context.scene.collection.objects.unlink(ob)
            union.objects.link(ob)
        mod=obj.modifiers.new('Unión exacta de piezas','BOOLEAN')
        mod.operation='UNION'
        mod.operand_type='COLLECTION'
        mod.collection=union
        mod.solver='MANIFOLD'
        context.view_layer.objects.active=obj
        result=bpy.ops.object.modifier_apply(modifier=mod.name)
        if 'FINISHED' not in result:
            raise ValueError('No se pudo unir el lote: '+obj.name)
    finally:
        discard_objects(names[1:])
        bpy.data.collections.remove(union)
    if not validate:
        return
    bm=bmesh.new()
    bm.from_mesh(obj.data)
    parts=sorted(shells(bm),key=lambda part:part[1],reverse=True)
    debris=cavities=0
    for group,volume in parts[1:]:
        if volume<0:
            cavities+=1
        elif volume<config.EXPORT_DEBRIS_MM3:
            debris+=1
        else:
            span=[max(v.co[i] for v in group)-min(v.co[i] for v in group) for i in range(3)]
            position=[round(min(v.co[i] for v in group),1) for i in range(3)]
            bm.free()
            raise ValueError('Fragmento suelto de %s mm (%.1f mm³) en %s: prueba otra semilla o menos derrumbe/daño.'
                             %('×'.join('%.1f'%s for s in span),volume,position))
        bmesh.ops.delete(bm,geom=list(group),context='VERTS')
    bm.to_mesh(obj.data)
    bm.free()
    obj['residuos_eliminados']=debris
    obj['huecos_interiores_eliminados']=cavities


def fuse_heights(context,names):
    'IA: Une piezas completas en lotes de altura de 20 mm y hasta 60k caras; no corta superficies ni elimina componentes intermedios.'
    buckets={}
    for name in names:
        obj=bpy.data.objects[name]
        co=primitives.coords(obj)
        band=int(float((co[:,2].min()+co[:,2].max())/2)//20)
        buckets.setdefault(band,[]).append(name)
    stage=[]
    for band,group in sorted(buckets.items()):
        chunk=[];count=0
        for name in group:
            faces=len(bpy.data.objects[name].data.polygons)
            if chunk and count+faces>60000:
                first=bpy.data.objects[chunk[0]]
                fuse_manifold(context,first,chunk,validate=False);stage.append(first.name)
                chunk=[];count=0
            chunk.append(name);count+=faces
        if chunk:
            first=bpy.data.objects[chunk[0]]
            if len(chunk)>1:fuse_manifold(context,first,chunk,validate=False)
            stage.append(first.name)
    batches=len(stage)
    # Árbol de uniones: reduce el número de operandos sin duplicar piezas entre franjas.
    while len(stage)>4:
        following=[]
        for i in range(0,len(stage),4):
            group=stage[i:i+4];first=bpy.data.objects[group[0]]
            if len(group)>1:fuse_manifold(context,first,group,validate=False)
            following.append(first.name)
        stage=following
    first=bpy.data.objects[stage[0]]
    fuse_manifold(context,first,stage)
    first['lotes_altura']=batches
    return first


def printable_mesh(obj,density):
    'IA: Valida triángulos con vértices coincidentes soldados, como STL; si los n-gons booleanos fallan, normaliza por vóxel antes de entregar.'
    import bmesh
    for attempt in range(2):
        bm=bmesh.new();bm.from_mesh(obj.data)
        bmesh.ops.triangulate(bm,faces=list(bm.faces),quad_method='FIXED',ngon_method='EAR_CLIP')
        bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000001)
        valid=bool(bm.faces) and all(e.is_manifold for e in bm.edges) and all(f.calc_area()>1e-12 for f in bm.faces)
        if valid:
            bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
            bm.to_mesh(obj.data);bm.free();obj.data.update()
            obj['triangulacion_validada']=True
            return
        bm.free()
        if attempt==0:
            # Remalla la superficie ya unida, nunca miles de piezas densas simultáneas.
            resolution=.30+.15*(1-density)
            bpy.context.view_layer.objects.active=obj
            fuse_voxel(obj,resolution)
            obj['normalizacion_voxel']=resolution
    raise ValueError('La triangulación final no es cerrada. La fuente y el sólido anterior se conservan.')


@profiling.timed("fusion")
def make_solid(context, voxel=None, method=None):
    'IA: Omite piezas sin caras, fusiona copias (Manifold o vóxel) y valida cáscaras; si falla, borra copias y sólido parcial y deja la fuente intacta.'
    start=time.perf_counter()
    method=method or config.EXPORT_METHOD
    from ..geometry import instances
    if voxel is None:
        voxel=config.QUALITY[context.scene.ruin_settings.export_quality][1]
    src=bpy.data.collections.get(config.COLLECTION)
    if not src or not src.objects:
        raise ValueError('Genera primero el muro.')
    if any(ob.get('ruin_batch') for ob in src.objects):
        # Las islas agrupadas son una representación de edición, no operandos de unión.
        was_preview,was_busy=runtime.preview,runtime.busy
        runtime.preview=False;runtime.busy=True
        try:
            src=generation.generate(context,context.scene.ruin_settings,context.scene.ruin_settings.export_quality)
        finally:
            runtime.preview=was_preview;runtime.busy=was_busy
    faces=instances.expanded_faces(src)
    if faces>config.EXPORT_FACE_LIMIT:
        raise ValueError('Fuente de más de 4 millones de caras: reduce Densidad del sólido o divide en tramos antes de fusionar.')
    old=bpy.data.objects.get(config.SOLID_NAME)
    bpy.ops.object.select_all(action='DESELECT')
    copies=[]
    try:
        for obj in src.objects:
            if obj.get('ruin_instances'):
                for ob in instances.export_copies(obj,context.scene.collection,context.scene.ruin_settings.export_density):
                    ob.select_set(True)
                    copies.append(ob.name)
                continue
            if not obj.data.polygons:continue
            ob=primitives.reduced_copy(obj,context.scene.ruin_settings.export_density)
            if not ob.data.polygons:
                primitives.remove_objects([ob])
                continue
            context.scene.collection.objects.link(ob)
            ob.hide_set(False)
            ob.select_set(True)
            copies.append(ob.name)
        if not copies:raise ValueError('No quedan caras exportables tras los recortes de daño.')
        first=bpy.data.objects[copies[0]]
        context.view_layer.objects.active=first
        if method=='MANIFOLD':
            obj=fuse_heights(context,copies)
        else:
            bpy.ops.object.join()
            obj=context.object
        obj['metodo_fusion']=method
        if method!='MANIFOLD':
            fuse_voxel(obj,voxel)
        printable_mesh(obj,context.scene.ruin_settings.export_density)
        if old:
            primitives.remove_objects([old])
        obj.name=config.SOLID_NAME
        copies.append(obj.name)
    except Exception:
        discard_objects(copies)
        raise
    finally:
        primitives.drop_stage()
    for ob in src.objects:
        ob.hide_set(True)
        ob.hide_render=True
    obj.select_set(True)
    context.view_layer.objects.active=obj
    generation.metrics(context,src,{'fusion':time.perf_counter()-start,'total':time.perf_counter()-start},False,solid=obj)
    return obj
