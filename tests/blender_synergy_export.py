"""Exportación y vistas de la reproducción integrada, conservando la fuente y el laboratorio."""
import sys,json,time
from pathlib import Path
import bpy
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'tests'))
import ruinas_panel as addon
from ruinas_panel.services import physics_jobs
from blender_v032 import render


def run():
    'IA: Exporta el fotograma calculado a 0,5 mm, guarda las cuatro etapas y muestra las maderas sin cubierta para inspección.'
    addon.register();scene=bpy.context.scene
    assert scene.get('physics_result_scene') and not any(o.rigid_body for o in scene.objects)
    scene.frame_set(scene.frame_end);scene.ruin_settings.physics_export_voxel=.5
    target=ROOT/'dist/ruinas_v03211_integrada.stl';job=physics_jobs.start(scene,'EXPORT',target)
    started=time.perf_counter();peak=0
    while True:
        peak=max(peak,physics_jobs.memory_mb(job['process'].pid));status=physics_jobs.poll()
        if 'finished' in status:break
        time.sleep(1)
    result=status['finished'];result.name='04 · Sólido exportado'
    report=json.loads(result['physical_export_report']);report.update(seconds=time.perf_counter()-started,peak_mb=peak)
    (ROOT/'reports/synergy_export.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    render(scene,ROOT/'reports/synergy_final.png',focus=(0,.09,.07),location=(.3,-.32,.3),scale=.36)
    source=bpy.data.scenes['01 · Casa editable'];bpy.context.window.scene=source
    visibility={o:o.hide_render for o in source.objects}
    for ob in source.objects:ob.hide_render=not bool(ob.get('roof_timber'))
    render(source,ROOT/'reports/synergy_timber.png',focus=(0,90,145),location=(200,-200,300),scale=285)
    pieces=[o for o in source.objects if o.get('roof_fracture_parent') and (o.get('timber_broken_start') or o.get('timber_broken_end'))]
    part=max(pieces,key=lambda o:o.get('roof_sag_mm',0));a,b=[Vector(v) for v in part['timber_path']];center=(a+b)/2
    render(source,ROOT/'reports/synergy_splinters.png',focus=center,location=center+Vector((35,-50,45)),scale=65)
    for ob,hidden in visibility.items():ob.hide_render=hidden
    scene.frame_set(1);bpy.context.window.scene=source
    from ruinas_panel.ui.operators import frame_view
    frame_view(bpy.context)
    text=bpy.data.texts.get('LEEME · Prueba integrada') or bpy.data.texts.new('LEEME · Prueba integrada')
    text.clear();text.write((ROOT/'docs/MANUAL_SELECCION_ALTURA.md').read_text(encoding='utf8'))
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'dist/ruinas_v03211_integrada.blend'))
    print('SYNERGY_EXPORT_PASSED',report,flush=True)


if __name__=='__main__':run()
