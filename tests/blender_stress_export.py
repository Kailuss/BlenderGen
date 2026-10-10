"""Exportación aislada del último fotograma de la casa máxima calculada."""
import json,sys,time
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import ruinas_panel as addon
from ruinas_panel.services import physics_jobs


def run():
    'IA: Exporta únicamente una reproducción calculada, conserva las escenas editables y guarda informe del proceso aislado.'
    addon.register();scene=bpy.context.scene
    assert scene.get('physics_result_scene') and not any(o.rigid_body for o in scene.objects)
    scene.frame_set(scene.frame_end)
    if '--voxel' in sys.argv:scene.ruin_settings.physics_export_voxel=float(sys.argv[sys.argv.index('--voxel')+1])
    target=ROOT/'dist/ruinas_v0328_maxima.stl'
    job=physics_jobs.start(scene,'EXPORT',target);peak=0;started=time.perf_counter()
    while True:
        peak=max(peak,physics_jobs.memory_mb(job['process'].pid));status=physics_jobs.poll()
        if 'finished' in status:break
        time.sleep(1)
    result=status['finished'];report=json.loads(result['physical_export_report'])
    report.update(peak_worker_mb=peak,seconds=time.perf_counter()-started)
    (ROOT/'reports/stress_max_export.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    scene.frame_set(1);bpy.context.window.scene=scene
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'dist/ruinas_v0328_maxima.blend'))
    print('STRESS_EXPORT_PASSED',report,flush=True)


if __name__=='__main__':run()
