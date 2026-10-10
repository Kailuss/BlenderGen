"""Regresión de reparto, cotas y cancelas en perfiles bajos."""
import sys,json
from pathlib import Path
import bpy
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'tests'))
import ruinas_panel as addon
from ruinas_panel import runtime,meta
from ruinas_panel.structure import layout
from blender_probe import closure,digest
from blender_v032 import render


def run():
    'IA: Comprueba ventanas distribuidas, cotas de escalera/forjado, caché y cancelas sin dintel ni altura aplastada; guarda vistas reproducibles.'
    bpy.ops.wm.read_factory_settings(use_empty=True);addon.register();runtime.busy=True;runtime.preview=True
    scene=bpy.context.scene;p=scene.ruin_settings;p.live_preview=False
    for key,value in dict(length=220,building_depth=180,height_type='TWO',layout_mode='ROOM',interior_layout='TWO',ground_storey_height=65,upper_storey_height=42,windows_enabled=True,windows_per_wall=3,balconies=True,pillar_count=0,damage_enabled=False,door_enabled=True,ground_floor=True,upper_floor=True,floor_beams=True,stair_type='STONE',roof_frame=True,roof_tiles=True,roof_gables=True,use_instances=True,batch_preview=False,ground_roughness=0,rubble_amount=0).items():setattr(p,key,value)
    coll=addon.generate(bpy.context,p,'WORK');windows=meta.get(scene,'ventanas_generadas')
    front=sorted(h['x'] for h in windows if h['wall']=='front')
    assert len(front)==3 and front[-1]-front[0]>80,front
    assert p.height==109 and layout.upper_floor(p)==67
    stair=meta.get(scene,'escalera_generada');assert stair['top']==67,stair
    beams=meta.get(scene,'vigas_generadas');assert beams and all(abs(b['z']-63.4)<1e-5 for b in beams)
    partitions=[o for o in coll.objects if o.get('partition_member')=='plank']
    assert partitions and abs(max(v.co.z for o in partitions for v in o.data.vertices)-65.2)<.01
    headers=[o for o in coll.objects if o.name.startswith('Madera · cabecero escalera')]
    assert headers and all(abs((min(v.co.z for v in o.data.vertices)+max(v.co.z for v in o.data.vertices))/2-63.4)<.3 for o in headers)
    assert not closure(coll)['open_edges']
    first=digest(coll);assert digest(addon.generate(bpy.context,p,'WORK'))==first
    render(scene,ROOT/'reports/constructibility_house.png',focus=(0,85,58),location=(300,-320,280),scale=390)
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'dist/ruinas_v0329_construccion.blend'))
    report={'front_windows':front,'height_mm':p.height,'upper_floor_mm':stair['top'],'gates':[]}
    for style in ('WOOD_GATE','IRON_GATE'):
        p.layout_mode='NONE';p.build_type='PARTITION';p.height_type='RUIN';p.low_wall_height=27;p.door_height=40;p.door_style=style;p.pillar_count=0;p.windows_enabled=False;p.roof_frame=False
        coll=addon.generate(bpy.context,p,'WORK');door=meta.get(scene,'puerta_generada')
        assert door['top']==40 and door['gate'] and not any('dintel' in o.name.lower() for o in coll.objects)
        assert not closure(coll)['open_edges']
        report['gates'].append({'style':style,'height_mm':door['top']})
        render(scene,ROOT/('reports/constructibility_'+style.lower()+'.png'),focus=(0,0,22),location=(95,-240,100),scale=245)
    p.build_type='WALL';p.height_type='ONE';p.length=200;p.door_enabled=False;p.pillar_count=3;p.pillar_distribution='CUSTOM';p.pillar_positions='20;50;80'
    coll=addon.generate(bpy.context,p,'WORK')
    positions=meta.get(scene,'pilares_generados');assert len(positions)==3,positions
    assert all(abs(actual['x_mm']-expected)<1e-4 for actual,expected in zip(positions,(-60,0,60))),positions
    preserved=digest(coll);p.pillar_positions='50;50;50'
    try:addon.generate(bpy.context,p,'WORK')
    except ValueError:pass
    else:raise AssertionError('Se permitieron pilares solapados')
    assert digest(coll)==preserved,'La validación destruyó la fuente'
    report['manual_pillars_mm']=[item['x_mm'] for item in positions];report['invalid_preserves_source']=True
    (ROOT/'reports/constructibility.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print('CONSTRUCTIBILITY_PASSED',report,flush=True)


if __name__=='__main__':run()
