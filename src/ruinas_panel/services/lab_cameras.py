"""Cámaras editables del laboratorio; posiciones en metros originales."""
import math
import bpy
from mathutils import Vector


def create(scene,door=None):
    'IA: Tres cámaras con seguimiento y órbita de diez segundos según FPS, sol/área/spot métricos; conserva duración física y excluye terreno del encuadre.'
    points=[o.matrix_basis@Vector(v) for o in scene.objects if o.type=='MESH' and o.get('physical_role')!='ground' and not o.get('impactor') for v in o.bound_box]
    if not points:return []
    lo=Vector([min(v[k] for v in points) for k in range(3)]);hi=Vector([max(v[k] for v in points) for k in range(3)])
    center=(lo+hi)/2;size=max(hi-lo);radius=max(.10,size*2.2);result=[]
    for kind,label in (('STATIC','Estática'),('ORBIT','Órbita 10 s'),('INTERIOR','Interior')):
        existing=next((o for o in scene.objects if o.type=='CAMERA' and o.get('lab_camera')==kind),None)
        if existing:
            result.append(existing);continue
        data=bpy.data.cameras.new('Cámara · '+label);ob=bpy.data.objects.new(data.name,data);scene.collection.objects.link(ob)
        ob['lab_camera']=kind;data.type='PERSP';data.lens=42 if kind!='INTERIOR' else 18;data.clip_start=.0001;data.clip_end=max(200,size*100)
        if kind=='INTERIOR':
            target=Vector(((door['left']+door['right'])*.0005 if door else center.x,lo.y,(door['top']*.0005 if door else lo.z+.025)))
            ob.location=(center.x,hi.y-(hi.y-lo.y)*.15,min(hi.z-.01,lo.z+.045))
            ob.rotation_euler=(target-ob.location).to_track_quat('-Z','Y').to_euler()
        else:
            intervals=max(1,round(10*scene.render.fps/scene.render.fps_base))
            for frame in (range(1,intervals+2) if kind=='ORBIT' else (1,)):
                angle=-math.pi*.75+2*math.pi*(frame-1)/intervals
                ob.location=center+Vector((radius*math.cos(angle),radius*math.sin(angle),radius*.55))
                ob.rotation_euler=(center-ob.location).to_track_quat('-Z','Y').to_euler()
                if kind=='ORBIT':
                    ob.keyframe_insert(data_path='location',frame=frame);ob.keyframe_insert(data_path='rotation_euler',frame=frame)
        aim=bpy.data.objects.new('Objetivo · '+label,None);scene.collection.objects.link(aim)
        aim.location=target if kind=='INTERIOR' else center
        aim.empty_display_type='SPHERE';aim.empty_display_size=max(.002,size*.035);aim['lab_render_target']=True
        track=ob.constraints.new('TRACK_TO');track.name='Seguir objetivo editable'
        track.target=aim;track.track_axis='TRACK_NEGATIVE_Z';track.up_axis='UP_Y'
        result.append(ob)
    lighting(scene,center,size)
    scene.camera=result[0];scene.frame_set(1)
    return result


def lighting(scene,center,size):
    'IA: Completa sol/área/spot sin duplicar luces marcadas ni reemplazar ajustes existentes; potencias métricas y mundo tenue solo si faltan.'
    size=max(.05,size)
    for kind,label,offset,power in (
        ('SUN','Sol',(-2,-3,4),1.5),
        ('AREA','Relleno',(2,-1,2),60*size*size),
        ('SPOT','Contraluz',(-1,2,3),45*size*size)):
        if any(o.type=='LIGHT' and o.get('lab_light') and o.data.type==kind for o in scene.objects):continue
        data=bpy.data.lights.new('Luz · '+label,kind);ob=bpy.data.objects.new(data.name,data);scene.collection.objects.link(ob)
        ob['lab_light']=True;ob.location=center+Vector(offset)*size
        ob.rotation_euler=(center-ob.location).to_track_quat('-Z','Y').to_euler();data.energy=power
        if kind=='SUN':data.angle=.12;data.color=(1,.91,.78)
        elif kind=='AREA':data.shape='DISK';data.size=size*2;data.color=(.78,.87,1)
        else:data.spot_size=math.radians(65);data.spot_blend=.6;data.shadow_soft_size=size*.15;data.color=(1,.65,.78)
    if scene.world is None:
        world=bpy.data.worlds.new('Mundo · laboratorio');world.use_nodes=True
        world.node_tree.nodes.get('Background').inputs['Color'].default_value=(.18,.21,.27,1)
        world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.3;scene.world=world
    scene.render.engine='CYCLES';scene.cycles.samples=64;scene.cycles.use_denoising=True
    scene.render.resolution_x=1600;scene.render.resolution_y=1200;scene.render.resolution_percentage=100
    from ..geometry import surfaces
    for ob in scene.objects:
        if ob.type=='MESH':
            for slot in ob.material_slots:
                if slot.material:
                    material=surfaces.lab_material(slot.material);slot.link='OBJECT';slot.material=material


def ten_seconds(scene):
    'IA: Configura diez segundos físicos a escala temporal uno, retima solo órbitas marcadas y completa luces; rechaza caché horneada y conserva nombres y selección.'
    world=scene.rigidbody_world
    if not world:raise ValueError('Abre un laboratorio físico antes de preparar la toma.')
    if world.point_cache.is_baked:raise ValueError('Libera la caché horneada antes de cambiar la duración.')
    points=[o.matrix_basis@Vector(v) for o in scene.objects if o.type=='MESH' and o.get('physical_role')!='ground' and not o.get('impactor') for v in o.bound_box]
    if not points:raise ValueError('El laboratorio no contiene piezas.')
    lo=Vector([min(v[k] for v in points) for k in range(3)]);hi=Vector([max(v[k] for v in points) for k in range(3)])
    intervals=max(1,round(10*scene.render.fps/scene.render.fps_base))
    from . import impact_physics
    impact_physics.reset(scene)
    scene.frame_start=1;scene.frame_end=intervals+1;scene.ruin_settings.physics_frames=scene.frame_end
    world.point_cache.frame_start=1;world.point_cache.frame_end=scene.frame_end;world.time_scale=1
    for ob in scene.objects:
        if ob.get('lab_camera')!='ORBIT' or not ob.animation_data or not ob.animation_data.action:continue
        action=ob.animation_data.action.copy();ob.animation_data.action=action
        curves=[curve for layer in action.layers for strip in layer.strips for bag in strip.channelbags for curve in bag.fcurves if curve.data_path in ('location','rotation_euler')]
        keys=[key for curve in curves for key in curve.keyframe_points]
        if not keys:continue
        first=min(key.co.x for key in keys);last=max(key.co.x for key in keys)
        if last<=first:continue
        scale=intervals/(last-first)
        for key in keys:
            key.co.x=1+(key.co.x-first)*scale
            key.handle_left.x=1+(key.handle_left.x-first)*scale
            key.handle_right.x=1+(key.handle_right.x-first)*scale
        for curve in curves:curve.update()
    lighting(scene,(lo+hi)/2,max(hi-lo))
    return scene.frame_end


def prepare_render(scene):
    'IA: Completa equipo de render, Cycles con rebotes, DOF y vídeo H264; aplica materiales visuales compartidos sin cambiar mallas ni recalcular física.'
    camera=scene.camera;frame=scene.frame_current;subframe=scene.frame_subframe
    create(scene)
    scene.frame_set(frame,subframe=subframe)
    if camera and camera.name in scene.objects:scene.camera=camera
    for ob in scene.objects:
        if ob.type!='CAMERA':continue
        target=next((c.target for c in ob.constraints if hasattr(c,'target') and c.target),None)
        if target:
            ob.data.dof.use_dof=True;ob.data.dof.focus_object=target;ob.data.dof.aperture_fstop=11
    scene.render.engine='CYCLES';scene.cycles.samples=128;scene.cycles.use_denoising=True
    scene.cycles.max_bounces=8;scene.cycles.diffuse_bounces=4;scene.cycles.glossy_bounces=4;scene.cycles.transmission_bounces=6
    scene.render.resolution_x=1920;scene.render.resolution_y=1080;scene.render.resolution_percentage=100
    if hasattr(scene.render.image_settings,'media_type'):scene.render.image_settings.media_type='VIDEO'
    scene.render.image_settings.file_format='FFMPEG';scene.render.ffmpeg.format='MPEG4';scene.render.ffmpeg.codec='H264';scene.render.ffmpeg.constant_rate_factor='HIGH'
    from pathlib import Path
    from datetime import datetime
    from ..ui import preferences
    folder=Path(bpy.path.abspath(preferences.value('render_directory','//Videos Render/')))
    folder.mkdir(parents=True,exist_ok=True)
    stem=bpy.path.clean_name(Path(bpy.data.filepath).stem or 'Ruinas')
    scene.render.filepath=str(folder/(stem+'_'+bpy.path.clean_name(scene.name)+'_'+datetime.now().strftime('%Y%m%d_%H%M%S')+'_'));scene.render.use_file_extension=True
    from ..geometry import surfaces
    for ob in scene.objects:
        if ob.type!='MESH' or ob.get('collision_floor'):continue
        for slot in ob.material_slots:
            if slot.material:
                material=surfaces.render_material(slot.material);slot.link='OBJECT';slot.material=material
    scene['render_detail_instructions']='F12: imagen; Ctrl+F12: vídeo H264. Microrelieve visual, no modifica el STL.'


def copy_to_replay(source,result):
    'IA: Copia cámaras, luces, objetivos, seguimiento y mundo sin escalarlos con Bullet; remapea objetivos al duplicado o pieza de reproducción.'
    mapping={}
    for original in source.objects:
        if original.type not in ('CAMERA','LIGHT') and not original.get('lab_render_target'):continue
        ob=original.copy()
        if original.data:ob.data=original.data.copy()
        result.collection.objects.link(ob)
        if original.animation_data and original.animation_data.action:ob.animation_data.action=original.animation_data.action.copy()
        mapping[original]=ob
    pieces={o.get('replay_source_object'):o for o in result.objects if o.get('replay_source_object')}
    for original,ob in mapping.items():
        for constraint in ob.constraints:
            if hasattr(constraint,'target') and constraint.target:
                constraint.target=mapping.get(constraint.target) or pieces.get(constraint.target.name)
    result.camera=mapping.get(source.camera)
    result.world=source.world.copy() if source.world else None
    result.render.engine=source.render.engine
    result.cycles.samples=source.cycles.samples;result.cycles.use_denoising=source.cycles.use_denoising
    for key in ('resolution_x','resolution_y','resolution_percentage','pixel_aspect_x','pixel_aspect_y'):
        setattr(result.render,key,getattr(source.render,key))
    for key in ('max_bounces','diffuse_bounces','glossy_bounces','transmission_bounces'):
        setattr(result.cycles,key,getattr(source.cycles,key))
    if hasattr(source.render.image_settings,'media_type'):result.render.image_settings.media_type=source.render.image_settings.media_type
    result.render.image_settings.file_format=source.render.image_settings.file_format
    for key in ('format','codec','constant_rate_factor'):
        setattr(result.render.ffmpeg,key,getattr(source.render.ffmpeg,key))
    result.render.filepath=source.render.filepath
    for original,ob in mapping.items():
        if ob.type=='CAMERA' and original.data.dof.focus_object:
            target=original.data.dof.focus_object
            ob.data.dof.focus_object=mapping.get(target) or pieces.get(target.name)
