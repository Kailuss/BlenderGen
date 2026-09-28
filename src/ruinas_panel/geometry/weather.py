"""geometry /weather — ver docs/ARCHITECTURE.md para contratos y dependencias."""

from .. import config
from .. import runtime
from ..geometry import primitives
from ..services import profiling


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


def mesh_edges(obj):
    'IA: Pares de vértices de las aristas como matriz numpy (n, 2) en una sola llamada C.'
    import numpy
    ends=numpy.empty(len(obj.data.edges)*2,dtype=numpy.int32)
    obj.data.edges.foreach_get('vertices',ends)
    return ends.reshape(-1,2)


def vertex_normals(obj):
    'IA: Normales de vértice como matriz numpy (n, 3); lee en float32, el tipo nativo.'
    import numpy
    data=numpy.empty(len(obj.data.vertices)*3,dtype=numpy.float32)
    obj.data.vertices.foreach_get('normal',data)
    return data.reshape(-1,3).astype(numpy.float64)


def gaussian_field(edges,count,rng,iterations):
    'IA: Ruido blanco gaussiano por vértice difundido iterations veces entre vecinos (aprox. filtro gaussiano en la malla); media 0, desviación 1.'
    import numpy
    field=rng.standard_normal(count)
    if len(edges) and iterations:
        a,b=edges[:,0],edges[:,1]
        degree=numpy.bincount(edges.ravel(),minlength=count).astype(float)
        degree[degree==0]=1
        for _ in range(iterations):
            total=numpy.bincount(a,weights=field[b],minlength=count)+numpy.bincount(b,weights=field[a],minlength=count)
            field=.5*field+.5*total/degree
    field=field-field.mean()
    spread=field.std()
    return field/spread if spread>0 else field


def fine_relief(obj, spec, amount, seed):
    'IA: Poros y grano sembrados por pieza hacia dentro; intensidad progresiva sin saturar antes de amount=1.'
    import numpy
    rng=numpy.random.default_rng(seed+9001)
    edges=mesh_edges(obj)
    count=len(obj.data.vertices)
    strength=amount*(.7+.8*amount)
    pits=gaussian_field(edges,count,rng,spec['pit_iterations'])
    grain=gaussian_field(edges,count,rng,spec['grain_iterations'])
    # Poros donde el campo cae por debajo del umbral; el grano se normaliza a [0,1] para no sacar material.
    depth=spec['pits']*numpy.clip((-pits-spec['pit_threshold'])/1.2,0,1)**.7
    depth+=spec['grain']*(grain-grain.min())/max(1e-9,numpy.ptp(grain))
    co=primitives.coords(obj)-vertex_normals(obj)*(depth*strength)[:,None]
    primitives.set_coords(obj,co)


@profiling.timed("desgaste")
def weather_stone(obj, amount, seed):
    # Erosión hacia dentro; no desplaza las hiladas ni hincha los ladrillos.
    'IA: Erosión progresiva hacia dentro, limitada por espesor; semillas y densidad constantes entre intensidades positivas; cero no modifica la pieza.'
    import numpy
    if amount<=0 or runtime.quality not in config.DAMAGE_QUALITIES:
        return
    # Malla ligera desde el principio, sin crear alta resolución para reducirla después.
    mod=obj.modifiers.new('Superficie de trabajo lowpoly','SUBSURF')
    mod.subdivision_type='SIMPLE'
    # Esquirlas y fragmentos de agujero son prismas irregulares triangulados: más densidad los arruga.
    irregular=obj.name.startswith(('Esquirla','Piedra parcial'))
    mod.levels=1 if irregular else config.QUALITY[runtime.quality][0]
    primitives.apply_modifier(obj,mod)
    obj['vertices_desgaste_actuales']=len(obj.data.vertices)
    obj.data.update()
    spec=config.FINE_DETAIL.get(runtime.quality)
    if spec and not irregular:
        # Refinar antes de deformar conserva la rejilla y la densidad entre intensidades.
        refine_visible(obj,spec['edge'])
    co=primitives.coords(obj)
    normals=vertex_normals(obj)
    edges=mesh_edges(obj)
    count=len(co)
    rng=numpy.random.default_rng(seed+5123)
    character=rng.uniform(.8,1.15)
    scale=config.WEAR_NOISE['scale']
    broad=gaussian_field(edges,count,rng,config.WEAR_NOISE['broad'])*scale
    patch=gaussian_field(edges,count,rng,config.WEAR_NOISE['patch'])*scale
    grain=gaussian_field(edges,count,rng,config.WEAR_NOISE['grain'])*scale
    lo=co.min(axis=0)
    hi=co.max(axis=0)
    # Distancia a la segunda cara más cercana de la caja: cerca de una arista la erosión aumenta.
    border=numpy.sort(numpy.minimum(co-lo,hi-co),axis=1)[:,1]
    edge=numpy.clip(1-border/1.3,0,None)
    mask=numpy.clip(.4+patch,.05,1)
    # Grandes depresiones suaves y pequeñas zonas erosionadas, no ruido uniforme.
    loss=amount*character*(.08+.90*numpy.clip(broad+.25,0,None)**2
                           +.22*mask*numpy.clip(grain+.3,0,None)+edge*(.12+.3*numpy.clip(broad,0,None)))
    loss*=1+config.WEAR_RESPONSE['gain']*amount
    loss=numpy.minimum(loss, (hi-lo).min()*config.WEAR_RESPONSE['max_fraction'])
    primitives.set_coords(obj,co-normals*loss[:,None])
    bins=numpy.clip(((patch+.65)*3).astype(int),0,3)
    smooth_group=obj.vertex_groups.new(name='Erosion suavizada por zonas')
    for i in range(4):
        ids=numpy.nonzero(bins==i)[0].tolist()
        if ids:
            smooth_group.add(ids,.2+i*.25,'REPLACE')
    mod=obj.modifiers.new('Suavizado irregular de piedra','SMOOTH')
    mod.factor=.35*amount
    mod.iterations=1
    mod.vertex_group=smooth_group.name
    primitives.apply_modifier(obj,mod)
    if spec and not irregular:
        fine_relief(obj,spec,amount,seed)
    obj.data.shade_smooth()
