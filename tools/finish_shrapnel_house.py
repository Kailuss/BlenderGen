"""Acabado GPU y polvo temporal sobre las físicas calculadas del ejercicio 02."""
import sys,json,math
from pathlib import Path
import bpy
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
import ruinas_panel as addon
from ruinas_panel import runtime
from ruinas_panel.services import lab_cameras,lab_atmosphere
from stage_shrapnel_house import PATHS
OUT=ROOT/'dist/Ejercicio02_metralla_20261028'


def run(smoke=True):
    'IA: Configura Cycles OptiX 1080p, humo Mantaflow activado por impactos y caché relativa; hornea solo con bandera explícita; smoke=False permite una prueba estática del acabado sin dominio.'
    addon.register();runtime.busy=runtime.preview=True
    s=next(s for s in bpy.data.scenes if s.get('physics_result_scene'))
    bpy.context.window.scene=s;s.frame_set(1)
    for ob in list(s.objects):
        if ob.get('lab_collision_proxy'):bpy.data.objects.remove(ob,do_unlink=True)
    for other in list(bpy.data.scenes):
        if other!=s:bpy.data.scenes.remove(other)
    bpy.data.orphans_purge(do_local_ids=True,do_linked_ids=True,do_recursive=True)
    lab_cameras.prepare_render(s)
    rock=bpy.data.materials.new('Metralla · roca oscura');rock.use_nodes=True
    nodes=rock.node_tree.nodes;links=rock.node_tree.links
    shader=nodes.get('Principled BSDF');shader.inputs['Base Color'].default_value=(.045,.03,.022,1)
    shader.inputs['Roughness'].default_value=.83
    noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=16
    noise.inputs['Detail'].default_value=4
    bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.65;bump.inputs['Distance'].default_value=.001
    links.new(noise.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs['Normal'],shader.inputs['Normal'])
    for ob in s.objects:
        if ob.type=='MESH' and ob.get('impactor'):
            if not ob.material_slots:ob.data.materials.append(rock)
            ob.material_slots[0].link='OBJECT';ob.material_slots[0].material=rock
            source_name=ob.get('replay_source_object',ob.name)
            path=next((path for path in PATHS if source_name=='Metralla · '+path['name']),None)
            if path:
                for frame,hidden in ((1,True),(path['frame']-2,True),(path['frame']-1,False)):
                    ob.hide_render=hidden;ob.keyframe_insert(data_path='hide_render',frame=frame)
    pref=bpy.context.preferences.addons['cycles'].preferences
    pref.compute_device_type='OPTIX';pref.get_devices()
    devices=[]
    for d in pref.devices:
        d.use=d.type=='OPTIX' and '3090' in d.name
        if d.use:devices.append(d.name)
    if not devices:raise ValueError('No se detecta la RTX 3090 Ti por OptiX.')
    s.cycles.device='GPU';s.cycles.samples=1024
    s.cycles.use_adaptive_sampling=True;s.cycles.adaptive_threshold=.003;s.cycles.adaptive_min_samples=64
    s.cycles.use_denoising=True;s.cycles.denoiser='OPENIMAGEDENOISE';s.cycles.denoising_use_gpu=True
    s.cycles.max_bounces=12;s.cycles.diffuse_bounces=6;s.cycles.glossy_bounces=6
    s.cycles.transmission_bounces=6;s.cycles.volume_bounces=4;s.cycles.transparent_max_bounces=8
    s.cycles.caustics_reflective=False;s.cycles.caustics_refractive=False
    s.cycles.volume_step_rate=.5;s.cycles.volume_max_steps=2048
    s.render.use_motion_blur=True;s.render.motion_blur_shutter=.35
    s.render.resolution_x=1920;s.render.resolution_y=1080;s.render.resolution_percentage=100
    s.render.fps=24;s.render.fps_base=1;s.frame_start=1;s.frame_end=241
    s.view_settings.view_transform='AgX'
    s.camera=next(o for o in s.objects if o.get('lab_camera')=='STATIC')
    s.camera.location=(.72,-1.05,.68);s.camera.data.lens=42;s.camera.data.dof.aperture_fstop=8
    s.render.image_settings.media_type='VIDEO';s.render.image_settings.file_format='FFMPEG'
    s.render.ffmpeg.format='MPEG4';s.render.ffmpeg.codec='H264';s.render.ffmpeg.constant_rate_factor='HIGH'
    (OUT/'render').mkdir(exist_ok=True);s.render.filepath='//render/Ejercicio02.mp4'
    s.render.use_file_extension=True
    # Guardar primero fija la raíz para las rutas relativas del dominio.
    target=OUT/'05_render_en_preparacion.blend';bpy.ops.wm.save_as_mainfile(filepath=str(target))
    (OUT/'Render_GPU.py').write_text((ROOT/'tools/render_shrapnel_gpu.py').read_text(encoding='utf8'),encoding='utf8')
    (OUT/'Render_GPU.cmd').write_text('@echo off\n"'+bpy.app.binary_path+'" --factory-startup -b "%~dp005_render_listo.blend" --python-exit-code 1 --python "%~dp0Render_GPU.py"\npause\n',encoding='utf8')
    if not smoke:return
    domain=lab_atmosphere.prepare_smoke(s)
    settings=next(m.domain_settings for m in domain.modifiers if m.type=='FLUID')
    settings.resolution_max=128;settings.use_noise=True;settings.noise_scale=2
    settings.use_adaptive_domain=True;settings.adapt_margin=8
    settings.cache_type='ALL';settings.cache_directory='//cache/humo'
    settings.cache_frame_start=1;settings.cache_frame_end=241
    settings.vorticity=.4;settings.alpha=0;settings.beta=0
    settings.use_dissolve_smoke=True;settings.dissolve_speed=90
    domain['cache_directory']=settings.cache_directory
    for ob in list(s.objects):
        if ob.get('lab_smoke_emitter'):bpy.data.objects.remove(ob,do_unlink=True)
    emitters=[]
    impact_report=json.loads((OUT/'impactos.json').read_text(encoding='utf8'))
    step=impact_report.get('speed_m_s',2)/24
    # La revisión de velocidad conserva las trayectorias pero cambia su duración.
    for path in impact_report['paths']:
        path['release_frame']=path['frame']+math.ceil((Vector(path['end'])-Vector(path['start'])).length/step)+1
    (OUT/'impactos.json').write_text(json.dumps(impact_report,indent=2),encoding='utf8')
    for path in PATHS:
        start=Vector(path['start']);delta=Vector(path['end'])-start;direction=delta.normalized()
        for i,fraction in enumerate((.3,.5,.75)):
            center=start+delta*fraction;radius=path['radius']*.8
            source=lab_atmosphere.box(s,'Polvo localizado · '+path['name']+' · '+str(i),center-Vector((radius,)*3),center+Vector((radius,)*3))
            source.hide_render=True;source.display_type='WIRE';source['lab_smoke_emitter']=True
            mod=source.modifiers.new('Polvo de impacto','FLUID');mod.fluid_type='FLOW';bpy.context.view_layer.update()
            fs=mod.flow_settings;fs.flow_type='SMOKE';fs.flow_behavior='INFLOW'
            fs.density=.8;fs.temperature=0;fs.surface_distance=1.5;fs.use_initial_velocity=True
            fs.velocity_coord=direction*.10+Vector((0,0,.03))
            first=path['frame']+math.floor(delta.length*fraction/step)
            for frame,enabled in ((1,False),(first-1,False),(first,True),(first+7,True),(first+8,False)):
                fs.use_inflow=enabled;fs.keyframe_insert(data_path='use_inflow',frame=frame)
            emitters.append(dict(object=source.name,first_frame=first,last_frame=first+7))
    s.frame_set(1)
    domain['simulation_scope']='Localized dust from nine timed sources; 32 bounding-box obstacles. One-way visual gas simulation, no blast pressure coupling.'
    s['gpu_render_profile']='RTX3090Ti / OptiX / 1080p / 1024 adaptive / shutter .35 / gas128 noise2'
    (OUT/'render_config.json').write_text(json.dumps(dict(gpu=devices,emitters=emitters,smoke_resolution=128,noise_scale=2,cache=settings.cache_directory,samples=1024),indent=2),encoding='utf8')
    bpy.ops.wm.save_as_mainfile(filepath=str(target))
    if '--bake' in sys.argv:
        for ob in bpy.context.selected_objects:ob.select_set(False)
        domain.select_set(True);bpy.context.view_layer.objects.active=domain
        print('SMOKE_BAKE_START',flush=True)
        bpy.ops.fluid.bake_all()
        if not settings.has_cache_baked_data or not settings.has_cache_baked_noise:raise ValueError('El humo no tiene ambas cachés horneadas.')
        target=OUT/'05_render_listo.blend'
        bpy.ops.wm.save_as_mainfile(filepath=str(target))
        print('SMOKE_BAKE_COMPLETE',flush=True)
    if '--proof' in sys.argv:
        s.render.image_settings.media_type='IMAGE';s.render.image_settings.file_format='PNG'
        s.frame_set(135);s.cycles.samples=128;s.render.filepath=str(ROOT/'reports/ejercicio02_render_135.png')
        bpy.ops.render.render(write_still=True)
        print('GPU_PROOF_SAVED',flush=True)


if __name__=='__main__':run()
