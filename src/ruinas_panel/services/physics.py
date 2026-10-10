"""Primer ensayo físico aislado: secciones de un tabique, sin tocar la fuente."""
import json
import hashlib
import random
import bpy
from mathutils import Vector,Matrix
from .. import config,meta,runtime


def signature(p):
    'IA: Firma del modelo para no reaplicar poses a otras semillas o dimensiones; opciones de calidad y presentación no invalidan los IDs de tabique.'
    ignored={'preview_quality','export_quality','quick_edit','batch_preview','microdetail_preview','use_instances','export_density'}
    values={k:getattr(p,k) for k in config.FIELDS if k not in ignored}
    values.update(lock_distribution=p.lock_distribution,distribution_seed=p.distribution_seed,physics_schema=2)
    return hashlib.sha256(json.dumps(values,sort_keys=True).encode()).hexdigest()


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
            # El laboratorio antiguo solo conoce paneles; el nuevo simula
            # también travesaños y el resto del edificio con contactos reales.
            if ':rail' in tags['partition_section']:continue
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
    'IA: MASONRY prepara un ensayo seco acotado, BUILDING el edificio completo; las opciones heredadas preparan cajas de tabiques por estancia, sin mampostería ni tejado.'
    p=source_scene.ruin_settings;target=p.physics_target
    if target=='MASONRY':
        from . import masonry_physics
        return masonry_physics.prepare(source_scene)
    if target=='BUILDING':
        from . import structural_physics
        return structural_physics.prepare(source_scene)
    if meta.get(source_scene,'physics_result',{}):raise ValueError('Descarta el resultado físico anterior antes de iniciar otro ensayo.')
    coll=bpy.data.collections.get(config.COLLECTION)
    if coll and not any(ob.name in source_scene.objects for ob in coll.objects):coll=None
    records=sections(coll) if coll else []
    if not records:raise ValueError('Genera primero habitaciones con tabiques. Si la vista agrupada es anterior, pulsa Actualizar.')
    room=None
    if target=='PARTITION':
        first=min(r['partition'] for r in records);records=[r for r in records if r['partition']==first]
    else:
        rooms=meta.get(source_scene,'plano_interior',{}).get('rooms',[]);index=int(target[-1])-1
        if index>=len(rooms):raise ValueError('Esa estancia no existe en el plano generado.')
        room=rooms[index];x0,x1,y0,y1=room['bounds']
        records=[r for r in records if r['hi'][0]>x0-1.6 and r['lo'][0]<x1+1.6 and r['hi'][1]>y0-1.6 and r['lo'][1]<y1+1.6]
        if not records:raise ValueError('No quedan secciones de tabique en esa estancia.')
    lintels={r['id']:r for r in records if r['support']=='jambs'}
    boxes=[]
    for rec in records:
        lo=[v+.03 for v in rec['lo']];hi=[v-.03 for v in rec['hi']]
        if room and rec['support']=='ground':lo[2]=max(lo[2],(3.2 if p.ground_floor else .7)+.03)
        if rec['support'] in lintels:lo[2]=max(lo[2],lintels[rec['support']]['hi'][2]+.03)
        if min(b-a for a,b in zip(lo,hi))<=.02:continue
        boxes.append((rec,lo,hi))
    # Resolver únicamente encuentros ortogonales de tabiques, recortando cajas,
    # no el detalle imprimible. Un solape mayor requiere otra descomposición.
    for i,(rec,lo,hi) in enumerate(boxes):
        for other,other_lo,other_hi in boxes[i+1:]:
            if all(min(hi[k],other_hi[k])-max(lo[k],other_lo[k])>1e-5 for k in range(3)):
                if rec['partition']==other['partition']:raise ValueError('Solape entre secciones del mismo tabique.')
                axis=min((0,1),key=lambda k:min(hi[k],other_hi[k])-max(lo[k],other_lo[k]))
                cut_lo,cut_hi,stop_lo,stop_hi=(lo,hi,other_lo,other_hi) if hi[axis]-lo[axis]>other_hi[axis]-other_lo[axis] else (other_lo,other_hi,lo,hi)
                if sum((cut_lo[axis],cut_hi[axis]))<sum((stop_lo[axis],stop_hi[axis])):cut_hi[axis]=stop_lo[axis]-.03
                else:cut_lo[axis]=stop_hi[axis]+.03
    boxes=[b for b in boxes if min(v-u for u,v in zip(b[1],b[2]))>.02]
    if not boxes:raise ValueError('No hay secciones válidas para simular.')
    released=set()
    intensity=min(1,p.collapse+p.wood_damage*.35) if p.damage_enabled else 0
    for rec,lo,hi in boxes:
        seed=int(hashlib.sha256((str(p.seed)+rec['id']).encode()).hexdigest()[:8],16)
        if rec['support']=='ground' and random.Random(seed).random()<intensity:released.add(rec['id'])
    for _ in boxes:
        for rec,lo,hi in boxes:
            if rec['support'] in released:released.add(rec['id'])
    scene=bpy.data.scenes.new('Ruinas · ensayo de tabique')
    scene['ruinas_physics_lab']=True;scene['source_scene']=source_scene.name
    scene['source_signature']=signature(p);scene['physics_target']=target
    scene['physics_room']=room['id'] if room else 'primer tabique'
    scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1;scene.unit_settings.length_unit='MILLIMETERS'
    scene.gravity=(0,0,-9.81);scene.frame_end=p.physics_frames
    for rec,lo,hi in boxes:
        active=rec['support']!='jambs' if target=='PARTITION' else rec['id'] in released
        ob=body(scene,'Ensayo · '+rec['id'],lo,hi,active)
        ob['source_section']=rec['id'];ob['source_support']=rec['support']
        ob['initial_matrix']=json.dumps([list(row) for row in ob.matrix_world])
    low=[min(lo[k] for _,lo,hi in boxes) for k in range(3)];high=[max(hi[k] for _,lo,hi in boxes) for k in range(3)]
    floor_z=(3.2 if p.ground_floor else .7) if room else low[2]-.03
    body(scene,'Ensayo · suelo',[low[0]-50,low[1]-50,floor_z-2],[high[0]+50,high[1]+50,floor_z],False)
    world=scene.rigidbody_world;world.substeps_per_frame=20;world.solver_iterations=40;world.point_cache.frame_end=scene.frame_end
    scene['limitations']='Solo tabiques y suelo plano; no hay colisión con muebles, escaleras, muros ni tejado. Dinteles fijos. Revisar el resultado antes de aceptar.'
    return scene


def simulate(scene):
    'IA: Calcula secuencialmente desde el inicio para obtener un resultado evaluado; no modifica la fuente.'
    if not scene.get('ruinas_physics_lab'):raise ValueError('Abre primero una preparación física.')
    for frame in range(1,scene.frame_end+1):scene.frame_set(frame)
    scene['physics_simulated']=scene.frame_end
    runtime.physics_simulations.add(scene.as_pointer())


def release_support(scene,ob):
    'IA: En estructura completa suelta uniones; solo el laboratorio heredado retira lateralmente un apoyo entre 1 y 12 y lo libera en 13.'
    if scene.get('structural_physics'):
        from . import structural_physics
        return structural_physics.release(scene,ob)
    if not scene.get('ruinas_physics_lab') or ob is None or ob.get('source_support')!='ground':
        raise ValueError('Selecciona una sección de base del tabique en la escena de ensayo.')
    if scene.get('support_release'):
        raise ValueError('Este ensayo ya tiene una retirada de apoyo; prepara otro para cambiarla.')
    scene.frame_set(1)
    descendants={ob['source_section']}
    for _ in scene.objects:
        for piece in scene.objects:
            if piece.get('source_support') in descendants:descendants.add(piece['source_section'])
    for piece in scene.objects:
        if piece.get('source_section') in descendants:piece.rigid_body.type='ACTIVE'
    ob.rigid_body.kinematic=True;ob.rigid_body.keyframe_insert(data_path='kinematic',frame=1)
    ob.rigid_body.keyframe_insert(data_path='kinematic',frame=12)
    ob.location=Matrix(json.loads(ob['initial_matrix'])).translation
    ob.keyframe_insert(data_path='location',frame=1)
    axis=0 if ob.dimensions.x<ob.dimensions.y else 1
    ob.location[axis]-=.018;ob.keyframe_insert(data_path='location',frame=12)
    ob.rigid_body.kinematic=False;ob.rigid_body.keyframe_insert(data_path='kinematic',frame=13)
    scene['support_release']=ob['source_section'];scene['physics_simulated']=0
    runtime.physics_simulations.discard(scene.as_pointer())
    scene.timeline_markers.new('Inicio',frame=1)
    scene.timeline_markers.new('Apoyo retirado; caída por física',frame=13)
    scene.frame_set(1)


def accept(scene):
    'IA: Guarda transformaciones en mm de laboratorio calculado o reproducción aislada de tabiques; exige firma e IDs vigentes antes de regenerar.'
    if scene.get('structural_physics'):
        raise ValueError('Ensayo estructural: todavía no se reconstruye mortero imprimible. Conserva el laboratorio; no se puede aplicar al exportador antiguo.')
    source=bpy.data.scenes.get(scene.get('source_scene',''))
    if source is None or signature(source.ruin_settings)!=scene.get('source_signature'):raise ValueError('La casa ha cambiado; prepara de nuevo la física.')
    baked=scene.get('physics_result_scene') and scene.get('simulation_report')
    if not baked and (scene.as_pointer() not in runtime.physics_simulations or scene.get('physics_simulated')!=scene.frame_current):
        raise ValueError('Pulsa Simular antes de aceptar el resultado; al reabrir hay que recalcular el laboratorio.')
    dg=bpy.context.evaluated_depsgraph_get();poses={}
    for ob in scene.objects:
        if 'source_section' not in ob:continue
        delta=ob.evaluated_get(dg).matrix_world@Matrix(json.loads(ob['initial_matrix'])).inverted()
        delta.translation*=1000
        poses[ob['source_section']]=[list(row) for row in delta]
    meta.put(source,'physics_result',{'signature':scene['source_signature'],'poses':poses,'room':scene['physics_room'],'frame':scene.frame_current})
    return source


def apply_result(scene,coll,p):
    'IA: Reaplica una vez sobre geometría fresca, fuera de caché, las poses aceptadas; bloquea exportación de resultados obsoletos en lugar de perderlos silenciosamente.'
    result=meta.get(scene,'physics_result',{})
    if not result:return
    if result['signature']!=signature(p):raise ValueError('Resultado físico obsoleto: descártalo y vuelve a simular tras los cambios.')
    objects={ob['partition_section']:ob for ob in coll.objects if 'partition_section' in ob}
    if not set(result['poses'])<=objects.keys():raise ValueError('Han cambiado las secciones; descarta y repite la física.')
    for key,rows in result['poses'].items():
        ob=objects[key];delta=Matrix(rows)
        ob.data.transform(ob.matrix_world.inverted()@delta@ob.matrix_world);ob.data.update()
