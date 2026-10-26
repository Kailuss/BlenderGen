"""Cámaras manuales, lámpara, bruma y horneado real de polvo reducido."""
import sys,json
from pathlib import Path
import bpy
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import ruinas_panel as addon
from ruinas_panel import runtime
from ruinas_panel.services import lab_cameras,lab_chandelier,lab_atmosphere,physics_worker
from ruinas_panel.structure import layout


def run():
    'IA: Comprueba idempotencia, rutas, copia de decoración, exclusión del escalado y seis fotogramas Mantaflow; renderiza la lámpara.'
    addon.register();runtime.busy=True
    scene=bpy.context.scene
    for ob in list(scene.objects):bpy.data.objects.remove(ob,do_unlink=True)
    scene['ruinas_physics_lab']=True;scene.frame_end=241
    roof=lab_atmosphere.box(scene,'Techo de ensayo',(-.04,-.04,.08),(.04,.04,.085));del roof['lab_decor'];roof['physical_role']='wood'
    roof.data.materials.append(lab_chandelier.material('Techo de ensayo',(.12,.065,.025)))
    legacy_target=bpy.data.objects.new('Objetivo antiguo',None);scene.collection.objects.link(legacy_target);legacy_target['lab_render_target']=True
    for index in range(2):
        legacy=bpy.data.objects.new('Cámara antigua',bpy.data.cameras.new('Antigua'));scene.collection.objects.link(legacy);legacy['lab_camera']='ORBIT'
        legacy.constraints.new('TRACK_TO').target=legacy_target
    custom=bpy.data.objects.new('Cámara del usuario',bpy.data.cameras.new('Usuario'));scene.collection.objects.link(custom)
    lab_cameras.enter(scene)
    assert [o for o in scene.objects if o.type=='CAMERA']==[custom]
    assert not [o for o in scene.objects if o.get('lab_render_target')]
    bpy.data.objects.remove(custom,do_unlink=True)
    lab_cameras.setup(scene)
    assert not [o for o in scene.objects if o.type=='CAMERA']
    for kind in ('STATIC','ORBIT','INTERIOR','TRAVELLING','SPIRAL'):
        cam=lab_cameras.create(scene,kind=kind)[0]
        assert lab_cameras.create(scene,kind=kind)[0]==cam
        if kind in ('ORBIT','TRAVELLING','SPIRAL'):
            scene.frame_set(1);a=cam.location.copy();scene.frame_set(121);b=cam.location.copy();assert (a-b).length>.001
    lab_cameras.enter(scene);assert len([o for o in scene.objects if o.type=='CAMERA'])==5
    lamp=lab_chandelier.create(scene,roof);assert lab_chandelier.create(scene,roof)==lamp
    lights=[o for o in scene.objects if o.type=='LIGHT' and o.get('lab_decor')];assert len(lights)==3
    scene.frame_set(1);energy=lights[0].data.energy;rotation=lamp.rotation_euler.copy()
    scene.frame_set(19);assert abs(lights[0].data.energy-energy)>1e-5 and (Vector(lamp.rotation_euler)-Vector(rotation)).length>.001
    fog=lab_atmosphere.fog(scene);assert lab_atmosphere.fog(scene)==fog
    mat=fog.data.materials[0]
    lab_cameras.prepare_render(scene);assert len([o for o in scene.objects if o.type=='CAMERA'])==5 and fog.data.materials[0]==mat
    p=scene.ruin_settings;p.height_type='THREE';p.ground_storey_height=125;p.upper_storey_height=125;layout.apply_profiles(p)
    assert abs(p.height-377)<1e-5 and layout.floor_bases(p)==[2,127,252]
    replay=bpy.data.scenes.new('Reproducción prueba artística');replay['ruinas_replay']=True;replay['physics_result_scene']=True
    clone=roof.copy();clone.data=roof.data.copy();clone['replay_source_object']=roof.name;replay.collection.objects.link(clone)
    lab_cameras.copy_to_replay(scene,replay)
    copied=next(o for o in replay.objects if o.get('lab_chandelier'));assert copied.parent==clone
    assert len([o for o in replay.objects if o.type=='LIGHT' and o.get('lab_decor')])==3
    assert all(c.target in list(replay.objects) for o in replay.objects for c in o.constraints if hasattr(c,'target') and c.target)
    before=[tuple(v.co) for v in fog.data.vertices];physics_worker.scale_solver(scene,100)
    assert before==[tuple(v.co) for v in fog.data.vertices]
    bpy.context.window.scene=replay;replay.frame_end=6;replay.frame_set(1)
    clone.location=(0,0,0);clone.keyframe_insert(data_path='location',frame=1);clone.location=(.004,0,-.004);clone.keyframe_insert(data_path='location',frame=6)
    domain=lab_atmosphere.prepare_smoke(replay);assert lab_atmosphere.prepare_smoke(replay)==domain
    settings=domain.modifiers[0].domain_settings
    assert domain['proxy_count']==1 and settings.resolution_max==32
    for ob in replay.objects:ob.select_set(False)
    domain.select_set(True);bpy.context.view_layer.objects.active=domain;replay.frame_set(1)
    result=bpy.ops.fluid.bake_all();assert 'FINISHED' in result
    files=list(Path(settings.cache_directory).rglob('*'));assert any(p.is_file() and p.stat().st_size>100 for p in files)
    replay.frame_set(6);bpy.context.view_layer.update()
    density=list(domain.evaluated_get(bpy.context.evaluated_depsgraph_get()).modifiers[0].domain_settings.density_grid)
    print('DENSITY_DIAGNOSTIC',len(density),max(density,default=0),settings.cache_directory,flush=True)
    assert density and max(density)>0, 'La caché no contiene densidad de humo'
    print('SMOKE_DENSITY',len(density),max(density),flush=True)
    domain.hide_render=True
    replay.frame_set(1)
    camera=next(o for o in replay.objects if o.get('lab_camera')=='STATIC');replay.camera=camera
    camera.location=(.045,-.07,.055);camera.constraints[0].target.location=(0,0,.061);camera.data.lens=55
    replay.render.image_settings.media_type='IMAGE';replay.render.image_settings.file_format='PNG';replay.render.resolution_x=640;replay.render.resolution_y=640;replay.render.resolution_percentage=100;replay.cycles.samples=24
    replay.render.filepath=str(ROOT/'reports/lab_art_direction_preview.png');bpy.ops.render.render(write_still=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'dist/lab_art_direction_smoke_test.blend'))
    report={'cameras':5,'candle_lights':3,'height_mm':377,'floor_bases_mm':[2,127,252],'smoke_frames':6,'max_smoke_density':max(density),'smoke_resolution':32,'smoke_proxies':domain['proxy_count'],'cache':settings.cache_directory,'cache_files':sum(p.is_file() for p in files),'physics_scale_excludes_fog':True,'chandelier_motion':'decorative; parent follows ceiling','full_ten_second_smoke_tested':False}
    (ROOT/'reports/lab_art_direction.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print('ART_DIRECTION_PASSED',report,flush=True)


if __name__=='__main__':run()
