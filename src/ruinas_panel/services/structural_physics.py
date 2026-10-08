"""Ensayo estructural sobre copias: encajes, contactos y uniones rompibles.

No convierte un resultado físico en un sólido imprimible ni mide resistencia real.
"""
import json
import time
import bpy
import bmesh
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
from .. import config, runtime
from ..geometry import primitives, instances


def role(name,materials):
    'IA: Clasifica por identidad y material antes de agrupar; el mortero y los núcleos de impresión nunca son cuerpos estructurales.'
    text=(name+' '+' '.join(materials)).lower()
    if any(s in text for s in ('mortero','núcleo')):return 'binder'
    if any(s in text for s in ('tierra','grava','peana')):return 'ground'
    if any(s in text for s in ('madera','tabique interior')):return 'wood'
    if any(s in text for s in ('teja','cerámica')):return 'tile'
    if any(s in text for s in ('hierro','latón')):return 'metal'
    return 'stone'


def components(mesh):
    'IA: Separa componentes conectados por aristas; nunca deja un paño de tejas desconectadas como un único cuerpo rígido.'
    links=[[] for _ in mesh.vertices]
    for edge in mesh.edges:
        a,b=edge.vertices;links[a].append(b);links[b].append(a)
    groups=[];seen=set()
    for start in range(len(links)):
        if start in seen:continue
        found={start};seen.add(start);stack=[start]
        while stack:
            for other in links[stack.pop()]:
                if other not in seen:seen.add(other);found.add(other);stack.append(other)
        groups.append(sorted(found))
    return groups


def extract(mesh,indices,name):
    'IA: Copia solo caras completas de una pieza y sus materiales; conserva posiciones, sin soldar piezas próximas.'
    lookup={v:i for i,v in enumerate(indices)}
    faces=[p for p in mesh.polygons if all(v in lookup for v in p.vertices)]
    result=bpy.data.meshes.new(name)
    result.from_pydata([mesh.vertices[i].co for i in indices],[],[[lookup[v] for v in p.vertices] for p in faces])
    for mat in mesh.materials:result.materials.append(mat)
    for target,source in zip(result.polygons,faces):target.material_index=source.material_index;target.use_smooth=source.use_smooth
    result.update();return result


def valid(mesh):
    'IA: Exige volumen positivo y aristas manifold antes de alimentar Bullet; devuelve volumen en mm³, cero si no es sólido.'
    bm=bmesh.new();bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    volume=bm.calc_volume()
    okay=bool(bm.faces) and all(e.is_manifold for e in bm.edges) and volume>1e-7
    if okay:bm.to_mesh(mesh)
    bm.free();return volume if okay else 0


def triangulate(mesh):
    'IA: Triangula caras no planas antes de booleanas y colisión; no rellena agujeros ni cambia coordenadas.'
    bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()


def bounds(ob):
    'IA: Cotas de la malla de trabajo en mm; las copias se normalizan a matriz identidad antes del recorte.'
    points=[v.co for v in ob.data.vertices]
    return (Vector([min(v[k] for v in points) for k in range(3)]),Vector([max(v[k] for v in points) for k in range(3)]))


def tree(ob):
    'IA: BVH de superficies reales para rechazar contactos aparentes de cajas que cruzan un vano o una teja cóncava.'
    return BVHTree.FromPolygons([v.co for v in ob.data.vertices],[list(p.vertices) for p in ob.data.polygons])


def pairs(objects,tolerance):
    'IA: Barrido espacial en X; devuelve candidatos de proximidad en los tres ejes sin comparar todas las parejas.'
    records=sorted([(bounds(o),o) for o in objects],key=lambda r:r[0][0].x)
    for i,((lo,hi),ob) in enumerate(records):
        for (low,high),other in records[i+1:]:
            if low.x>hi.x+tolerance:break
            if all(min(hi[k],high[k])+tolerance>=max(lo[k],low[k]) for k in (1,2)):
                yield ob,other,(lo,hi),(low,high)


def contact(a,b,box_a,box_b,tolerance):
    'IA: Proyecciones alternas sobre superficies desde centros y esquinas del solape; acepta solo distancia geométrica dentro de tolerancia.'
    lo=Vector([max(box_a[0][k],box_b[0][k]) for k in range(3)])
    hi=Vector([min(box_a[1][k],box_b[1][k]) for k in range(3)])
    seeds=[(lo+hi)/2]+[Vector((x,y,z)) for x in (lo.x,hi.x) for y in (lo.y,hi.y) for z in (lo.z,hi.z)]
    best=None
    for seed in seeds:
        point=seed
        for _ in range(3):
            pa=a.find_nearest(point)[0]
            if pa is None:break
            pb=b.find_nearest(pa)[0]
            if pb is None:break
            distance=(pa-pb).length
            if best is None or distance<best[0]:best=(distance,(pa+pb)/2)
            point=pb
    return best[1] if best and best[0]<=tolerance else None


def snapshot(source,coll,report):
    'IA: Materializa instancias y desagrupa rangos conservados en copias; excluye aglutinante y separa componentes sin tocar datos originales.'
    temporary=[];records=[]
    for original in source.objects:
        if original.type!='MESH':continue
        if original.get('ruin_instances'):
            clones=instances.export_copies(original,coll);temporary.extend(clones)
            keys=json.loads(original['ruin_keys'])
            records.extend((o,keys[i],list(range(len(o.data.vertices)))) for i,o in enumerate(clones))
        elif original.get('ruin_batch'):
            records.extend((original,r['name'],list(range(r['vertex_start'],r['vertex_start']+r['vertex_count']))) for r in json.loads(original['ruin_parts']))
        else:records.append((original,original.name,list(range(len(original.data.vertices)))))
    result=[]
    try:
        for original,name,indices in records:
            kind=role(name,[m.name for m in original.data.materials if m])
            if kind=='binder':report['binder_excluded']+=1;continue
            if not original.data.polygons:continue
            mesh=extract(original.data,indices,'Preparación · '+name)
            mesh.transform(original.matrix_world)
            for part,indices in enumerate(components(mesh)):
                piece=extract(mesh,indices,name)
                if not piece.polygons:bpy.data.meshes.remove(piece);continue
                triangulate(piece)
                if not valid(piece):
                    bpy.data.meshes.remove(piece);bpy.data.meshes.remove(mesh)
                    raise ValueError('Pieza no cerrada antes de física: '+name)
                ob=bpy.data.objects.new(name,piece);coll.objects.link(ob)
                ob['physical_role']=kind;ob['source_piece']=name;ob['source_component']=part
                result.append(ob)
            bpy.data.meshes.remove(mesh)
    finally:primitives.remove_objects(temporary)
    return result


def resolve(objects,report):
    'IA: Diferencias booleanas solo sobre candidatos solapados, madera antes que piedra; valida cierre y conserva piezas de la fuente intactas.'
    priority={'wood':0,'metal':1,'tile':2,'stone':3,'ground':4}
    removed=set()
    # Se procesan cajas iniciales: una diferencia solo reduce volumen.
    candidates=list(pairs(objects,-.001))
    for a,b,ba,bb in candidates:
        if a in removed or b in removed:continue
        if 'ground' in (a['physical_role'],b['physical_role']):continue
        cutter,target=sorted((a,b),key=lambda o:(priority[o['physical_role']],o.name))
        ta,tb=tree(a),tree(b)
        if not ta.overlap(tb):
            # Detectar contención completa, que no cruza superficies.
            center=(bb[0]+bb[1])/2;near,normal,_,distance=ta.find_nearest(center)
            inside=near is not None and (center-near).dot(normal)<-1e-4
            center2=(ba[0]+ba[1])/2;near2,normal2,_,_=tb.find_nearest(center2)
            inside2=near2 is not None and (center2-near2).dot(normal2)<-1e-4
            if not inside and not inside2:continue
        backup=target.data.copy();before=valid(backup)
        mod=target.modifiers.new('Encaje para física','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='MANIFOLD';mod.object=cutter
        primitives.apply_modifier(target,mod,cutter)
        if not target.data.polygons:
            removed.add(target);report['covered_pieces_removed']+=1;bpy.data.meshes.remove(backup);continue
        after=valid(target.data)
        if not after or after>before+max(.001,before*.0001):
            failed=target.data;target.data=backup.copy();bpy.data.meshes.remove(failed)
            mod=target.modifiers.new('Encaje exacto para física','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter
            primitives.apply_modifier(target,mod,cutter)
            primitives.repair_precision(target);after=valid(target.data)
            if not target.data.polygons:
                removed.add(target);report['covered_pieces_removed']+=1;bpy.data.meshes.remove(backup);continue
        if not after or after>before+max(.001,before*.0001):
            print('INVALID_JOINT',target.name,cutter.name,before,after,flush=True)
            failed=target.data;target.data=backup;bpy.data.meshes.remove(failed)
            raise ValueError('Encaje no válido entre '+target['source_piece']+' y '+cutter['source_piece'])
        if after<config.PHYSICS_RESIDUE_MAX_VOLUME and before-after>max(1e-5,before*1e-7):
            area=sum(p.area for p in target.data.polygons)
            if area and 2*after/area<config.PHYSICS_RESIDUE_MAX_THICKNESS:
                removed.add(target)
                report.setdefault('thin_residues_removed',[]).append({'piece':target['source_piece'],'volume_mm3':after,'effective_thickness_mm':2*after/area})
        if before-after>max(1e-5,before*1e-7):report['joints_cut']+=1
        bpy.data.meshes.remove(backup)
    remaining=[o for o in objects if o not in removed]
    primitives.remove_objects(list(removed))
    return remaining


def rigid(scene,ob):
    'IA: Malla cóncava real en metros con masa por volumen; terreno y pies bajo 0,65 mm anclados. No usa envolventes que tapen vanos.'
    lo,hi=bounds(ob);center=(lo+hi)/2;volume=valid(ob.data)
    ob['physical_volume_mm3']=volume
    density=config.PHYSICS_DENSITIES[ob['physical_role']]
    ob.data.transform(Matrix.Translation(-center));ob.data.transform(Matrix.Scale(.001,4));ob.matrix_world=Matrix.Translation(center*.001)
    static=ob['physical_role']=='ground' or (ob['physical_role']=='stone' and hi.z<=3.1 and lo.z<.65)
    if not ob.rigid_body:
        with bpy.context.temp_override(scene=scene,view_layer=scene.view_layers[0],object=ob,active_object=ob,selected_objects=[ob],selected_editable_objects=[ob]):
            bpy.ops.rigidbody.object_add(type='ACTIVE')
    rb=ob.rigid_body;rb.type='PASSIVE' if static else 'ACTIVE';rb.collision_shape='MESH';rb.mesh_source='BASE';rb.use_margin=True;rb.collision_margin=0
    rb.mass=max(.001,volume*1e-9*density*config.PHYSICS_MASS_SCALE);rb.friction=1;rb.restitution=0;rb.angular_damping=.5
    ob['initial_matrix']=json.dumps([list(r) for r in ob.matrix_world])


def joint(scene,a,b,point,strength,template=None):
    'IA: Unión fija entre piezas próximas, umbral de impulso escalado por masa y resistencia artística; colisiones entre socios desactivadas mientras están unidos.'
    ob=template.copy() if template else bpy.data.objects.new('Unión',None)
    ob.name='Unión · '+a.name+' / '+b.name;scene.collection.objects.link(ob);ob.location=point*.001
    ob.empty_display_type='PLAIN_AXES';ob.empty_display_size=.001;ob.hide_render=True
    if template:
        if ob.name not in scene.rigidbody_world.constraints.objects:scene.rigidbody_world.constraints.objects.link(ob)
    else:
        with bpy.context.temp_override(scene=scene,view_layer=scene.view_layers[0],object=ob,active_object=ob,selected_objects=[ob]):bpy.ops.rigidbody.constraint_add()
    c=ob.rigid_body_constraint;c.type='FIXED';c.object1=a;c.object2=b;c.disable_collisions=True
    c.use_breaking=True;c.breaking_threshold=max(.00001,(a.rigid_body.mass+b.rigid_body.mass)*9.81/24*strength)
    return ob


def prepare(source_scene):
    'IA: Construye laboratorio de edificio completo sin mortero; valida sólidos, resuelve encajes, detecta contactos reales y crea uniones. Fallar limpia solo copias.'
    from . import physics
    started=time.perf_counter();cpu_started=time.process_time();p=source_scene.ruin_settings
    source=bpy.data.collections.get(config.COLLECTION)
    if source is None or not any(o.name in source_scene.objects for o in source.objects):raise ValueError('Genera primero la casa.')
    scene=bpy.data.scenes.new('Ruinas · estructura sin mortero')
    coll=bpy.data.collections.new('Física · piezas');scene.collection.children.link(coll)
    report={'binder_excluded':0,'joints_cut':0,'covered_pieces_removed':0,'numeric_fragments_removed':0}
    try:
        objects=snapshot(source,coll,report)
        print('STRUCTURAL_SNAPSHOT',len(objects),'piezas',flush=True)
        objects=resolve(objects,report)
        print('STRUCTURAL_JOINTS',report,'CPU',round(time.process_time()-cpu_started,2),flush=True)
        # Una booleana puede desconectar una tabla o un sillar: separar otra vez.
        for ob in list(objects):
            groups=components(ob.data)
            if len(groups)<2:continue
            for index,indices in enumerate(groups):
                mesh=extract(ob.data,indices,ob.name)
                if not mesh.polygons:
                    bpy.data.meshes.remove(mesh);continue
                if not valid(mesh):
                    bm=bmesh.new();bm.from_mesh(mesh);volume=abs(bm.calc_volume());closed=all(e.is_manifold for e in bm.edges);bm.free()
                    if closed and volume<1e-6:
                        report['numeric_fragments_removed']+=1;bpy.data.meshes.remove(mesh);continue
                    print('INVALID_FRAGMENT',ob.name,len(mesh.vertices),len(mesh.polygons),flush=True)
                    raise ValueError('Fragmento degenerado después de recortar: '+ob.name)
                clone=bpy.data.objects.new(ob.name+' · fragmento',mesh);coll.objects.link(clone)
                for key in ob.keys():clone[key]=ob[key]
                clone['cut_component']=index;objects.append(clone)
            objects.remove(ob);primitives.remove_objects([ob])
        trees={o:tree(o) for o in objects};contacts=[]
        for a,b,ba,bb in pairs(objects,.8):
            if a['physical_role']==b['physical_role']=='ground':continue
            point=contact(trees[a],trees[b],ba,bb,.8)
            if point is not None:contacts.append((a,b,point))
        print('STRUCTURAL_CONTACTS',len(contacts),'CPU',round(time.process_time()-cpu_started,2),flush=True)
        if not objects:raise ValueError('No hay piezas físicas en la fuente.')
        with bpy.context.temp_override(scene=scene,view_layer=scene.view_layers[0],object=objects[0],active_object=objects[0],selected_objects=objects,selected_editable_objects=objects):
            bpy.ops.rigidbody.objects_add(type='ACTIVE')
        extent=[bounds(o) for o in objects]
        for ob in objects:rigid(scene,ob)
        lo=[min(b[0][k] for b in extent) for k in range(3)];hi=[max(b[1][k] for b in extent) for k in range(3)]
        margin=max(100,hi[2]-lo[2])*3
        floor=physics.body(scene,'Suelo de seguridad',(lo[0]-margin,lo[1]-margin,lo[2]-5),(hi[0]+margin,hi[1]+margin,lo[2]-.02),False)
        floor['collision_floor']=True;floor['physical_role']='ground';floor['source_piece']='Suelo de seguridad'
        objects.append(floor)
        template=None
        for a,b,point in contacts:
            if a.rigid_body.type==b.rigid_body.type=='PASSIVE':continue
            template=joint(scene,a,b,point,p.physics_strength,template)
        report.update(bodies=len(objects),constraints=sum(o.rigid_body_constraint is not None for o in scene.objects),roles={k:sum(o['physical_role']==k for o in objects) for k in ('wood','stone','tile','metal','ground')},seconds=round(time.perf_counter()-started,3),cpu_seconds=round(time.process_time()-cpu_started,3),faces=sum(len(o.data.polygons) for o in objects))
        connected={o for a,b,_ in contacts for o in (a,b)}
        report['unconnected']=[o.name for o in objects if o not in connected and o.rigid_body.type=='ACTIVE']
        scene['ruinas_physics_lab']=True;scene['structural_physics']=True;scene['source_scene']=source_scene.name
        scene['source_signature']=physics.signature(p);scene['physics_room']='edificio completo';scene['preparation_report']=json.dumps(report,ensure_ascii=False)
        scene['limitations']='Experimental: uniones rígidas rompibles, sin flexión ni fractura interna. Sin reconstrucción de mortero para exportar.'
        scene['mass_scale']=config.PHYSICS_MASS_SCALE
        scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1;scene.unit_settings.length_unit='MILLIMETERS'
        scene.frame_end=p.physics_frames;scene.gravity=(0,0,-9.81)
        world=scene.rigidbody_world;world.substeps_per_frame=40;world.solver_iterations=60;world.point_cache.frame_end=scene.frame_end;world.time_scale=.2
        print('STRUCTURAL_PREPARED',report,flush=True)
        return scene
    except Exception:
        primitives.remove_objects(list(scene.objects));bpy.data.scenes.remove(scene);bpy.data.collections.remove(coll)
        raise


def release(scene,ob):
    'IA: Suelta a partir del fotograma 13 las uniones de todas las piezas elegidas; no prescribe desplazamientos ni elimina su colisionador.'
    chosen=[ob] if isinstance(ob,bpy.types.Object) else list(ob or [])
    chosen={o for o in chosen if o.name in scene.objects and o.rigid_body and o.rigid_body.type=='ACTIVE'}
    if not chosen:raise ValueError('Selecciona piezas móviles del edificio.')
    if scene.get('support_release'):raise ValueError('Prepara otro ensayo para cambiar la pieza liberada.')
    scene.frame_set(1);affected=[]
    for other in scene.objects:
        c=other.rigid_body_constraint
        if c and chosen.intersection((c.object1,c.object2)):affected.append(other)
    if not affected:raise ValueError('La pieza no tiene uniones; ya está libre.')
    first=affected[0];c=first.rigid_body_constraint
    c.enabled=True;c.keyframe_insert(data_path='enabled',frame=1);c.keyframe_insert(data_path='enabled',frame=12)
    c.enabled=False;c.keyframe_insert(data_path='enabled',frame=13)
    # La misma curva booleana sirve para todas las uniones seleccionadas.
    # Evita evaluar miles de cuerpos al insertar cada fotograma por separado.
    for other in affected[1:]:
        animation=other.animation_data_create();animation.action=first.animation_data.action
        animation.action_slot=first.animation_data.action_slot
    scene['support_release']=json.dumps(sorted(o.name for o in chosen));scene['physics_simulated']=0;runtime.physics_simulations.discard(scene.as_pointer())
    scene.timeline_markers.new('Soltar uniones; caída sin trayectoria impuesta',frame=13);scene.frame_set(1)
