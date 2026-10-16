"""Zarandeo corto sobre una copia aislada; conserva el laboratorio del usuario."""
import json
import bpy
from mathutils import Vector
from .. import config
from . import impact_physics,structural_physics


def selected(scene,names):
    'IA: Exige selección explícita de cuerpos originalmente móviles y respeta el límite; nunca amplía silenciosamente la selección a todo el edificio.'
    if not scene.get('structural_physics'):raise ValueError('Prepara primero el edificio en el laboratorio.')
    names=set(names)
    chosen=[o for o in scene.objects if o.name in names and o.rigid_body and not o.get('impactor') and o.get('physical_role')!='ground' and o.get('original_body_type',o.rigid_body.type)=='ACTIVE']
    if not chosen:raise ValueError('Selecciona las piezas que quieres soltar antes de zarandear.')
    if len(chosen)>scene.ruin_settings.physics_brick_limit:raise ValueError('La selección supera el límite de piezas del laboratorio.')
    return chosen


def prepare(scene,names):
    'IA: Solo en el hijo: limita móviles a selección, suelta uniones en 2 y aplica cuatro empujes de esquina hasta 4, ocultos y sin colisión desde 5; calcula diez fotogramas.'
    chosen=selected(scene,names);impact_physics.reset(scene)
    old=[o for o in scene.objects if o.get('impactor')]
    old_set=set(old);joints=[o for o in scene.objects if o.rigid_body_constraint and old_set.intersection((o.rigid_body_constraint.object1,o.rigid_body_constraint.object2))]
    if joints:bpy.data.batch_remove(ids=tuple(joints))
    bpy.data.batch_remove(ids=tuple(old))
    impact_physics.limit_to_selection(scene,chosen)
    if 'support_release' in scene:del scene['support_release']
    attached=any(o.rigid_body_constraint and set(chosen).intersection((o.rigid_body_constraint.object1,o.rigid_body_constraint.object2)) for o in scene.objects)
    if attached:structural_physics.release(scene,chosen,frame=2)
    points=[o.matrix_basis@v.co for o in scene.objects if o.type=='MESH' and o.rigid_body and o.get('physical_role')!='ground' for v in o.data.vertices]
    low=Vector([min(v[k] for v in points) for k in range(3)]);high=Vector([max(v[k] for v in points) for k in range(3)])
    if 'structural_bounds_mm' in scene:
        x0,x1,y0,y1,z0,z1=scene['structural_bounds_mm'];low=Vector((x0,y0,z0))*.001;high=Vector((x1,y1,z1))*.001
    center=(low+high)/2;radius=config.SHAKE_RADIUS_MM/1000;stroke=scene.ruin_settings.physics_shake_strength/1000
    for index,(x,y) in enumerate(((low.x,low.y),(high.x,low.y),(high.x,high.y),(low.x,high.y))):
        corner=Vector((x,y,center.z));direction=Vector((center.x-x,center.y-y,0)).normalized()
        # Arranca fuera de la esquina; recorre el radio de contacto y unos mm dentro.
        start=corner-direction*(radius+.0002)
        with bpy.context.temp_override(scene=scene,view_layer=scene.view_layers[0]):
            bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=8,radius=radius,location=start)
            ob=bpy.context.object;bpy.ops.rigidbody.object_add(type='ACTIVE')
        ob.name='Zarandeo · esquina %s'%index;ob['impactor']=True;ob['shake_impactor']=True;ob['impact_expire_frame']=config.SHAKE_EXPIRE_FRAME
        ob['impact_render_visible']=scene.ruin_settings.impact_render_visible
        rb=ob.rigid_body;rb.collision_shape='SPHERE';rb.kinematic=True;rb.friction=1;rb.restitution=0;rb.use_margin=True;rb.collision_margin=.00001
        ob.location=start;ob.keyframe_insert(data_path='location',frame=1)
        ob.location=start+direction*stroke;ob.keyframe_insert(data_path='location',frame=config.SHAKE_EXPIRE_FRAME-1)
        rb.keyframe_insert(data_path='collision_collections',frame=1);rb.collision_collections=(False,)*20;rb.keyframe_insert(data_path='collision_collections',frame=config.SHAKE_EXPIRE_FRAME)
        for key in ('hide_viewport','hide_render'):
            setattr(ob,key,key=='hide_render' and not ob['impact_render_visible']);ob.keyframe_insert(data_path=key,frame=1)
            setattr(ob,key,True);ob.keyframe_insert(data_path=key,frame=config.SHAKE_EXPIRE_FRAME)
        for layer in ob.animation_data.action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for curve in bag.fcurves:
                        for key in curve.keyframe_points:key.interpolation='LINEAR' if curve.data_path=='location' else 'CONSTANT'
    scene.frame_end=config.SHAKE_FRAMES;scene.rigidbody_world.point_cache.frame_end=config.SHAKE_FRAMES;scene.frame_set(1)
    scene['shake_report']=json.dumps({'selected':len(chosen),'frames':config.SHAKE_FRAMES,'release_frame':2,'expire_frame':config.SHAKE_EXPIRE_FRAME,'stroke_mm':stroke*1000,'impactors':4})
    return chosen
