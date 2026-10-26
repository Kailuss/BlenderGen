"""Bruma visual y simulación de polvo sobre una reproducción calculada."""
import tempfile
from pathlib import Path
import bpy
from mathutils import Vector
from . import lab_cameras


def box(scene,name,lo,hi):
    'IA: Caja cerrada propia de render; lab_decor la excluye de Bullet y de STL.'
    mesh=bpy.data.meshes.new(name)
    vertices=[(x,y,z) for z in (lo[2],hi[2]) for y in (lo[1],hi[1]) for x in (lo[0],hi[0])]
    mesh.from_pydata(vertices,[],[(0,2,3,1),(4,5,7,6),(0,1,5,4),(2,6,7,3),(0,4,6,2),(1,3,7,5)]);mesh.update()
    ob=bpy.data.objects.new(name,mesh);scene.collection.objects.link(ob);ob['lab_decor']=True;return ob


def volume_material(name,density,smoke=False):
    'IA: Material solo volumétrico; densidad de humo procede de Mantaflow, bruma usa ruido procedural.'
    mat=bpy.data.materials.new(name);mat.use_nodes=True;nodes=mat.node_tree.nodes;nodes.clear()
    output=nodes.new('ShaderNodeOutputMaterial');volume=nodes.new('ShaderNodeVolumePrincipled')
    volume.inputs['Color'].default_value=(.72,.65,.54,1);volume.inputs['Anisotropy'].default_value=.25
    multiply=nodes.new('ShaderNodeMath');multiply.operation='MULTIPLY';multiply.inputs[1].default_value=density
    if smoke:
        field=nodes.new('ShaderNodeAttribute');field.attribute_name='density';socket=field.outputs['Fac']
    else:
        field=nodes.new('ShaderNodeTexNoise');field.inputs['Scale'].default_value=3.5;field.inputs['Detail'].default_value=2;socket=field.outputs['Fac']
    mat.node_tree.links.new(socket,multiply.inputs[0]);mat.node_tree.links.new(multiply.outputs[0],volume.inputs['Density'])
    mat.node_tree.links.new(volume.outputs['Volume'],output.inputs['Volume']);return mat


def region(scene):
    'IA: Reserva aire alrededor de la casa en metros, incluyendo margen lateral y altura adicional.'
    lo,hi=lab_cameras.bounds(scene);size=max(hi-lo);margin=max(.025,size*.35)
    return lo-Vector((margin,margin,margin*.15)),hi+Vector((margin,margin,margin*.6)),size


def fog(scene):
    'IA: Añade o ajusta un único bloque de bruma procedural; no pretende simular aire.'
    lo,hi,size=region(scene)
    existing=next((o for o in scene.objects if o.get('lab_fog')),None)
    if existing:
        node=next(n for n in existing.data.materials[0].node_tree.nodes if n.type=='MATH')
        node.inputs[1].default_value=scene.ruin_settings.lab_fog_density/max(size,.01);return existing
    ob=box(scene,'Atmósfera · bruma',lo,hi);ob['lab_fog']=True;ob.display_type='WIRE'
    ob.data.materials.append(volume_material('Atmósfera · bruma',scene.ruin_settings.lab_fog_density/max(size,.01)))
    return ob


def prepare_smoke(scene):
    'IA: Dominio GAS de 32 celdas y emisores con hasta 32 colisionadores animados; solo replay sin Bullet. No es una simulación de presión ni del total de escombros.'
    if not scene.get('physics_result_scene') or not scene.get('ruinas_replay'):
        raise ValueError('Calcula primero las físicas y abre su reproducción; allí el polvo seguirá las trayectorias calculadas.')
    existing=next((o for o in scene.objects if o.get('lab_smoke_domain')),None)
    if existing:return existing
    lo,hi,size=region(scene)
    domain=box(scene,'Atmósfera · polvo simulado',lo,hi);domain['lab_smoke_domain']=True
    bpy.context.view_layer.objects.active=domain;domain.select_set(True)
    mod=domain.modifiers.new('Polvo · dominio','FLUID');mod.fluid_type='DOMAIN';bpy.context.view_layer.update()
    settings=mod.domain_settings;settings.domain_type='GAS';settings.resolution_max=32;settings.cache_type='ALL';settings.use_noise=False
    settings.cache_frame_start=scene.frame_start;settings.cache_frame_end=scene.frame_end
    cache_root=(Path(bpy.data.filepath).parent if bpy.data.filepath else Path(tempfile.gettempdir()))/'Ruinas_cache'
    cache_root.mkdir(parents=True,exist_ok=True)
    settings.cache_directory=tempfile.mkdtemp(prefix='polvo_',dir=str(cache_root));domain['cache_directory']=settings.cache_directory
    settings.alpha=0;settings.beta=0;settings.vorticity=.15
    domain.data.materials.append(volume_material('Atmósfera · polvo',2/max(size,.01),True))
    source=box(scene,'Polvo · emisor',lo+Vector((.002,.002,.002)),Vector((hi.x-.002,hi.y-.002,lo.z+max(.004,size*.025))))
    source.hide_render=True;source.display_type='WIRE';source['lab_smoke_emitter']=True
    flow=source.modifiers.new('Polvo · flujo','FLUID');flow.fluid_type='FLOW';bpy.context.view_layer.update()
    fs=flow.flow_settings;fs.flow_type='SMOKE';fs.flow_behavior='INFLOW';fs.surface_distance=1;fs.density=.08;fs.temperature=0
    fs.use_initial_velocity=True;fs.velocity_coord=(0,0,.025)
    candidates=[o for o in scene.objects if o.type=='MESH' and not o.get('lab_decor') and o.get('replay_source_object') and not o.get('collision_floor') and not o.get('impactor')]
    candidates.sort(key=lambda o:(-(o.dimensions.x*o.dimensions.y*o.dimensions.z),o.name))
    for original in candidates[:32]:
        vertices=[Vector(v) for v in original.bound_box]
        proxy=box(scene,'Polvo · colisionador',tuple(min(v[k] for v in vertices) for k in range(3)),tuple(max(v[k] for v in vertices) for k in range(3)))
        proxy.parent=original;proxy.hide_render=True;proxy.display_type='WIRE';proxy['lab_smoke_proxy']=True
        effector=proxy.modifiers.new('Polvo · obstáculo animado','FLUID');effector.fluid_type='EFFECTOR';bpy.context.view_layer.update();effector.effector_settings.surface_distance=.5
    domain['proxy_count']=min(32,len(candidates));domain['simulation_scope']='Gas/dust with largest 32 bounding-box obstacles; no structural pressure coupling'
    for ob in scene.objects:
        if ob.get('lab_fog'):ob.hide_render=True
    return domain


def bake(scene):
    'IA: Un clic prepara y lanza el horneado nativo con progreso; conserva caché existente y deja errores visibles.'
    domain=prepare_smoke(scene)
    for ob in bpy.context.selected_objects:ob.select_set(False)
    domain.select_set(True);bpy.context.view_layer.objects.active=domain;scene.frame_set(scene.frame_start)
    return bpy.ops.fluid.bake_all('INVOKE_DEFAULT')
