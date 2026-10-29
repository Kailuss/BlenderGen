"""Segundo ejercicio: fuente intacta máxima y preparación aislada reproducible."""
import sys, json, time
from pathlib import Path
import bpy
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'tools'), str(ROOT / 'tests')]
import ruinas_panel as addon
from ruinas_panel import runtime, meta
from build_meteor_tower import wait_job
from blender_v032 import render
OUT = ROOT / 'dist/Ejercicio02_metralla_20261028'


def run():
    """IA: Genera al máximo de dimensiones admitidas, mide la fuente prístina y prepara copias físicas sin tocar la entrega anterior."""
    OUT.mkdir(exist_ok=True)
    addon.register()
    runtime.busy = runtime.preview = True
    scene = bpy.context.scene
    scene.name = '01 · Casa prístina editable'
    p = scene.ruin_settings
    p.live_preview = False
    values = dict(length=240, building_depth=240, height_type='THREE',
        ground_storey_height=125, upper_storey_height=125, layout_mode='ROOM',
        build_type='FORTRESS', pillar_count=0, interior_layout='TWO',
        door_enabled=True, door_width=40, door_height=62, door_leaf=True,
        door_canopy=True, windows_enabled=True, windows_per_wall=3,
        window_width=28, window_height=38, window_projection=10,
        window_canopies=True, window_leaves=True, window_open_angle=65,
        balconies=True, balconies_per_wall=2, balcony_width=32,
        balcony_height=60, balcony_depth=24, balcony_gate=True,
        balcony_open_angle=25, balcony_canopy=True,
        roof_frame=True, roof_type='PITCHED', roof_tiles=True,
        roof_gables=True, roof_curve=.65, roof_sweep=.55,
        roof_sweep_bias=.25, roof_asymmetry=.18, chimneys=True, brass_pipes=True,
        foundation_enabled=True, foundation_height=16, entrance_tread=12,
        patio_enabled=True, patio_margin=35, patio_fence=True, fence_height=18,
        ground_floor=True, upper_floor=True, floor_beams=True,
        stair_type='WOOD', stair_tread=8, stair_riser=8,
        collapse=0, roof_damage=0, hole_count=0, cracks=0,
        rubble_amount=0, ground_roughness=0, floor_damage=0,
        wood_damage=0, facade_damage=0, damage_enabled=False,
        batch_preview=False, microdetail_preview=False, seed=103,
        physics_strength=180, physics_fragile_size=40, physics_frames=241,
        physics_memory_mb=10240, physics_timeout_seconds=7200,
        physics_precision='HIGH', physics_sparse_constraints=False)
    for key, value in values.items():
        setattr(p, key, value)
    started = time.monotonic()
    coll = addon.generate(bpy.context, p, 'WORK')
    report = dict(parameters=values, generation_seconds=time.monotonic()-started,
        objects=len(coll.objects), faces=sum(len(o.data.polygons) for o in coll.objects if o.type=='MESH'),
        stairs=meta.get(scene, 'escaleras_generadas', []),
        windows=meta.get(scene, 'ventanas_generadas', []),
        effective_profile={k:getattr(p,k) for k in ('stone_size','thickness','height')},
        hardware_target=dict(ram_gb=32, gpu='RTX 3090 Ti', vram_gb=24))
    if any('error' in step for step in report['stairs']):
        raise ValueError('Escalera inválida: '+str(report['stairs']))
    scene.render.fps=24
    scene.frame_start=1
    scene.frame_end=241
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'01_fuente_pristina.blend'))
    (OUT/'generacion.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print('SOURCE_READY', json.dumps(report), flush=True)
    render(scene, ROOT/'reports/ejercicio02_pristino.png',focus=(0,120,230),location=(600,-700,600),scale=850)
    scene.camera.data.clip_end=10000
    bpy.ops.render.render(write_still=True)
    if '--prepare' in sys.argv:
        lab, peak=wait_job(scene,'PREPARE')
        bpy.context.window.scene=lab
        lab.name='02 · Laboratorio tres impactos'
        report['preparation']=json.loads(lab['preparation_report'])
        report['prepare_peak_mb']=peak
        bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'02_laboratorio_base.blend'))
        (OUT/'generacion.json').write_text(json.dumps(report,indent=2),encoding='utf8')
        print('LAB_READY',json.dumps(report['preparation']),flush=True)


if __name__ == '__main__':
    run()
