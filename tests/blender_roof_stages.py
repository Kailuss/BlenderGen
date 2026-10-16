"""Daño progresivo de cubierta y geometría triangulada preparada para física."""
import sys,json
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'tests'))
import ruinas_panel as addon
from ruinas_panel import runtime,meta
from ruinas_panel.services import structural_physics
from ruinas_panel.geometry import primitives
from blender_v032 import render
from blender_probe import digest,closure


def run():
    'IA: Etapa inicial conserva tejas y hunde maderas; la avanzada pierde piezas; ambas mantienen cierre, caché y triangulación válida.'
    bpy.ops.wm.read_factory_settings(use_empty=True);addon.register();runtime.busy=True;runtime.preview=True
    scene=bpy.context.scene;p=scene.ruin_settings;p.live_preview=False
    values=dict(length=160,building_depth=120,height_type='ONE',layout_mode='ROOM',pillar_count=0,door_enabled=False,windows_enabled=False,roof_frame=True,roof_tiles=True,roof_gables=False,chimneys=False,ground_floor=False,stair_type='NONE',collapse=0,hole_count=0,cracks=0,rubble_amount=0,ground_roughness=0,batch_preview=True)
    for k,v in values.items():setattr(p,k,v)
    reports=[]
    for damage in (0,.35,.85):
        p.roof_damage=damage;coll=addon.generate(bpy.context,p,'WORK');record=meta.get(scene,'cubierta_detalles');record['damage']=damage
        assert not closure(coll)['open_edges']
        first=digest(coll);coll=addon.generate(bpy.context,p,'WORK');assert digest(coll)==first
        copies=bpy.data.collections.new('Auditoría física');scene.collection.children.link(copies)
        objects=structural_physics.snapshot(coll,copies,{'binder_excluded':0})
        if damage:
            assert max(o.get('roof_sag_mm',0) for o in objects)>1
            assert any(o.get('roof_fracture_parent') and 'roof_member_segment' in o for o in objects)
        primitives.remove_objects(objects);bpy.data.collections.remove(copies)
        render(scene,ROOT/('reports/roof_stage_%s.png'%round(damage*100)),focus=(0,55,65),location=(220,-260,260),scale=285)
        reports.append(record)
    assert reports[0]['tiles']==reports[1]['tiles'] and reports[1]['missing_tiles']==0
    assert reports[1]['sag_mm']>1 and reports[1]['deformed_timbers']>0
    assert reports[2]['tiles']<reports[1]['tiles'] and reports[2]['missing_tiles']>0
    assert reports[2]['sag_mm']>reports[1]['sag_mm']
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'dist/ruinas_v03212_tejado.blend'))
    (ROOT/'reports/roof_stages.json').write_text(json.dumps(reports,indent=2),encoding='utf8')
    print('ROOF_STAGES_PASSED',[(r['damage'],r['tiles'],r['sag_mm']) for r in reports],flush=True)


if __name__=='__main__':run()
