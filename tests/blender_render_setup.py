"""Perfil de render sin alterar geometría ni animación física."""
import sys
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import ruinas_panel as addon
from ruinas_panel import runtime
from ruinas_panel.services import lab_cameras


def run():
    'IA: Verifica render repetible, materiales compartidos, DOF remapeado y codificación real de vídeo con dos fotogramas económicos.'
    addon.register();runtime.busy=True
    scene=bpy.context.scene
    for ob in list(scene.objects):bpy.data.objects.remove(ob,do_unlink=True)
    bpy.ops.mesh.primitive_cube_add(size=.1)
    cube=bpy.context.object
    mat=bpy.data.materials.new('Piedra prueba');mat.diffuse_color=(.4,.3,.2,1);cube.data.materials.append(mat)
    cube.keyframe_insert(data_path='location',frame=1)
    cube.location.z=.01;cube.keyframe_insert(data_path='location',frame=2)
    mesh=cube.data;vertices=[tuple(v.co) for v in mesh.vertices];action=cube.animation_data.action
    lab_cameras.prepare_render(scene)
    count=len(bpy.data.materials);material=cube.material_slots[0].material
    lab_cameras.prepare_render(scene)
    assert len(bpy.data.materials)==count and cube.material_slots[0].material==material
    assert cube.data==mesh and vertices==[tuple(v.co) for v in mesh.vertices]
    assert cube.animation_data.action==action
    assert len([o for o in scene.objects if o.type=='LIGHT'])==3
    assert len([o for o in scene.objects if o.type=='CAMERA'])==3
    assert all(o.data.dof.use_dof for o in scene.objects if o.type=='CAMERA')
    replay=bpy.data.scenes.new('Render replay');lab_cameras.copy_to_replay(scene,replay)
    assert all(o.data.dof.focus_object in list(replay.objects) for o in replay.objects if o.type=='CAMERA')
    scene.render.resolution_x=160;scene.render.resolution_y=90;scene.cycles.samples=4
    scene.frame_start=1;scene.frame_end=2
    scene.render.filepath=str(ROOT/'reports'/'render_setup_smoke_')
    bpy.ops.render.render(animation=True)
    assert list((ROOT/'reports').glob('render_setup_smoke_*.mp4'))
    print('RENDER_SETUP_PASSED',flush=True)


if __name__=='__main__':run()
