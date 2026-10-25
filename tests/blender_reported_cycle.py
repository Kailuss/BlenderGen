"""Regresión del laboratorio real: zona localizada, caída larga y exportación vigilada."""
import json
import sys
import time
from pathlib import Path
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import ruinas_panel as addon
from ruinas_panel import runtime
from ruinas_panel.services import physics_jobs,impact_physics,structural_physics,lab_cameras


def calculate(scene,mode,report):
    'IA: Vigila cada etapa con el límite real del panel y conserva progreso, coste y diagnóstico incluso al fallar.'
    started=time.perf_counter();peak=0
    job=physics_jobs.start(scene,mode,str(ROOT/'dist/repro_revoco_ciclo.stl'))
    last=0;status={}
    try:
        while True:
            peak=max(peak,physics_jobs.memory_mb(job['process'].pid))
            status=physics_jobs.poll()
            if 'finished' in status:return status['finished']
            if time.perf_counter()-last>20:
                print('CYCLE_PROGRESS',mode,status,round(peak),flush=True);last=time.perf_counter()
            time.sleep(.5)
    finally:
        report[mode]={'seconds':time.perf_counter()-started,'peak_worker_mb':peak,'diagnostic':str(job['folder']),'last_progress':{k:v for k,v in status.items() if k!='finished'}}
        (ROOT/'reports/reported_cycle.json').write_text(json.dumps(report,indent=2),encoding='utf8')


def run():
    'IA: Simula diez segundos reales con 512 piezas contiguas, luces y órbita sincronizadas; conserva el original, comprueba poses finitas y exporta a 0,5 mm.'
    addon.register();runtime.busy=True
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'dist/repro_revoco_laboratorio_corregido.blend'))
    lab=bpy.context.scene;assert lab.get('structural_physics')
    candidates=[o for o in lab.objects if o.rigid_body and o.rigid_body.type=='ACTIVE' and not o.get('impactor') and o.get('physical_role')!='ground']
    low=Vector(tuple(min(o.location[i] for o in candidates) for i in range(3)))
    high=Vector(tuple(max(o.location[i] for o in candidates) for i in range(3)))
    center=Vector(((low.x+high.x)/2,low.y,low.z+(high.z-low.z)*.7))
    chosen=sorted(candidates,key=lambda o:((o.location-center).length_squared,o.name))[:512]
    p=lab.ruin_settings;p.physics_brick_limit=512;p.physics_memory_mb=4096;p.physics_timeout_seconds=1800
    impact_physics.limit_to_selection(lab,chosen)
    structural_physics.release(lab,chosen,frame=5)
    lab_cameras.ten_seconds(lab)
    assert {o.data.type for o in lab.objects if o.type=='LIGHT' and o.get('lab_light')}=={'SUN','AREA','SPOT'}
    report={'selected':len(chosen),'selection_center_m':list(center),'frames':lab.frame_end,'time_scale':lab.rigidbody_world.time_scale,'memory_limit_mb':4096,'source':bpy.data.filepath}
    print('CYCLE_START',report,flush=True)
    replay=calculate(lab,'SIMULATE',report)
    report['simulation']=json.loads(replay['simulation_report'])
    assert report['simulation']['moving']>0
    bpy.context.window.scene=replay;replay.frame_set(replay.frame_end)
    import math
    assert all(math.isfinite(v) for o in replay.objects for row in o.matrix_world for v in row)
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'dist/repro_revoco_ciclo.blend'))
    replay.ruin_settings.physics_export_voxel=.5
    exported=calculate(replay,'EXPORT',report)
    report['export']=json.loads(exported['physical_export_report']);assert report['export']['closed']
    bpy.context.window.scene=replay;replay.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'dist/repro_revoco_ciclo.blend'))
    (ROOT/'reports/reported_cycle.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print('REPORTED_CYCLE_PASSED',report,flush=True)


if __name__=='__main__':run()
