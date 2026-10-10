"""Carga máxima: todos los cuerpos arquitectónicos activos con colisión optimizada."""
import sys,time,json
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import ruinas_panel as addon
from ruinas_panel.services import structural_physics,physics_jobs,impact_physics

def run():
    'IA: Ensaya la casa máxima completa, vigila el hijo y guarda reproducción junto con laboratorio y casa originales.'
    addon.register();lab=bpy.context.scene
    merged=structural_physics.merge_ground(lab)
    print('STRESS_GROUND_MERGED',merged,flush=True)
    stats=structural_physics.optimise_collisions(lab) if '--reuse' not in sys.argv else json.loads(lab.get('collision_optimisation','{}'));stats['ground_merged']=merged
    print('STRESS_COLLISIONS',stats,flush=True)
    if '--active-cap' in sys.argv:
        cap=int(sys.argv[sys.argv.index('--active-cap')+1])
        candidates=sorted([o for o in lab.objects if o.rigid_body and o.rigid_body.type=='ACTIVE'],key=lambda o:o.location.y)
        for ob in candidates[cap:]:ob.rigid_body.type='PASSIVE'
        unused=[o for o in lab.objects if o.rigid_body_constraint and o.rigid_body_constraint.object1.rigid_body.type=='PASSIVE' and o.rigid_body_constraint.object2.rigid_body.type=='PASSIVE']
        bpy.data.batch_remove(ids=tuple(unused))
        stats['active_cap']=cap
        print('STRESS_ACTIVE_CAP',cap,flush=True)
    stats['constraints']=structural_physics.sparsify_constraints(lab)
    if '--diagnostic-hulls' in sys.argv:
        for ob in lab.objects:
            if ob.rigid_body and ob.rigid_body.type=='ACTIVE':ob.rigid_body.collision_shape='CONVEX_HULL'
        stats['diagnostic_all_hulls']=True
    lab.rigidbody_world.substeps_per_frame=12;lab.rigidbody_world.solver_iterations=30
    lab.ruin_settings.impact_speed=600;lab.ruin_settings.impact_radius=20;lab.ruin_settings.impact_direction=(0,1,0)
    stones=[o for o in lab.objects if o.get('physical_role')=='stone' and o.rigid_body.type=='ACTIVE']
    chosen=sorted(stones,key=lambda o:(o.location.x-.12)**2+o.location.y**2+(o.location.z-.045)**2)[:12]
    if not any(o.get('impactor') for o in lab.objects):impact_physics.launch(lab,chosen)
    lab.frame_end=96
    lab.rigidbody_world.point_cache.frame_end=96
    stats['active']=sum(bool(o.rigid_body and o.rigid_body.type=='ACTIVE') for o in lab.objects);stats['total']=sum(o.rigid_body is not None for o in lab.objects)
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'dist/stress_max_optimised.blend'))
    print('STRESS_SIMULATION_START',stats,flush=True)
    job=physics_jobs.start(lab);started=time.perf_counter();peak=0;last=None
    while True:
        peak=max(peak,physics_jobs.memory_mb(job['process'].pid));status=physics_jobs.poll()
        if 'finished' in status:break
        if status.get('frame',0)//12!=last:
            last=status.get('frame',0)//12;print('STRESS_PROGRESS',status,'MB',round(peak),flush=True)
        time.sleep(1)
    result=status['finished'];bpy.context.window.scene=result
    stats.update(json.loads(result['simulation_report']));stats['peak_worker_mb']=peak;stats['total_seconds']=time.perf_counter()-started
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'dist/ruinas_v0328_maxima.blend'))
    (ROOT/'reports/stress_max_simulation.json').write_text(json.dumps(stats,indent=2),encoding='utf8')
    print('STRESS_SIMULATION_PASSED',stats,flush=True)
if __name__=='__main__':run()

