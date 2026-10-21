"""Reabre y renderiza el laboratorio obtenido del archivo del usuario."""
import sys,json
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import ruinas_panel as addon
from ruinas_panel import runtime


def run():
    'IA: Reabre la entrega real, comprueba cámaras, luces y restricciones y renderiza el fotograma inicial; no afirma validar un derrumbe completo.'
    addon.register();runtime.busy=True
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'dist/repro_revoco_laboratorio_corregido.blend'))
    scene=bpy.context.scene
    assert scene.get('structural_physics')
    cameras=[o for o in scene.objects if o.type=='CAMERA']
    lights=[o for o in scene.objects if o.type=='LIGHT']
    assert len(cameras)==3 and {o.data.type for o in lights}=={'SUN','AREA','SPOT'}
    assert all(o.constraints and o.constraints[0].target in list(scene.objects) for o in cameras)
    report=json.loads(scene['preparation_report'])
    assert not report['unconnected']
    report['lights']=[{'name':o.name,'type':o.data.type,'energy':o.data.energy} for o in lights]
    report['cameras']=[o.name for o in cameras]
    report['materials_without_nodes']=sorted({slot.material.name for o in scene.objects if o.type=='MESH' for slot in o.material_slots if slot.material and not slot.material.use_nodes})
    scene.frame_set(1);scene.cycles.samples=24;scene.render.resolution_percentage=60
    scene.render.filepath=str(ROOT/'reports/reported_lab_render.png');bpy.ops.render.render(write_still=True)
    (ROOT/'reports/reported_lab_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print('REPORTED_LAB_VERIFIED',flush=True)


if __name__=='__main__':run()
