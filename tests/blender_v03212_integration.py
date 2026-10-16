"""Torre de tres plantas: fuente, preparación aislada, zarandeo y exportación."""
import sys,json,time
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'tests'))
import ruinas_panel as addon
from ruinas_panel import runtime,meta
from ruinas_panel.services import physics_jobs
from blender_probe import closure,digest
from blender_v032 import render


def wait(job):
    'IA: Espera con vigilancia de recursos del trabajador, registra pico residente y conserva el diagnóstico ante cualquier fallo.'
    peak=0;started=time.perf_counter();last=None
    while True:
        peak=max(peak,physics_jobs.memory_mb(job['process'].pid));status=physics_jobs.poll()
        if status.get('stage')!=last:
            last=status.get('stage');print('STAGE',last,round(peak),flush=True)
        if 'finished' in status:return status['finished'],{'peak_mb':peak,'seconds':time.perf_counter()-started}
        time.sleep(.25)


def run():
    'IA: Verifica tres forjados, dos escaleras, balcones independientes y cimientos; simula hasta 2048 cuerpos seleccionados y exporta frame 10, conservando cuatro etapas editables.'
    bpy.ops.wm.read_factory_settings(use_empty=True);addon.register();runtime.busy=True;runtime.preview=True
    source=bpy.context.scene;source.name='01 · Torre editable';p=source.ruin_settings;p.live_preview=False
    settings=dict(length=180,building_depth=120,height_type='THREE',layout_mode='ROOM',pillar_count=0,door_enabled=True,windows_enabled=True,windows_per_wall=2,balconies=True,balconies_per_wall=1,balcony_width=24,balcony_height=42,balcony_depth=20,roof_frame=True,roof_type='TOWER',ground_floor=True,upper_floor=True,floor_beams=True,stair_type='WOOD',damage_enabled=False,foundation_enabled=True,foundation_height=8,patio_enabled=True,patio_margin=20,ground_roughness=0,rubble_amount=0,physics_strength=5,physics_frames=24,batch_preview=True,use_instances=True)
    for key,value in settings.items():setattr(p,key,value)
    coll=addon.generate(bpy.context,p,'WORK');sealed=closure(coll);assert not sealed['open_edges'],sealed
    floors=meta.get(source,'suelos_generados');assert len(floors)==3 and all(f['boards']>0 for f in floors),floors
    stairs=meta.get(source,'escaleras_generadas');assert len(stairs)==3 and all('error' not in s for s in stairs),stairs
    assert stairs[-1]['destination']=='terrace'
    assert abs(stairs[-1]['top']-(p.height+7+p.foundation_height))<.001,(stairs,p.height,p.foundation_height)
    for previous,following in zip(stairs,stairs[1:]):assert abs(previous['top']-following['bottom'])<.001
    assert meta.get(source,'cubierta_detalles')['access_opening']
    openings=meta.get(source,'ventanas_generadas');assert any(o['balcony'] for o in openings) and any(not o['balcony'] for o in openings)
    first=digest(coll);coll=addon.generate(bpy.context,p,'WORK');assert digest(coll)==first
    report={'settings':settings,'source':meta.get(source,'ruinas_metricas'),'floors':floors,'stairs':stairs,'openings':openings,'closure':sealed}
    render(source,ROOT/'reports/v03212_tower_source.png',focus=(0,55,90),location=(320,-350,340),scale=350)
    hidden={o:o.hide_render for o in coll.objects}
    try:
        for ob in coll.objects:
            ob.hide_render=not ('Madera' in ob.name or 'Escalera' in ob.name)
        render(source,ROOT/'reports/v03212_tower_interior.png',focus=(0,70,90),location=(290,350,270),scale=300)
    finally:
        for ob,value in hidden.items():ob.hide_render=value
    lab,report['prepare_job']=wait(physics_jobs.start(source,'PREPARE'));lab.name='02 · Laboratorio torre';bpy.context.window.scene=lab
    report['preparation']=json.loads(lab['preparation_report']);assert len([o for o in lab.objects if o.type=='CAMERA'])==3
    assert 'structural_bounds_mm' in lab,'El zarandeo necesita cotas de muros, no de la valla'
    lab.ruin_settings.physics_brick_limit=2048;lab.ruin_settings.physics_stone_strength=.5;lab.ruin_settings.physics_wood_strength=.3;lab.ruin_settings.physics_floor_strength=.2
    bodies=[o for o in lab.objects if o.rigid_body and o.rigid_body.type=='ACTIVE' and o.get('physical_role')!='ground']
    chosen=sorted(bodies,key=lambda o:(-o.location.z,o.name))[:2048]
    report['eligible']=len(bodies);report['selected']=len(chosen)
    for ob in lab.objects:ob.select_set(ob in chosen)
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'dist/ruinas_v03212_torre_checkpoint.blend'))
    replay,report['shake_job']=wait(physics_jobs.start(lab,'SHAKE',selection=[o.name for o in chosen]));replay.name='03 · Zarandeo calculado'
    report['simulation']=json.loads(replay['simulation_report']);assert report['simulation']['moving']>10
    assert len([o for o in replay.objects if o.type=='CAMERA'])==3
    bpy.context.window.scene=replay;replay.frame_set(10)
    replay.render.engine='BLENDER_WORKBENCH';replay.display.shading.color_type='MATERIAL';replay.display.shading.light='STUDIO';replay.display.shading.show_cavity=True
    replay.render.resolution_x=1200;replay.render.resolution_y=1000;replay.render.resolution_percentage=100;replay.render.filepath=str(ROOT/'reports/v03212_tower_shake.png')
    bpy.ops.render.render(write_still=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'dist/ruinas_v03212_torre_simulada.blend'))
    replay.ruin_settings.physics_export_voxel=.5
    solid,report['export_job']=wait(physics_jobs.start(replay,'EXPORT',ROOT/'dist/ruinas_v03212_torre.stl'));solid.name='04 · Sólido frame 10'
    report['export']=json.loads(solid['physical_export_report'])
    bpy.context.window.scene=source;assert digest(coll)==first
    from ruinas_panel.ui.operators import frame_view
    frame_view(bpy.context)
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'dist/ruinas_v03212_torre_integrada.blend'))
    (ROOT/'reports/v03212_integration.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print('V03212_INTEGRATION_PASSED',report,flush=True)


if __name__=='__main__':run()
