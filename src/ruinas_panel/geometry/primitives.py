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
    'IA: Crea y enlaza una malla; vértices en mm y caras con orientación exterior.'
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    coll.objects.link(obj)
    obj.data.materials.append(mat)
    return obj


@profiling.timed("biseles")
def bevel(obj, width):
    'IA: Aplica bisel según calidad; respeta la exclusión de mortero en previsualización.'
    if runtime.preview and not (obj.name.startswith(('Piedra','Esquirla')) or '· sillar' in obj.name):
        return
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    mod = obj.modifiers.new('Aristas modeladas', 'BEVEL')
    mod.width = width
    mod.segments = config.QUALITY[runtime.quality][2]
    bpy.ops.object.modifier_apply(modifier=mod.name)
    obj.select_set(False)


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
    bpy.context.view_layer.objects.active=obj
    mod=obj.modifiers.new('Relieve físico', 'SUBSURF')
    mod.subdivision_type='SIMPLE'
    mod.levels=2
    bpy.ops.object.modifier_apply(modifier=mod.name)
    obj.data.update()
    for v in obj.data.vertices:
        q=v.co
        field=noise.noise_vector(Vector((q.x*.65+seed,q.y*.65,q.z*.65)))
        v.co += v.normal.copy()*field.x*strength
    obj.data.update()


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
