"""Escenario de carga máxima por opciones constructivas compatibles."""
import sys,time,json,os
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import ruinas_panel as addon
from ruinas_panel import runtime
from ruinas_panel.geometry import instances

def run():
    'IA: Genera dimensiones máximas y todas las familias constructivas compatibles; guarda checkpoint antes de física.'
    bpy.ops.wm.read_factory_settings(use_empty=True);addon.register();runtime.busy=True;runtime.preview=True
    scene=bpy.context.scene;scene.name='CASA MAXIMA 240';p=scene.ruin_settings;p.live_preview=False
    settings=dict(length=240,building_depth=240,height_type='TWO',layout_mode='ROOM',interior_layout='THREE',seed=17,lock_distribution=False,
        roof_frame=True,roof_tiles=True,roof_gables=True,chimneys=True,brass_pipes=True,ground_floor=True,upper_floor=True,floor_beams=True,
        stair_type='STONE',windows_enabled=True,windows_per_wall=3,balconies=True,door_enabled=True,door_leaf=True,door_width=40,
        wood_frame=True,damage_enabled=True,collapse=.12,wood_damage=.15,floor_damage=.1,roof_damage=.1,cracks=.15,wear=.3,hole_count=1,
        rubble_amount=.15,ground_roughness=.3,use_instances=True,batch_preview=True,preview_quality='WORK',export_quality='WORK')
    for k,v in settings.items():setattr(p,k,v)
    print('STRESS_GENERATE_START',os.getpid(),flush=True);started=time.perf_counter()
    coll=addon.generate(bpy.context,p,'WORK')
    report={'settings':settings,'seconds':time.perf_counter()-started,'objects':len(coll.objects),'expanded_faces':instances.expanded_faces(coll)}
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'dist/stress_max_source.blend'))
    (ROOT/'reports/stress_max_generation.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print('STRESS_GENERATION_PASSED',report,flush=True)

if __name__=='__main__':run()
