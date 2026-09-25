"""geometry /primitives — ver docs/ARCHITECTURE.md para contratos y dependencias."""

from .. import config
from .. import runtime
from ..services import profiling
from mathutils import Vector
from mathutils import noise
import bpy


def material(name, color):
    'IA: Reutiliza materiales por nombre; evita crear uno por ladrillo.'
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    return m


def mesh_obj(name, verts, faces, coll, mat):
    'IA: Crea y enlaza una malla; vértices en mm, caras con orientación exterior y ruin_key con el nombre pedido.'
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    # Blender añade .001 si el nombre ya existe en el archivo; la clave conserva el nombre pedido.
    obj['ruin_key'] = name
    coll.objects.link(obj)
    obj.data.materials.append(mat)
    return obj


def piece_key(obj):
    'IA: Clave estable de una pieza para semillas; no cambia aunque Blender añada sufijos .001 al nombre.'
    return obj.get('ruin_key', obj.name)


def stage_scene():
    'IA: Escena de taller para aplicar modificadores pieza a pieza; se busca por nombre y se crea si falta.'
    stage = bpy.data.scenes.get(config.STAGE_SCENE)
    if stage is None:
        stage = bpy.data.scenes.new(config.STAGE_SCENE)
    return stage


def drop_stage():
    'IA: Borra la escena de taller al terminar una generación; sus piezas solo estaban enlazadas de paso.'
    stage = bpy.data.scenes.get(config.STAGE_SCENE)
    if stage is not None:
        bpy.data.scenes.remove(stage)


def apply_modifier(obj, mod, *operands):
    'IA: Aplica mod con solo obj y sus operandos en la escena de taller: coste por llamada constante; mismo resultado que en la escena principal.'
    if not config.ISOLATE_MODIFIERS:
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
        return
    stage = stage_scene()
    pieces = [obj, *operands]
    for piece in pieces:
        stage.collection.objects.link(piece)
    try:
        with bpy.context.temp_override(scene=stage, view_layer=stage.view_layers[0], object=obj,
                                       active_object=obj, selected_objects=[obj]):
            bpy.ops.object.modifier_apply(modifier=mod.name)
    finally:
        for piece in pieces:
            stage.collection.objects.unlink(piece)


@profiling.timed("biseles")
def bevel(obj, width):
    'IA: Aplica bisel según calidad; respeta la exclusión de mortero en previsualización.'
    if runtime.preview and not (obj.name.startswith(('Piedra','Esquirla')) or '· sillar' in obj.name):
        return
    mod = obj.modifiers.new('Aristas modeladas', 'BEVEL')
    mod.width = width
    mod.segments = config.QUALITY[runtime.quality][2]
    apply_modifier(obj, mod)


def block(name, x0, x1, y0, y1, z0, z1, coll, mat, rng=None, wear=0):
    'IA: Caja cerrada con bisel; mantén mínimos menores que máximos en los tres ejes.'
    verts = [(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),
             (x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)]
    if rng:
        verts = [(x + rng.uniform(-wear,wear), y + rng.uniform(-wear,wear),
                  z + rng.uniform(-wear,wear)) for x,y,z in verts]
    obj = mesh_obj(name, verts, [(0,3,2,1),(4,5,6,7),(0,1,5,4),
                   (1,2,6,5),(2,3,7,6),(3,0,4,7)], coll, mat)
    bevel(obj, min(.65, (z1-z0)*.12, (x1-x0)*.1))
    return obj


def relief(obj, strength, seed):
    'IA: Relieve auxiliar solo fuera de preview; cualquier aumento de subdivisión debe medirse.'
    if runtime.preview:
        return
    mod=obj.modifiers.new('Relieve físico', 'SUBSURF')
    mod.subdivision_type='SIMPLE'
    mod.levels=2
    apply_modifier(obj, mod)
    obj.data.update()
    for v in obj.data.vertices:
        q=v.co
        field=noise.noise_vector(Vector((q.x*.65+seed,q.y*.65,q.z*.65)))
        v.co += v.normal.copy()*field.x*strength
    obj.data.update()


def mesh_volume(mesh):
    'IA: Volumen en mm³ de una malla cerrada; solo mide, no modifica la malla.'
    import bmesh
    bm=bmesh.new()
    bm.from_mesh(mesh)
    volume=bm.calc_volume()
    bm.free()
    return volume


def clip_closed(ob,point,normal):
    'IA: Recorta con bmesh y tapa la sección; la salida debe seguir siendo cerrada.'
    import bmesh
    bm=bmesh.new()
    bm.from_mesh(ob.data)
    result=bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),
        dist=.00001,plane_co=point,plane_no=normal,clear_outer=True,clear_inner=False)
    edges=[e for e in result['geom_cut'] if isinstance(e,bmesh.types.BMEdge) and e.is_boundary]
    if edges:
        bmesh.ops.holes_fill(bm,edges=edges,sides=0)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()
