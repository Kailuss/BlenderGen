"""Impactos dirigidos y prefractura acotada sobre copias físicas."""
import math
import bpy
import bmesh
from mathutils import Vector,Matrix
from .. import config,runtime
from . import structural_physics


def reset(scene):
    'IA: Invalida el ensayo al editar cuerpos y vuelve al inicio; no modifica las reproducciones horneadas.'
    scene.frame_set(1)
    scene['physics_simulated']=0;runtime.physics_simulations.discard(scene.as_pointer())
    if scene.rigidbody_world:
        with bpy.context.temp_override(scene=scene,point_cache=scene.rigidbody_world.point_cache):
            if scene.rigidbody_world.point_cache.is_baked:bpy.ops.ptcache.free_bake()


def launch(scene,selected):
    'IA: Añade hasta ocho impactos dirigidos a selección o estructura; lanzamiento con cesión a Bullet o empuje cinemático explícito.'
    if not scene.get('structural_physics'):raise ValueError('Prepara primero la casa en el laboratorio físico.')
    if sum(bool(o.get('impactor')) for o in scene.objects)>=8:raise ValueError('Límite de ocho impactos por ensayo.')
    p=scene.ruin_settings;direction=Vector(p.impact_direction)
    if direction.length<1e-6:raise ValueError('La dirección no puede ser cero en los tres ejes.')
    targets=[o for o in selected if o.name in scene.objects and o.rigid_body and not o.get('impactor') and o.rigid_body.type=='ACTIVE']
    if not targets:targets=[o for o in scene.objects if o.rigid_body and o.rigid_body.type=='ACTIVE' and not o.get('impactor')]
    if not targets:raise ValueError('No hay cuerpos móviles a los que apuntar.')
    reset(scene);direction.normalize()
    points=[o.matrix_world@Vector(v) for o in targets for v in o.bound_box]
    center=Vector([(min(v[k] for v in points)+max(v[k] for v in points))/2 for k in range(3)])
    radius=p.impact_radius*.001
    distance=max(abs((v-center).dot(direction)) for v in points)+radius+.025
    start=center-direction*distance
    floors=[o for o in scene.objects if o.rigid_body and o.rigid_body.type=='PASSIVE' and o.get('collision_floor')]
    if floors:
        top=max((o.matrix_world@Vector(v)).z for o in floors for v in o.bound_box)
        start.z=max(start.z,top+radius+.001)
    side=direction.cross(Vector((0,0,1)))
    if side.length<.01:side=Vector((1,0,0))
    side.normalize()
    existing=[Vector(o['launch_start']) for o in scene.objects if o.get('impactor') and 'launch_start' in o]
    while any((start-other).length<radius*2.1 for other in existing):start+=side*radius*2.2
    with bpy.context.temp_override(scene=scene,view_layer=scene.view_layers[0]):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=12,radius=radius,location=start)
        ob=bpy.context.object;bpy.ops.rigidbody.object_add(type='ACTIVE')
    ob.name='Piedra · '+p.impact_mode;ob['impactor']=True;ob['impact_mode']=p.impact_mode;ob['launch_start']=list(start)
    rb=ob.rigid_body;rb.collision_shape='SPHERE';rb.mass=4/3*math.pi*radius**3*2200*config.PHYSICS_MASS_SCALE*p.impact_mass
    rb.friction=1;rb.restitution=0;rb.use_margin=True;rb.collision_margin=.00001
    # El tramo de lanzamiento recorre el espacio vacío hasta cerca del blanco.
    fps=scene.render.fps/scene.render.fps_base;step=p.impact_speed*.001*scene.rigidbody_world.time_scale/fps
    release=max(3,min(scene.frame_end-1,int(max(.001,distance-radius-.01)/step)+1))
    end=scene.frame_end if p.impact_mode=='PRESS' else release
    ob.location=start;ob.keyframe_insert(data_path='location',frame=1)
    ob.location=start+direction*step*(end-1);ob.keyframe_insert(data_path='location',frame=end)
    rb.kinematic=True;rb.keyframe_insert(data_path='kinematic',frame=1);rb.keyframe_insert(data_path='kinematic',frame=end)
    if p.impact_mode=='THROW':rb.kinematic=False;rb.keyframe_insert(data_path='kinematic',frame=end+1)
    action=ob.animation_data.action
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for curve in bag.fcurves:
                    for key in curve.keyframe_points:key.interpolation='LINEAR' if curve.data_path=='location' else 'CONSTANT'
    ob['release_frame']=end+1;reset(scene)
    return ob


def halves(mesh):
    'IA: Corta oblicuamente el centro en dos sólidos cerrados; coordenadas locales en metros, sin separación artificial.'
    points=[v.co for v in mesh.vertices];center=sum(points,Vector())/len(points)
    spans=[max(v[k] for v in points)-min(v[k] for v in points) for k in range(3)]
    axis=max(range(3),key=lambda k:spans[k]);normal=Vector((.17,.11,.23));normal[axis]=1;normal.normalize()
    results=[]
    try:
        for side in (False,True):
            bm=bmesh.new();bm.from_mesh(mesh)
            try:
                bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-8,plane_co=center,plane_no=normal,clear_inner=side,clear_outer=not side)
                edges=[e for e in bm.edges if e.is_boundary]
                bmesh.ops.holes_fill(bm,edges=edges,sides=0)
                bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
                if not bm.faces or not all(e.is_manifold for e in bm.edges) or bm.calc_volume()<=1e-12:raise ValueError('No se puede cerrar la fractura de esta pieza.')
                result=bpy.data.meshes.new('Fragmento de piedra');bm.to_mesh(result)
                for mat in mesh.materials:result.materials.append(mat)
                results.append(result)
            finally:bm.free()
        original=bmesh.new();original.from_mesh(mesh);before=abs(original.calc_volume());original.free()
        after=0
        for result in results:
            check=bmesh.new();check.from_mesh(result);after+=check.calc_volume();check.free()
        if abs(after-before)>max(1e-12,before*.0001):raise ValueError('La fractura no conserva el volumen; se conserva la pieza original.')
        return results
    except Exception:
        for mesh in results:bpy.data.meshes.remove(mesh)
        raise


def fracture(scene,selected):
    'IA: Prefractura hasta 32 piedras activas en dos mitades cerradas con unión rompible; retiene conexiones exteriores y no toca la fuente.'
    if not scene.get('structural_physics'):raise ValueError('Abre el laboratorio físico.')
    chosen=[o for o in selected if o.name in scene.objects and o.rigid_body and o.rigid_body.type=='ACTIVE' and not o.get('fracture_fragment') and (o.get('masonry_brick') or o.get('physical_role')=='stone')]
    if not chosen:raise ValueError('Selecciona ladrillos de piedra sin fracturar, no el proyectil ni el terreno.')
    if len(chosen)>32:raise ValueError('Selecciona como máximo 32 ladrillos por operación.')
    reset(scene);prepared=[]
    try:
        for ob in chosen:prepared.append((ob,halves(ob.data)))
    except Exception:
        for _,meshes in prepared:
            for mesh in meshes:bpy.data.meshes.remove(mesh)
        raise
    fragments=[]
    for original,meshes in prepared:
        children=[];volumes=[]
        for mesh in meshes:
            bm=bmesh.new();bm.from_mesh(mesh);volumes.append(bm.calc_volume());bm.free()
        for i,mesh in enumerate(meshes):
            ob=bpy.data.objects.new(original.name+' · rotura '+str(i+1),mesh);scene.collection.objects.link(ob)
            center=sum((v.co for v in mesh.vertices),Vector())/len(mesh.vertices)
            mesh.transform(Matrix.Translation(-center));ob.matrix_world=original.matrix_world@Matrix.Translation(center)
            for key in original.keys():ob[key]=original[key]
            ob['fracture_fragment']=True;ob['physical_volume_mm3']=volumes[i]*1e9
            with bpy.context.temp_override(scene=scene,view_layer=scene.view_layers[0],object=ob,active_object=ob,selected_objects=[ob]):bpy.ops.rigidbody.object_add(type='ACTIVE')
            rb=ob.rigid_body;rb.collision_shape='MESH';rb.mesh_source='BASE';rb.use_margin=True;rb.collision_margin=0
            rb.mass=max(.001,original.rigid_body.mass*volumes[i]/sum(volumes));rb.friction=1;rb.restitution=0;rb.angular_damping=.5
            children.append(ob)
        for other in list(scene.objects):
            c=other.rigid_body_constraint
            if not c:continue
            nearest=min(children,key=lambda o:(o.location-other.location).length)
            if c.object1==original:c.object1=nearest
            if c.object2==original:c.object2=nearest
        structural_physics.joint(scene,*children,original.location*1000,scene.ruin_settings.fracture_strength)
        fragments.extend(children);bpy.data.objects.remove(original,do_unlink=True)
    reset(scene)
    return fragments


def limit_to_selection(scene,selected):
    'IA: Mantiene móviles solo las piezas seleccionadas hasta el límite; el resto de la casa permanece como soporte pasivo, sin desaparecer.'
    if not scene.get('structural_physics'):raise ValueError('Abre un laboratorio estructural.')
    chosen={o for o in selected if o.name in scene.objects and o.rigid_body and not o.get('collision_floor') and not o.get('impactor') and o.get('physical_role')!='ground'}
    if not chosen:raise ValueError('Selecciona las piezas de la zona que quieres simular.')
    if len(chosen)>scene.ruin_settings.physics_brick_limit:raise ValueError('La selección supera el límite de piezas del panel.')
    reset(scene)
    for ob in scene.objects:
        if not ob.rigid_body or ob.get('impactor'):continue
        if 'original_body_type' not in ob:ob['original_body_type']=ob.rigid_body.type
        ob.rigid_body.type='ACTIVE' if ob in chosen and ob['original_body_type']=='ACTIVE' else 'PASSIVE'
    scene['limited_dynamic_bodies']=len(chosen)
    return len(chosen)
