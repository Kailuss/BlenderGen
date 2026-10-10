"""Prefractura sobre revocos y chimenea del generador, con sus encajes reales."""
import json,sys
from pathlib import Path
import bpy,bmesh
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'tests'))
import ruinas_panel as addon
from ruinas_panel import runtime,meta
from ruinas_panel.services import structural_physics
from blender_probe import digest


def run():
    'IA: Prepara una casa real con hastiales y chimenea; exige fragmentos de ambas familias, cierre y fuente conservada.'
    bpy.ops.wm.read_factory_settings(use_empty=True);addon.register();runtime.busy=True;runtime.preview=True
    scene=bpy.context.scene;p=scene.ruin_settings;p.live_preview=False
    for key,value in dict(length=160,building_depth=120,height_type='ONE',layout_mode='ROOM',seed=47,damage_enabled=False,pillar_count=0,door_enabled=False,windows_enabled=False,roof_frame=True,roof_tiles=False,roof_gables=True,chimneys=True,brass_pipes=False,stair_type='NONE',ground_roughness=0,rubble_amount=0).items():setattr(p,key,value)
    coll=addon.generate(bpy.context,p,'WORK');assert meta.get(scene,'chimeneas_generadas'), 'No se generó chimenea'
    before=digest(coll);lab=structural_physics.prepare(scene);assert digest(coll)==before
    fragments=[o for o in lab.objects if o.get('fracture_parent')]
    assert any(o.get('fragile_material')=='plaster' for o in fragments)
    assert any(o.get('fragile_material')=='chimney' for o in fragments)
    ids=[o['physical_piece_id'] for o in fragments];assert len(ids)==len(set(ids)), 'IDs repetidos'
    for ob in fragments:
        bm=bmesh.new();bm.from_mesh(ob.data)
        assert all(e.is_manifold for e in bm.edges) and bm.calc_volume()>0,ob.name
        bm.free()
    report=json.loads(lab['preparation_report']);report['source_unchanged']=True
    (ROOT/'reports/fragile_house.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf8')
    print('FRAGILE_HOUSE_PASSED',len(fragments),flush=True)


if __name__=='__main__':run()
