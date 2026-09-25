"""geometry /weather — ver docs/ARCHITECTURE.md para contratos y dependencias."""

from .. import config
from .. import runtime
from ..geometry import primitives
from ..services import profiling
from mathutils import Vector
from mathutils import noise
import bpy
import random


def refine_visible(obj, target):
    'IA: Subdivide aristas de caras visibles (frente, dorso y techo) hasta ~target mm, por pasadas del grupo más largo; juntas y base no se densifican.'
    import bmesh
    import numpy
    me=obj.data
    for _ in range(8):
        co=primitives.coords(obj)
        ends=numpy.empty(len(me.edges)*2,dtype=numpy.int32)
        me.edges.foreach_get('vertices',ends)
        ends=ends.reshape(-1,2)
        normals=numpy.empty(len(me.polygons)*3,dtype=numpy.float32)
        me.polygons.foreach_get('normal',normals)
        normals=normals.reshape(-1,3)
        starts=numpy.empty(len(me.polygons),dtype=numpy.int32)
        totals=numpy.empty(len(me.polygons),dtype=numpy.int32)
        me.polygons.foreach_get('loop_start',starts)
        me.polygons.foreach_get('loop_total',totals)
        loop_edges=numpy.empty(len(me.loops),dtype=numpy.int32)
        me.loops.foreach_get('edge_index',loop_edges)
        # Incluir biseles (normal a ~45°): si solo se densifica la cara plana queda un labio en el borde.
        visible=(numpy.abs(normals[:,1])>.3)|(normals[:,2]>.3)
        owner=numpy.repeat(numpy.arange(len(starts)),totals)
        loops=numpy.repeat(starts,totals)+numpy.arange(len(owner))-numpy.repeat(numpy.cumsum(totals)-totals,totals)
        edges=numpy.unique(loop_edges[loops[visible[owner]]])
        lengths=numpy.linalg.norm(co[ends[edges,0]]-co[ends[edges,1]],axis=1)
        cuts=numpy.minimum(numpy.ceil(lengths/target).astype(int)-1,24)
        if not len(cuts) or cuts.max()<1:
            break
        top=int(cuts.max())
        # Una sola longitud por pasada: las aristas opuestas reciben los mismos cortes y el relleno forma rejilla.
        bm=bmesh.new()
        bm.from_mesh(me)
        bm.edges.ensure_lookup_table()
        bmesh.ops.subdivide_edges(bm,edges=[bm.edges[i] for i in edges[cuts==top]],cuts=top,use_grid_fill=True)
        bm.to_mesh(me)
        bm.free()
        me.update()


def fine_relief(obj, spec, amount):
    'IA: Picado Voronoi y grano de nubes hacia dentro con Displace en coordenadas globales: rápido, determinista y sin hinchar la pieza.'
    layers=(('Ruinas · picado','VORONOI',spec['pit_scale'],spec['pits']),('Ruinas · grano','CLOUDS',spec['grain_scale'],spec['grain']))
    for name,kind,size,depth in layers:
        texture=bpy.data.textures.get(name) or bpy.data.textures.new(name,kind)
        texture.noise_scale=size
        texture.use_clamp=True
        mod=obj.modifiers.new(name,'DISPLACE')
        mod.texture=texture
        mod.texture_coords='GLOBAL'
        mod.direction='NORMAL'
        # Con mid_level 1, un valor de textura en [0,1] solo desplaza hacia dentro, hasta depth·amount.
        mod.mid_level=1.0
        mod.strength=depth*min(1.0,amount*1.4)
        primitives.apply_modifier(obj,mod)


@profiling.timed("desgaste")
def weather_stone(obj, amount, seed):
    # Erosión hacia dentro; no desplaza las hiladas ni hincha los ladrillos.
    'IA: Desgaste hacia dentro sin cambiar hiladas; en calidades de config.FINE_DETAIL añade densidad visible y picado imprimible.'
    if amount<=0:
        return
    # Misma geometría de desgaste al editar y al preparar el sólido.
    # La densidad depende de milímetros, no de un número fijo por ladrillo.
    # Malla ligera desde el principio, sin crear alta resolución para reducirla después.
    mod=obj.modifiers.new('Superficie de trabajo lowpoly','SUBSURF')
    mod.subdivision_type='SIMPLE'
    mod.levels=1 if obj.name.startswith('Esquirla') else config.QUALITY[runtime.quality][0]
    primitives.apply_modifier(obj,mod)
    obj['vertices_desgaste_actuales']=len(obj.data.vertices)
    obj.data.update()
    coords=[v.co.copy() for v in obj.data.vertices]
    normals=[v.normal.copy() for v in obj.data.vertices]
    lo=Vector(tuple(min(q[i] for q in coords) for i in range(3)))
    hi=Vector(tuple(max(q[i] for q in coords) for i in range(3)))
    rr=random.Random(seed+5123)
    character=rr.uniform(.8,1.15)
    scale=rr.uniform(.16,.30)
    bins=[[],[],[],[]]
    offset=Vector((seed*.137,seed*.071,seed*.193))
    for v,q,n in zip(obj.data.vertices,coords,normals):
        distances=sorted(min(q[i]-lo[i],hi[i]-q[i]) for i in range(3))
        edge=max(0,1-distances[1]/1.3)
        broad=noise.noise_vector(q*scale+offset).x
        patch=noise.noise_vector(q*.12+offset).y
        grain=noise.noise_vector(q*.35+offset).z
        mask=max(.05,min(1,.4+patch))
        # Grandes depresiones suaves y pequeñas zonas erosionadas, no ruido uniforme.
        loss=amount*character*(.08+.90*max(0,broad+.25)**2+
                              .22*mask*max(0,grain+.3)+edge*(.12+.3*max(0,broad)))
        v.co=q-n*loss
        bins[max(0,min(3,int((patch+.65)*3)))].append(v.index)
    smooth_group=obj.vertex_groups.new(name='Erosion suavizada por zonas')
    for i,ids in enumerate(bins):
        if ids:
            smooth_group.add(ids,.2+i*.25,'REPLACE')
    mod=obj.modifiers.new('Suavizado irregular de piedra','SMOOTH')
    mod.factor=.35
    mod.iterations=1
    mod.vertex_group=smooth_group.name
    primitives.apply_modifier(obj,mod)
    spec=config.FINE_DETAIL.get(runtime.quality)
    if spec and not obj.name.startswith('Esquirla'):
        refine_visible(obj,spec['edge'])
        fine_relief(obj,spec,amount)
    for face in obj.data.polygons:
        face.use_smooth=True
    obj.data.update()
