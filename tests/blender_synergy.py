"""Casa integrada económica: accesorios reales y madera fracturada antes del laboratorio."""
import sys,json,time
from pathlib import Path
import bpy,bmesh
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'tests'))
import ruinas_panel as addon
from ruinas_panel import runtime,meta
from blender_probe import closure
from blender_v032 import render


def run():
    'IA: Genera un caso con accesorios presentes, verifica cierre y extremos astillados y guarda la fuente editable antes de simular.'
    bpy.ops.wm.read_factory_settings(use_empty=True);addon.register();runtime.busy=True;runtime.preview=True
    scene=bpy.context.scene;scene.name='01 · Casa editable';p=scene.ruin_settings;p.live_preview=False
    settings=dict(length=220,building_depth=190,height_type='TWO',layout_mode='ROOM',seed=47,lock_distribution=False,
        interior_layout='THREE',pillar_count=2,pillar_distribution='EVEN',door_enabled=True,door_width=35,door_height=48,
        windows_enabled=True,balconies=True,roof_frame=True,roof_tiles=True,roof_gables=True,chimneys=True,brass_pipes=True,
        ground_floor=True,upper_floor=True,floor_beams=True,stair_type='STONE',damage_enabled=True,
        collapse=0,hole_count=0,cracks=0,rubble_amount=.15,ground_roughness=.15,wear_level='CUSTOM',wear=.12,
        wood_grain=.35,wood_damage=.45,roof_damage=.35,floor_damage=.1,batch_preview=False)
    for key,value in settings.items():setattr(p,key,value)
    started=time.perf_counter();coll=addon.generate(bpy.context,p,'WORK')
    report={'settings':settings,'seconds':time.perf_counter()-started,'closure':closure(coll)}
    assert not report['closure']['open_edges'],report['closure']
    assert not report['closure']['degenerate_faces'],report['closure']
    for key in ('chimeneas_generadas','bajantes_generadas','ventanas_generadas','plano_interior','cubierta_detalles'):
        report[key]=meta.get(scene,key);assert report[key],key
    assert any(w.get('balcony') for w in report['ventanas_generadas'])
    fragments=[o for o in coll.objects if o.get('roof_fracture_parent')]
    assert fragments,'No hay madera fracturada'
    assert any(o.get('timber_broken_start') or o.get('timber_broken_end') for o in fragments)
    for ob in fragments:
        assert len(ob['timber_path'])==2,ob.name
        bm=bmesh.new();bm.from_mesh(ob.data)
        assert all(e.is_manifold for e in bm.edges) and bm.calc_volume()>0,ob.name
        bm.free()
    report['timber_fragments']=len(fragments)
    report['piece_flags']={key:sum(bool(o.get(key)) for o in coll.objects) for key in ('interior_partition','pipe_section','chimney','roof_tiles','stair')}
    report['balconies']=sum(bool(w.get('balcony')) for w in report['ventanas_generadas'])
    (ROOT/'reports/synergy_source.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    render(scene,ROOT/'reports/synergy_source.png',focus=(0,90,70),location=(300,-320,300),scale=360)
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'dist/ruinas_v03211_fuente.blend'))
    print('SYNERGY_SOURCE_PASSED',report,flush=True)


if __name__=='__main__':run()
