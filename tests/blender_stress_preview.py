"""Inspección visual de la carga antes de exportar."""
import sys
from pathlib import Path
import bpy
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tests'))
from blender_v032 import render


def run():
    'IA: Renderiza poses inicial y final sin modificar el archivo calculado; informa extensión para detectar expulsiones numéricas.'
    scene=next(s for s in bpy.data.scenes if s.get('physics_result_scene'));bpy.context.window.scene=scene
    for ob in scene.objects:
        if ob.get('collision_floor'):ob.hide_render=True
    for frame,label in ((1,'before'),(scene.frame_end,'after')):
        scene.frame_set(frame)
        points=[o.matrix_world@Vector(v) for o in scene.objects if o.type=='MESH' and not o.get('collision_floor') and not o.get('impactor') for v in o.bound_box]
        lo=Vector([min(v[k] for v in points) for k in range(3)]);hi=Vector([max(v[k] for v in points) for k in range(3)])
        print('PREVIEW_BOUNDS',frame,list(lo),list(hi),flush=True)
        if frame==1:center=(lo+hi)*.5;span=max(hi-lo)
        render(scene,ROOT/('reports/stress_max_'+label+'.png'),focus=center,location=center+Vector((.34,-.4,.3)),scale=span*1.7)


if __name__=='__main__':run()