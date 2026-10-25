"""Verifica gravedad real y contactos conservados por la reproducción aislada."""
import json
import sys
import time
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import ruinas_panel as addon
from ruinas_panel import runtime
from ruinas_panel.services import physics_jobs


def run():
    'IA: Una caja cae sobre suelo a escala métrica; comprueba gravedad sin cámara lenta, cada fotograma grabado y ausencia de penetración durante 48 fotogramas.'
    addon.register();runtime.busy=True
    scene=bpy.context.scene
    for ob in list(scene.objects):bpy.data.objects.remove(ob,do_unlink=True)
    for name,location,scale,kind in (('Suelo',(0,0,-.01),(1,1,.01),'PASSIVE'),('Caja',(0,0,1),(.1,.1,.1),'ACTIVE')):
        bpy.ops.mesh.primitive_cube_add(size=2,location=location);ob=bpy.context.object;ob.name=name;ob.scale=scale
        bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
        bpy.ops.rigidbody.object_add();ob.rigid_body.type=kind;ob.rigid_body.collision_shape='BOX';ob.rigid_body.use_margin=True;ob.rigid_body.collision_margin=0
        if kind=='PASSIVE':ob['collision_floor']=True
    for index in range(8):
        bpy.ops.mesh.primitive_cube_add(size=2,location=(.2+index*.03,0,.15+index*.02))
        ob=bpy.context.object;ob.name='Fragmento fino %s'%index;ob.scale=(.001,.0001,.0001)
        bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
        bpy.ops.rigidbody.object_add();ob.rigid_body.collision_shape='MESH';ob.rigid_body.use_margin=True;ob.rigid_body.collision_margin=0
    scene['ruinas_physics_lab']=True;scene.frame_end=48;scene.render.fps=24
    world=scene.rigidbody_world;world.time_scale=1;world.point_cache.frame_end=48
    scene.ruin_settings.physics_precision='BALANCED'
    job=physics_jobs.start(scene)
    while True:
        state=physics_jobs.poll()
        if 'finished' in state:break
        time.sleep(.25)
    replay=state['finished'];bpy.context.window.scene=replay
    box=next(o for o in replay.objects if o.get('replay_source_object')=='Caja')
    report=json.loads(replay['simulation_report']);assert report['sample_step']==1 and report['time_scale']==1
    curves=[c for layer in box.animation_data.action.layers for strip in layer.strips for bag in strip.channelbags for c in bag.fcurves if c.data_path=='location']
    assert all(len(c.keyframe_points)==48 for c in curves)
    heights=[]
    for frame in range(1,49):
        replay.frame_set(frame);heights.append(box.matrix_world.translation.z)
    assert .65<heights[6]<.80,heights[6]
    assert min(heights)>.095 and abs(heights[-1]-.1)<.005,heights
    assert all(o.matrix_world.translation.z>=-.001 for o in replay.objects if o.get('replay_source_object','').startswith('Fragmento fino'))
    bpy.context.window.scene=scene;scene.frame_set(1)
    scene.objects['Caja'].location.x=20
    physics_jobs.start(scene)
    try:
        while True:
            state=physics_jobs.poll()
            if 'finished' in state:raise AssertionError('Una caja fuera del suelo no debe entregar una reproducción válida')
            time.sleep(.25)
    except ValueError as error:assert 'Fuga bajo el suelo' in str(error),error
    assert runtime.physics_job is None
    print('REPLAY_CONTACTS_PASSED',report,flush=True)


if __name__=='__main__':run()
