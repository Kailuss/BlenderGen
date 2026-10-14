"""Regresión física: la escala interna no cambia dimensiones, tiempo ni trayectorias entregadas."""
import sys,json
from pathlib import Path
import bpy
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import ruinas_panel as addon
from ruinas_panel.services import physics,physics_worker


def run():
    'IA: Simula una caída libre y un proyectil cinemático; comprueba poses iniciales, dimensiones originales, trayectoria y suelo tras desescalar.'
    bpy.ops.wm.read_factory_settings(use_empty=True);addon.register()
    scene=bpy.context.scene;scene['ruinas_physics_lab']=True;scene.ruin_settings.live_preview=False
    floor=physics.body(scene,'Suelo',(-100,-100,-5),(100,100,0),False)
    stone=physics.body(scene,'Caída',(-5,-5,80),(5,5,90),True)
    projectile=physics.body(scene,'Trayectoria',(30,-5,20),(40,5,30),True)
    projectile.rigid_body.kinematic=True
    projectile.keyframe_insert(data_path='location',frame=1)
    projectile.location.x+=.02;projectile.keyframe_insert(data_path='location',frame=13)
    scene.frame_end=49;scene.rigidbody_world.point_cache.frame_end=49
    scene.rigidbody_world.time_scale=1;scene.render.fps=24
    scene.ruin_settings.physics_adaptive_collisions=False;scene.ruin_settings.physics_sparse_constraints=False
    scene.frame_set(1);bpy.context.view_layer.update()
    before={o.name:[o.matrix_world@v.co for v in o.data.vertices] for o in (floor,stone,projectile)}
    print('BODIES',[(o.name,o.rigid_body.type,list(o.rigid_body.collision_collections)) for o in (floor,stone,projectile)],flush=True)
    if '--unscaled' in sys.argv:
        from ruinas_panel import config
        config.PHYSICS_SOLVER_SCALE=1
    physics_worker.run(ROOT/'reports/solver_scale.blend',ROOT/'reports/solver_scale_progress.json',scene.name)
    result=next(s for s in bpy.data.scenes if s.get('ruinas_replay'));bpy.context.window.scene=result
    result.frame_set(1);bpy.context.view_layer.update()
    pieces={o.name.rsplit('.',1)[0]:o for o in result.objects}
    for name,points in before.items():
        ob=pieces[name]
        assert max((ob.matrix_world@v.co-p).length for v,p in zip(ob.data.vertices,points))<1e-7,name
    result.frame_set(5);bpy.context.view_layer.update()
    falling=pieces['Caída'].location.z
    print('POSITIONS',[(o.name,list(o.location),list(o.scale)) for o in result.objects],flush=True)
    # Contact with the ground occurs before frame 5; it must not tunnel through it.
    assert .003<falling<.02,falling
    result.frame_set(13);bpy.context.view_layer.update()
    assert abs(pieces['Trayectoria'].location.x-.055)<1e-6
    result.frame_set(49);bpy.context.view_layer.update()
    assert .003<pieces['Caída'].location.z<.007,pieces['Caída'].location.z
    report=json.loads(result['simulation_report']);report['final_height_mm']=pieces['Caída'].location.z*1000
    (ROOT/'reports/solver_scale.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print('SOLVER_SCALE_PASSED',report,flush=True)


if __name__=='__main__':run()
