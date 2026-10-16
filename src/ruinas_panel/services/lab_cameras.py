"""Cámaras editables del laboratorio; posiciones en metros originales."""
import math
import bpy
from mathutils import Vector


def create(scene,door=None):
    'IA: Añade una cámara estática, órbita completa de 120 fotogramas e interior hacia la entrada; excluye terreno y proyectiles del encuadre y no cambia duración física.'
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
        result.append(ob)
    scene.camera=result[0];scene.frame_set(1)
    return result


def copy_to_replay(source,result):
    'IA: Copia cámaras y acciones editadas sin escalarlas con Bullet; conserva cámara activa y configuración óptica en reproducción independiente.'
    mapping={}
    for original in source.objects:
        if original.type!='CAMERA':continue
        ob=original.copy();ob.data=original.data.copy();result.collection.objects.link(ob)
        if original.animation_data and original.animation_data.action:ob.animation_data.action=original.animation_data.action.copy()
        mapping[original]=ob
    result.camera=mapping.get(source.camera)
    for key in ('resolution_x','resolution_y','resolution_percentage','pixel_aspect_x','pixel_aspect_y'):
        setattr(result.render,key,getattr(source.render,key))
