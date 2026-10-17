"""Fachadas y cubierta variable: generación, laboratorio, reproducción y STL."""
import sys,json
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'tests'))
import ruinas_panel as addon
from ruinas_panel import runtime,meta
from ruinas_panel.services import physics_jobs
from blender_probe import closure,digest
from blender_v032 import render
from blender_v03212_integration import wait


def run():
    'IA: Integra hojas, miradores, tejadillos y perfil longitudinal con chimenea/desagües; exige cierre, fuente conservada, cálculo aislado y STL cerrado.'
    bpy.ops.wm.read_factory_settings(use_empty=True);addon.register();runtime.busy=True;runtime.preview=True
    source=bpy.context.scene;source.name='01 · Casa editable';p=source.ruin_settings;p.live_preview=False
    values=dict(layout_mode='ROOM',height_type='ONE',ground_storey_height=75,length=160,building_depth=100,pillar_count=0,damage_enabled=False,door_enabled=True,windows_enabled=True,windows_per_wall=1,window_width=22,window_leaves=True,window_canopies=True,door_canopy=True,window_projection=8,window_bay_join=True,window_bay_gap=40,window_open_angle=60,roof_frame=True,roof_tiles=True,roof_sweep=.8,roof_sweep_bias=.5,roof_asymmetry=.5,chimneys=True,brass_pipes=True,ground_roughness=0,batch_preview=True,physics_export_voxel=.5)
    for key,value in values.items():setattr(p,key,value)
    coll=addon.generate(bpy.context,p,'WORK');sealed=closure(coll);assert not sealed['open_edges'],sealed
    assert meta.get(source,'chimeneas_generadas'),'Caso sin chimenea'
    assert meta.get(source,'bajantes_generadas'),'Caso sin bajantes'
    first=digest(coll);coll=addon.generate(bpy.context,p,'WORK');assert digest(coll)==first
    report={'settings':values,'closure':sealed,'source':meta.get(source,'ruinas_metricas'),'facades':meta.get(source,'fachadas_detalles'),'roof':meta.get(source,'cubierta_detalles')}
    render(source,ROOT/'reports/v03213_source.png',focus=(0,45,65),location=(280,-320,240),scale=300)
    lab,report['prepare_job']=wait(physics_jobs.start(source,'PREPARE'));lab.name='02 · Laboratorio';report['preparation']=json.loads(lab['preparation_report'])
    bpy.context.window.scene=lab;lab.ruin_settings.physics_brick_limit=2048
    chosen=sorted((o for o in lab.objects if o.rigid_body and o.rigid_body.type=='ACTIVE' and o.get('physical_role')!='ground'),key=lambda o:(-o.location.z,o.name))[:512]
    for ob in lab.objects:ob.select_set(ob in chosen)
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'dist/ruinas_v03213_laboratorio.blend'))
    replay,report['shake_job']=wait(physics_jobs.start(lab,'SHAKE',selection=[o.name for o in chosen]));replay.name='03 · Zarandeo calculado'
    report['simulation']=json.loads(replay['simulation_report']);assert report['simulation']['moving']>10
    bpy.context.window.scene=replay;replay.frame_set(10)
    solid,report['export_job']=wait(physics_jobs.start(replay,'EXPORT',export_path=str(ROOT/'dist/ruinas_v03213_prueba.stl')))
    solid.name='04 · Sólido frame 10';report['export']=json.loads(solid['physical_export_report']);assert report['export']['closed']
    assert digest(coll)==first
    bpy.context.window.scene=source
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'dist/ruinas_v03213_integrada.blend'))
    (ROOT/'reports/v03213_integration.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print('V03213_INTEGRATION_PASSED',flush=True)


if __name__=='__main__':run()
