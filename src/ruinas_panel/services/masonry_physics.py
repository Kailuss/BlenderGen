"""Ensayo acotado de mampostería seca: contacto y gravedad, con juntas rompibles."""
import math
import bpy
from .. import config,runtime
from . import physics


def prepare(source):
    'IA: Crea hasta 256 ladrillos individuales según el límite solicitado, aparejados sobre suelo pasivo; no modifica la casa.'
    p=source.ruin_settings
    scene=bpy.data.scenes.new('LAB · ladrillos '+p.physics_masonry_shape)
    scene['ruinas_physics_lab']=True;scene['structural_physics']=True;scene['masonry_lab']=True
    scene['source_scene']=source.name;scene['physics_room']='mampostería con cohesión'
    scene.unit_settings.system='METRIC';scene.unit_settings.length_unit='MILLIMETERS'
    scene.frame_end=p.physics_frames
    mat=bpy.data.materials.new('Piedra · ensayo');mat.diffuse_color=(.48,.32,.20,1)
    poses=[];limit=min(256,p.physics_brick_limit)
    if p.physics_masonry_shape=='WALL':
        for row in range(limit//8):
            for col in range(8):poses.append(((col-3.5)*12+(3 if row%2 else 0),0,3+row*6,False))
    else:
        for row in range(limit//14):
            course=[(x,y,False) for y in (-21,21) for x in (-18,-6,6,18)]
            course += [(x,y,True) for x in (-21,21) for y in (-12,0,12)]
            for x,y,turned in course:
                if row%2:x,y,turned=-y,x,not turned
                poses.append((x,y,3+row*6,turned))
    for index,(x,y,z,turned) in enumerate(poses):
        hx,hy=(2.98,5.98) if turned else (5.98,2.98)
        ob=physics.body(scene,'Ladrillo %03d'%index,(x-hx,y-hy,z-2.98),(x+hx,y+hy,z+2.98),True)
        ob['masonry_brick']=True;ob['course']=int(z//6)
        ob.rigid_body.mass=11.96*5.96*5.96*1e-9*2200*config.PHYSICS_MASS_SCALE
        ob.rigid_body.friction=1;ob.data.materials.append(mat)
        bevel=ob.modifiers.new('Aristas de piedra','BEVEL');bevel.width=.00015;bevel.segments=1
    floor=physics.body(scene,'Suelo de colisión',(-500,-500,-5),(500,500,0),False)
    floor['collision_floor']=True
    from . import structural_physics
    scene.view_layers[0].update()
    bricks=[o for o in scene.objects if o.get('masonry_brick')]
    template=None
    for index,a in enumerate(bricks):
        for b in bricks[index+1:]:
            delta=b.location-a.location;limits=(a.dimensions+b.dimensions)*.5
            if all(abs(delta[k])<=limits[k]+.00006 for k in range(3)):
                template=structural_physics.joint(scene,a,b,(a.location+b.location)*500,2,template)
    scene['brick_count']=len(poses)
    world=scene.rigidbody_world;world.substeps_per_frame=20;world.solver_iterations=40;world.time_scale=.3
    world.point_cache.frame_end=scene.frame_end
    scene.frame_set(1)
    return scene


def remove_selected(scene,objects):
    'IA: Retira varias piezas del laboratorio seco en el fotograma inicial; conserva suelo, proyectil y fuente.'
    if not scene.get('masonry_lab'):raise ValueError('Abre un laboratorio de ladrillos.')
    chosen=[o for o in objects if o.name in scene.objects and o.get('masonry_brick')]
    if not chosen:raise ValueError('Selecciona varios ladrillos con Mayús o B; el suelo está protegido.')
    scene.frame_set(1)
    for ob in list(scene.objects):
        c=ob.rigid_body_constraint
        if c and (c.object1 in chosen or c.object2 in chosen):bpy.data.objects.remove(ob,do_unlink=True)
    for ob in chosen:bpy.data.objects.remove(ob,do_unlink=True)
    scene['brick_count']=sum(bool(o.get('masonry_brick')) for o in scene.objects)
    scene['physics_simulated']=0;runtime.physics_simulations.discard(scene.as_pointer())
    return len(chosen)


def impactor(scene):
    'IA: Añade una piedra esférica pesada por encima del muro; cae por gravedad y puede moverse en el fotograma uno.'
    if not scene.get('masonry_lab'):raise ValueError('Abre un laboratorio de ladrillos.')
    if any(o.get('impactor') for o in scene.objects):raise ValueError('Ya hay una piedra; muévela en el fotograma 1.')
    scene.frame_set(1)
    top=max((o.location.z+.003 for o in scene.objects if o.get('masonry_brick')),default=.06)
    with bpy.context.temp_override(scene=scene,view_layer=scene.view_layers[0]):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=12,radius=.018,location=(0,-.006,top+.06))
        ob=bpy.context.object
        bpy.ops.rigidbody.object_add(type='ACTIVE')
    ob.name='Piedra de impacto';ob['impactor']=True
    rb=ob.rigid_body;rb.collision_shape='SPHERE';rb.mass=4/3*math.pi*.018**3*2200*config.PHYSICS_MASS_SCALE
    rb.friction=1;rb.restitution=0;rb.use_margin=True;rb.collision_margin=.00001
    scene['physics_simulated']=0;runtime.physics_simulations.discard(scene.as_pointer())
    return ob
