"""Comprueba que el proceso aislado entrega una escena utilizable y deja la fuente intacta."""
import sys,time,json
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import ruinas_panel as addon
from ruinas_panel import config,runtime,meta
from ruinas_panel.services import masonry_physics,physics_jobs,physics

def run():
    'IA: Prueba worker real, progreso, límites de memoria y reapertura de reproducción sin rigid bodies.'
    bpy.ops.wm.read_factory_settings(use_empty=True);addon.register();source=bpy.context.scene
    source.ruin_settings.live_preview=False;source.ruin_settings.physics_brick_limit=16;source.ruin_settings.physics_frames=24
    lab=masonry_physics.prepare(source);before=len(lab.objects)
    floor=next(o for o in lab.objects if o.get('collision_floor'));floor.scale=(1.2,1.1,1)
    floor['test_scaled_floor']=True
    job=physics_jobs.start(lab)
    for attempt in range(120):
        result=physics_jobs.poll()
        if 'finished' in result:break
        time.sleep(.25)
    else:physics_jobs.cancel();raise AssertionError('Worker timeout')
    replay=result['finished'];assert replay.get('physics_result_scene') and not any(o.rigid_body for o in replay.objects)
    copied=next(o for o in replay.objects if o.get('test_scaled_floor'))
    assert (copied.scale-floor.scale).length<1e-6
    brick=next(o for o in replay.objects if o.get('masonry_brick'))
    original=next(o for o in lab.objects if o.get('masonry_brick'))
    assert len(brick.data.polygons)>len(original.data.polygons),'La reproducción pierde el bisel evaluado'
    assert len(lab.objects)==before
    target=ROOT/'dist/worker_test.stl';replay.frame_set(24);physics_jobs.start(replay,'EXPORT',target)
    for attempt in range(120):
        exported=physics_jobs.poll()
        if 'finished' in exported:break
        time.sleep(.25)
    else:physics_jobs.cancel();raise AssertionError('Export worker timeout')
    assert target.exists() and target.stat().st_size>84
    limit=config.PHYSICS_JOB_MEMORY_MB
    try:
        config.PHYSICS_JOB_MEMORY_MB=-1
        stopped=physics_jobs.start(lab)
        try:physics_jobs.poll()
        except ValueError as exc:assert 'límite de recursos' in str(exc)
        else:raise AssertionError('No se aplica el límite de memoria')
        stopped['process'].wait(timeout=10)
        assert runtime.physics_job is None and (stopped['folder']/'resource_limit.json').exists()
        assert len(lab.objects)==before
    finally:config.PHYSICS_JOB_MEMORY_MB=limit
    del lab['structural_physics'];lab['source_signature']=physics.signature(source.ruin_settings)
    original['source_section']='seccion_prueba';original['initial_matrix']=json.dumps([list(row) for row in original.matrix_world])
    physics_jobs.start(lab)
    for attempt in range(120):
        partition=physics_jobs.poll()
        if 'finished' in partition:break
        time.sleep(.25)
    else:physics_jobs.cancel();raise AssertionError('Partition worker timeout')
    accepted=partition['finished'];bpy.context.window.scene=accepted;accepted.frame_set(24)
    assert physics.accept(accepted)==source
    assert 'seccion_prueba' in meta.get(source,'physics_result')['poses']
    print('PHYSICS_JOBS_PASSED',replay['simulation_report'],flush=True)
if __name__=='__main__':run()
