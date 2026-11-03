"""Entrada única al laboratorio físico: firma de la fuente, preparación del edificio y cuerpos de prueba."""
import json
import hashlib
import bpy
from mathutils import Vector
from .. import config


def signature(p):
    'IA: Firma del modelo para no reaplicar poses a otras semillas o dimensiones; opciones de calidad y presentación no la invalidan.'
    ignored={'preview_quality','export_quality','quick_edit','batch_preview','microdetail_preview','use_instances','export_density'}
    values={k:getattr(p,k) for k in config.FIELDS if k not in ignored}
    values.update(lock_distribution=p.lock_distribution,distribution_seed=p.distribution_seed,physics_schema=2)
    return hashlib.sha256(json.dumps(values,sort_keys=True).encode()).hexdigest()


def source_matches(scene):
    'IA: Compara la configuración actual de la fuente con la firma guardada del laboratorio; devuelve None cuando falta la fuente o su firma, sin evaluar geometría.'
    source=bpy.data.scenes.get(scene.get('source_scene',''))
    saved=scene.get('source_signature')
    return signature(source.ruin_settings)==saved if source and saved else None


def body(scene,name,lo,hi,active):
    'IA: Caja de prueba centrada en metros y escala unidad, margen físico de .01 mm; densidad de madera aproximada. La usan bancos y pruebas, no el laboratorio.'
    center=Vector([(a+b)*.0005 for a,b in zip(lo,hi)])
    half=[(b-a)*.0005 for a,b in zip(lo,hi)]
    verts=[(x*half[0],y*half[1],z*half[2]) for x,y,z in ((-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1))]
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]);mesh.update()
    ob=bpy.data.objects.new(name,mesh);scene.collection.objects.link(ob);ob.location=center
    with bpy.context.temp_override(scene=scene,view_layer=scene.view_layers[0],object=ob,active_object=ob,selected_objects=[ob],selected_editable_objects=[ob]):
        bpy.ops.rigidbody.object_add(type='ACTIVE' if active else 'PASSIVE')
    rb=ob.rigid_body;rb.collision_shape='BOX';rb.use_margin=True;rb.collision_margin=.00001
    rb.mass=max(.001,8*half[0]*half[1]*half[2]*600);rb.friction=.65;rb.restitution=0
    return ob


def prepare(source_scene):
    'IA: Única entrada al laboratorio: el edificio completo sin mortero (structural_physics). El ejemplo aislado de ladrillos tiene su propia acción.'
    from . import structural_physics
    return structural_physics.prepare(source_scene)


def release_support(scene,objects):
    'IA: Suelta las uniones de las piezas seleccionadas en un laboratorio de edificio; no existe otro tipo de laboratorio con apoyos.'
    if not scene.get('structural_physics'):raise ValueError('Abre un laboratorio de edificio para soltar uniones.')
    from . import structural_physics
    return structural_physics.release(scene,objects)
