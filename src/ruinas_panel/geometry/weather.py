"""geometry /weather — ver docs/ARCHITECTURE.md para contratos y dependencias."""

from .. import config
from .. import runtime
from ..geometry import primitives
from ..services import profiling
from mathutils import Vector
from mathutils import noise
import bpy
import random


@profiling.timed("desgaste")
def weather_stone(obj, amount, seed):
    # Erosión hacia dentro; no desplaza las hiladas ni hincha los ladrillos.
    'IA: Aplica desgaste hacia dentro sin cambiar las hiladas; usa la calidad activa y la semilla local.'
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
    for face in obj.data.polygons:
        face.use_smooth=True
    obj.data.update()
