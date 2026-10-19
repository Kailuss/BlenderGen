"""Regresión combinada de escaleras, valla, balcones y torreón."""
import sys,json,time
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'tests'))
import ruinas_panel as addon
from ruinas_panel import runtime,meta
from ruinas_panel.structure import stairs
from ruinas_panel.services import structural_physics
from ruinas_panel.services.cache import clear_cache
from blender_probe import closure
from blender_v032 import render


def run():
    'IA: Comprueba escalones crecientes, cierre y preparación de las dos escaleras junto a valla y balcón; compara torreón intacto y dañado y guarda ejemplos.'
    addon.register();runtime.busy=True;runtime.preview=True;results=[]
    for kind,damage in (('WOOD',0),('STONE',0),('WOOD',.55)):
        clear_cache();bpy.ops.wm.read_factory_settings(use_empty=True);scene=bpy.context.scene;p=scene.ruin_settings
        for key,value in dict(layout_mode='ROOM',height_type='TWO',ground_storey_height=75,upper_storey_height=55,length=190,building_depth=85,pillar_count=0,stair_type=kind,roof_type='TOWER',roof_frame=True,patio_enabled=True,patio_fence=True,balconies=True,balconies_per_wall=1,windows_per_wall=1,window_projection=0,window_bay_join=False,balcony_open_angle=45,collapse=damage,roof_damage=0,hole_count=0,cracks=0,wear=0,rubble_amount=0,ground_roughness=0,wood_damage=0,batch_preview=False).items():setattr(p,key,value)
        p.windows_enabled=True;p.door_enabled=True;p.windows_per_wall=2
        p.ground_storey_height=45;low=stairs.plan(p,(-90,90,0,80));p.ground_storey_height=75;high=stairs.plan(p,(-90,90,0,80))
        assert high['steps']>low['steps'],(low,high)
        started=time.perf_counter();coll=addon.generate(bpy.context,p,'WORK');sealed=closure(coll)
        assert not sealed['open_edges'],sealed
        info={'kind':kind,'damage':damage,'stairs':meta.get(scene,'escaleras_generadas'),'roof':meta.get(scene,'cubierta_detalles'),'closure':sealed,'windows':meta.get(scene,'ventanas_generadas'),'low_steps':low['steps'],'high_steps':high['steps']}
        if damage==0:
            windows=info['windows'];front=[h for h in windows if h['wall']=='front']
            lower=next(h for h in front if h['floor']==0 and not h['balcony'])
            balcony=next(h for h in front if h['balcony'])
            assert abs(lower['x']-balcony['x'])<.01,(lower,balcony)
            for h in windows:
                if not h['balcony'] and h['floor']==1:assert h['z0']>balcony['z0']+5
        render(scene,ROOT/('reports/v03216_%s_%s.png'%(kind,int(damage*100))),focus=(0,35,75),location=(280,-320,260),scale=350)
        if damage==0:
            assert any(o.get('balcony_leaf') for o in coll.objects),'Falta cancela'
            lab=structural_physics.prepare(scene);info['preparation']=json.loads(lab['preparation_report']);bpy.context.window.scene=scene
        else:assert info['roof']['parapet_blocks']<results[0]['roof']['parapet_blocks']
        info['seconds']=time.perf_counter()-started;results.append(info)
        bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/('dist/ruinas_v03216_%s_%s.blend'%(kind,int(damage*100)))))
        (ROOT/'reports/v03216.json').write_text(json.dumps(results,indent=2),encoding='utf8')
        print('CASE_PASSED',kind,damage,flush=True)
    print('V03216_PASSED',flush=True)


if __name__=='__main__':run()
