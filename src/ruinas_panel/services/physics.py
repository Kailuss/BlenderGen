"""Primer ensayo físico aislado: secciones de un tabique, sin tocar la fuente."""
import json
import bpy
from mathutils import Vector
from .. import config


def sections(coll):
    'IA: Recupera identidad y cotas mundiales de tabiques únicos o agrupados; nunca modifica la fuente.'
    result=[]
    for ob in coll.objects:
        if 'partition_section' in ob:
            records=[{'partition':{k:ob[k] for k in ('partition_section','rests_on','partition_id') if k in ob},'vertex_start':0,'vertex_count':len(ob.data.vertices)}]
        elif ob.get('ruin_batch'):
            records=json.loads(ob['ruin_parts'])
        else:continue
        for rec in records:
            tags=rec.get('partition',{})
            if not tags:continue
            points=[ob.matrix_world@v.co for v in ob.data.vertices[rec['vertex_start']:rec['vertex_start']+rec['vertex_count']]]
            result.append({'id':tags['partition_section'],'support':tags['rests_on'],'partition':tags.get('partition_id',int(tags['partition_section'].split(':')[0])),
                           'lo':[min(v[i] for v in points) for i in range(3)],'hi':[max(v[i] for v in points) for i in range(3)]})
    return sorted(result,key=lambda r:r['id'])


def body(scene,name,lo,hi,active):
    'IA: Caja centrada en metros y escala unidad, margen físico de .01 mm; densidad de madera aproximada para ensayo.'
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
    'IA: Crea una escena nueva de ensayo del primer tabique con cajas sin solapes; dinteles y suelo pasivos, secciones libres; no certifica derrumbe estructural.'
    coll=bpy.data.collections.get(config.COLLECTION)
    if coll and not any(ob.name in source_scene.objects for ob in coll.objects):coll=None
    records=sections(coll) if coll else []
    if not records:raise ValueError('Genera primero habitaciones con tabiques. Si la vista agrupada es anterior, pulsa Actualizar.')
    first=min(r['partition'] for r in records);records=[r for r in records if r['partition']==first]
    lintels={r['id']:r for r in records if r['support']=='jambs'}
    boxes=[]
    for rec in records:
        lo=[v+.03 for v in rec['lo']];hi=[v-.03 for v in rec['hi']]
        if rec['support'] in lintels:lo[2]=max(lo[2],lintels[rec['support']]['hi'][2]+.03)
        if min(b-a for a,b in zip(lo,hi))<=.02:continue
        boxes.append((rec,lo,hi))
    for i,(_,lo,hi) in enumerate(boxes):
        for _,other_lo,other_hi in boxes[i+1:]:
            if all(min(hi[k],other_hi[k])-max(lo[k],other_lo[k])>1e-5 for k in range(3)):
                raise ValueError('El tabique contiene solapes que requieren resolver los apoyos antes del ensayo.')
    scene=bpy.data.scenes.new('Ruinas · ensayo de tabique')
    scene['ruinas_physics_lab']=True;scene['source_scene']=source_scene.name
    scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1;scene.unit_settings.length_unit='MILLIMETERS'
    scene.gravity=(0,0,-9.81);scene.frame_end=120
    for rec,lo,hi in boxes:
        ob=body(scene,'Ensayo · '+rec['id'],lo,hi,rec['support']!='jambs')
        ob['source_section']=rec['id'];ob['source_support']=rec['support']
    low=[min(lo[k] for _,lo,hi in boxes) for k in range(3)];high=[max(hi[k] for _,lo,hi in boxes) for k in range(3)]
    body(scene,'Ensayo · suelo',[low[0]-50,low[1]-50,low[2]-2],[high[0]+50,high[1]+50,low[2]-.03],False)
    world=scene.rigidbody_world;world.substeps_per_frame=20;world.solver_iterations=40;world.point_cache.frame_end=120
    scene['limitations']='Solo primer tabique; cajas simplificadas, madera suelta sin uniones ni transferencia a la casa. Dinteles fijados como apoyo de ensayo.'
    return scene
