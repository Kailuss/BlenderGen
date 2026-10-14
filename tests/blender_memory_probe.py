"""Diagnóstico acotado del arranque de Bullet: mismo laboratorio, una variable por ensayo."""
import sys,json,time
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import ruinas_panel as addon
from ruinas_panel.services import physics_jobs


def run():
    'IA: Compara solo dos fotogramas con un límite de 4 GB; registra cuerpos, triángulos y memoria, sin escribir sobre la casa ni el laboratorio original.'
    addon.register();scene=next(s for s in bpy.data.scenes if s.get('ruinas_physics_lab'));bpy.context.window.scene=scene
    variant=sys.argv[sys.argv.index('--')+1];scene.frame_end=2;scene.rigidbody_world.point_cache.frame_end=2
    p=scene.ruin_settings;p.physics_memory_mb=4096;p.physics_timeout_seconds=180
    bodies=[o for o in scene.objects if o.rigid_body]
    if variant=='NO_JOINTS':bpy.data.batch_remove(ids=tuple(o for o in scene.objects if o.rigid_body_constraint))
    elif variant=='HULLS':
        for ob in bodies:
            if ob.rigid_body.type=='ACTIVE':ob.rigid_body.collision_shape='CONVEX_HULL'
    elif variant=='NO_CONTACTS':
        for ob in bodies:ob.rigid_body.collision_collections=[False]*20
    elif variant=='SCALED':
        for ob in bodies:
            ob.location*=100;ob.scale*=100;ob.rigid_body.collision_margin*=100
        for ob in scene.objects:
            if ob.rigid_body_constraint:ob.location*=100;ob.rigid_body_constraint.breaking_threshold*=100
        for action in {o.animation_data.action for o in bodies if o.animation_data and o.animation_data.action}:
            for layer in action.layers:
                for strip in layer.strips:
                    for bag in strip.channelbags:
                        for curve in bag.fcurves:
                            if curve.data_path=='location':
                                for key in curve.keyframe_points:
                                    key.co.y*=100;key.handle_left.y*=100;key.handle_right.y*=100
        scene.gravity*=100
    report={'variant':variant,'bodies':len(bodies),'active':sum(o.rigid_body.type=='ACTIVE' for o in bodies),'constraints':sum(o.rigid_body_constraint is not None for o in scene.objects),'roles':{role:sum(o.get('physical_role')==role for o in bodies) for role in ('wood','stone','tile','metal','ground')}}
    job=physics_jobs.start(scene);peak=0;started=time.perf_counter()
    try:
        while True:
            peak=max(peak,physics_jobs.memory_mb(job['process'].pid));state=physics_jobs.poll()
            if 'finished' in state:report['completed']=True;break
            report['last_stage']=state;time.sleep(.25)
    except ValueError as error:report['error']=str(error)
    report.update(peak_mb=peak,seconds=time.perf_counter()-started)
    (ROOT/('reports/memory_probe_'+variant.lower()+'.json')).write_text(json.dumps(report,indent=2),encoding='utf8')
    print('MEMORY_PROBE',report,flush=True)


if __name__=='__main__':run()
