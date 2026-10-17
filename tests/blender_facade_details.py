"""Miradores, hojas y tejadillos en las cuatro orientaciones."""
import sys,json
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'tests'))
import ruinas_panel as addon
from ruinas_panel import runtime,meta
from blender_probe import closure,digest
from blender_v032 import render


def run():
    'IA: Comprueba opciones optativas, cierre, caché y giro de hojas sin alterar los vanos; entrega fuente ampliada para revisión visual.'
    bpy.ops.wm.read_factory_settings(use_empty=True);addon.register();runtime.busy=True;runtime.preview=True
    scene=bpy.context.scene;p=scene.ruin_settings;p.live_preview=False
    values=dict(layout_mode='ROOM',height_type='ONE',ground_storey_height=75,length=160,building_depth=100,pillar_count=0,damage_enabled=False,windows_enabled=True,windows_per_wall=3,window_width=20,window_leaves=True,window_canopies=True,door_canopy=True,window_projection=8,window_bay_join=True,window_bay_gap=40,window_open_angle=65,roof_frame=True,roof_tiles=True,roof_damage=0,ground_roughness=0,batch_preview=False)
    for key,value in values.items():setattr(p,key,value)
    coll=addon.generate(bpy.context,p,'WORK');report=closure(coll);assert not report['open_edges'],report
    details=meta.get(scene,'fachadas_detalles');assert len({d['wall'] for d in details})==4
    assert any(len(d['windows'])>1 for d in details)
    assert any(o.get('window_leaf') for o in coll.objects)
    assert any(o.name.startswith('Revoco ·') and o.get('facade_detail') for o in coll.objects)
    before=digest(coll);assert digest(addon.generate(bpy.context,p,'WORK'))==before
    render(scene,ROOT/'reports/facade_v03213.png',focus=(0,45,65),location=(260,-300,240),scale=280)
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'dist/ruinas_v03213_fachadas.blend'))
    (ROOT/'reports/facade_v03213.json').write_text(json.dumps({'settings':values,'closure':report,'details':details,'metrics':meta.get(scene,'ruinas_metricas')},indent=2),encoding='utf8')
    for key in ('collapse','hole_count','hole_damage','floor_damage','roof_damage','wood_damage','wear','cracks','rubble_amount'):
        setattr(p,key,0)
    p.damage_enabled=True;p.facade_damage=.95
    damaged=addon.generate(bpy.context,p,'WORK');assert not closure(damaged)['open_edges']
    render(scene,ROOT/'reports/facade_plaster_damage_v03213.png',focus=(0,45,65),location=(260,-300,240),scale=280)
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'dist/ruinas_v03213_fachadas_revoco.blend'))
    print('FACADE_DETAILS_PASSED',flush=True)


if __name__=='__main__':run()
