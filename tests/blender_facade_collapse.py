"""Regresión de fachada de tres plantas y arranque suave del derrumbe."""
import sys,json,time
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'tests'))
import ruinas_panel as addon
from ruinas_panel import runtime,meta
from ruinas_panel.services.cache import clear_cache
from blender_probe import closure
from blender_v032 import render


def run():
    'IA: Reproduce tres plantas con puerta lateral, vanos y cubierta; mide pérdida de tejas a 0.03 y exige cierre en niveles de daño crecientes.'
    addon.register();runtime.busy=True;runtime.preview=True;results=[]
    for collapse in (0,.03,.2,.55,.85):
        clear_cache();bpy.ops.wm.read_factory_settings(use_empty=True)
        scene=bpy.context.scene;p=scene.ruin_settings
        settings=dict(layout_mode='ROOM',height_type='THREE',ground_storey_height=75,upper_storey_height=55,length=160,building_depth=100,pillar_count=0,door_enabled=True,door_width=40,door_height=56,door_position=.81,windows_enabled=True,windows_per_wall=3,window_width=20,window_height=22,balconies=True,balconies_per_wall=1,roof_frame=True,roof_tiles=True,roof_curve=1,window_projection=14.55,window_bay_gap=40,facade_damage=.95,collapse=collapse,roof_damage=0,wood_damage=0,cracks=0,hole_count=0,wear=0,rubble_amount=0,ground_roughness=0,batch_preview=False)
        for key,value in settings.items():setattr(p,key,value)
        started=time.perf_counter();coll=addon.generate(bpy.context,p,'WORK')
        sealed=closure(coll);assert not sealed['open_edges'],(collapse,sealed)
        details=meta.get(scene,'cubierta_detalles');windows=meta.get(scene,'ventanas_generadas')
        results.append({'collapse':collapse,'seconds':time.perf_counter()-started,'roof':details,'windows':windows,'metrics':meta.get(scene,'ruinas_metricas'),'closure':sealed})
        if collapse==0:
            front=[w for w in windows if w['wall']=='front' and not w['balcony']]
            assert {w['floor'] for w in front}=={0,1,2},front
        if collapse==.03:assert details['tiles']>=results[0]['roof']['tiles']*.9,(results[0]['roof'],details)
        render(scene,ROOT/('reports/facade_collapse_%03d.png'%round(collapse*100)),focus=(0,45,115),location=(320,-360,290),scale=390)
        bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/('dist/ruinas_fachada_derrumbe_%03d.blend'%round(collapse*100))))
        print('COLLAPSE_CASE',collapse,details['tiles'],flush=True)
    (ROOT/'reports/facade_collapse.json').write_text(json.dumps(results,indent=2),encoding='utf8')
    print('FACADE_COLLAPSE_PASSED',flush=True)


if __name__=='__main__':run()
