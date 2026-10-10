"""Reabre la entrega y exporta las poses físicas sin depender del proceso temporal."""
import json,sys
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import ruinas_panel as addon
from ruinas_panel.services import physical_export


def run():
    'IA: Exige datos locales y animación persistente al reabrir; valida el sólido exportado y guarda informe reproducible.'
    addon.register()
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'dist/ruinas_v0329_fragmentos.blend'))
    for collection in (bpy.data.objects,bpy.data.meshes,bpy.data.materials,bpy.data.actions):
        assert all(item.library is None for item in collection),'La entrega depende de una biblioteca externa'
    scene=bpy.data.scenes['00 REPRODUCCION FRAGIL'];bpy.context.window.scene=scene
    assert not scene.rigidbody_world,'La reproducción no debe recalcular Bullet'
    scene.frame_set(1);pieces=[o for o in scene.objects if o.get('fracture_parent')]
    positions={o:o.matrix_world.translation.copy() for o in pieces}
    scene.frame_set(72);assert sum((o.matrix_world.translation-v).length>.002 for o,v in positions.items())>=20
    result=physical_export.export(scene,ROOT/'dist/ruinas_v0329_fragmentos.stl',.35)
    report=json.loads(result['physical_export_report']);report['reopened_self_contained']=True
    (ROOT/'reports/fragile_delivery.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print('FRAGILE_DELIVERY_PASSED',report,flush=True)


if __name__=='__main__':run()
