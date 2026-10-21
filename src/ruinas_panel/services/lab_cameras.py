"""Cámaras editables del laboratorio; posiciones en metros originales."""
import math
import bpy
from mathutils import Vector


def create(scene,door=None):
    'IA: Tres cámaras con objetivo editable y seguimiento, sol/área/spot a escala métrica; excluye terreno y proyectiles del encuadre y conserva duración física.'
    points=[o.matrix_basis@Vector(v) for o in scene.objects if o.type=='MESH' and o.get('physical_role')!='ground' and not o.get('impactor') for v in o.bound_box]
    if not points:return []
    lo=Vector([min(v[k] for v in points) for k in range(3)]);hi=Vector([max(v[k] for v in points) for k in range(3)])
    center=(lo+hi)/2;size=max(hi-lo);radius=max(.10,size*2.2);result=[]
    for kind,label in (('STATIC','Estática'),('ORBIT','Órbita 120'),('INTERIOR','Interior')):
        data=bpy.data.cameras.new('Cámara · '+label);ob=bpy.data.objects.new(data.name,data);scene.collection.objects.link(ob)
        ob['lab_camera']=kind;data.type='PERSP';data.lens=42 if kind!='INTERIOR' else 18;data.clip_start=.0001;data.clip_end=max(200,size*100)
        if kind=='INTERIOR':
            target=Vector(((door['left']+door['right'])*.0005 if door else center.x,lo.y,(door['top']*.0005 if door else lo.z+.025)))
            ob.location=(center.x,hi.y-(hi.y-lo.y)*.15,min(hi.z-.01,lo.z+.045))
            ob.rotation_euler=(target-ob.location).to_track_quat('-Z','Y').to_euler()
        else:
            for frame in (range(1,121) if kind=='ORBIT' else (1,)):
                angle=-math.pi*.75+2*math.pi*(frame-1)/119
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
    'IA: Equipo de tres luces editables: sol constante y área/foco con potencia proporcional al tamaño al cuadrado; mundo tenue y materiales visuales métricos.'
    size=max(.05,size)
    for kind,label,offset,power in (
        ('SUN','Sol',(-2,-3,4),1.5),
        ('AREA','Relleno',(2,-1,2),60*size*size),
        ('SPOT','Contraluz',(-1,2,3),45*size*size)):
        data=bpy.data.lights.new('Luz · '+label,kind);ob=bpy.data.objects.new(data.name,data);scene.collection.objects.link(ob)
        ob['lab_light']=True;ob.location=center+Vector(offset)*size
        ob.rotation_euler=(center-ob.location).to_track_quat('-Z','Y').to_euler();data.energy=power
        if kind=='SUN':data.angle=.12;data.color=(1,.91,.78)
        elif kind=='AREA':data.shape='DISK';data.size=size*2;data.color=(.78,.87,1)
        else:data.spot_size=math.radians(65);data.spot_blend=.6;data.shadow_soft_size=size*.15;data.color=(1,.65,.78)
    world=bpy.data.worlds.new('Mundo · laboratorio');world.use_nodes=True
    world.node_tree.nodes.get('Background').inputs['Color'].default_value=(.18,.21,.27,1)
    world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.3;scene.world=world
    scene.render.engine='CYCLES';scene.cycles.samples=64;scene.cycles.use_denoising=True
    scene.render.resolution_x=1600;scene.render.resolution_y=1200;scene.render.resolution_percentage=100
    from ..geometry import surfaces
    for ob in scene.objects:
        if ob.type=='MESH':
            for slot in ob.material_slots:
                if slot.material:slot.material=surfaces.lab_material(slot.material)


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
