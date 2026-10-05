"""Auditoría de mallas previa a preparar colisionadores, sin modificar la escena."""


def inspect(coll):
    'IA: Revisa todas las piezas y variantes, cierre, degeneración, volumen, componentes y escalas GN; no certifica contactos ni crea cuerpos físicos.'
    import bpy,bmesh
    from .export import shells
    objects=list(coll.objects);arrays=[ob for ob in objects if ob.get('ruin_instances')]
    for library in {ob['ruin_library'] for ob in arrays}:objects.extend(bpy.data.collections[library].objects)
    result={'mesh_count':0,'instances':sum(len(ob.data.vertices) for ob in arrays),'open_edges':{},'degenerate_faces':{},'nonpositive_volume':[],'multi_component_objects':{},'invalid_instance_scales':[],'precision_unresolved':{},'partition_sections':0,'physics_ready':False}
    for ob in objects:
        if ob.get('ruin_instances'):
            if any(min(v.vector)<=0 for v in ob.data.attributes['ruin_scale'].data):result['invalid_instance_scales'].append(ob.name)
            continue
        result['mesh_count']+=1
        result['partition_sections']+=int('partition_section' in ob)
        bm=bmesh.new();bm.from_mesh(ob.data)
        opened=sum(not e.is_manifold for e in bm.edges);degenerate=sum(f.calc_area()<1e-8 for f in bm.faces)
        if opened:result['open_edges'][ob.name]=opened
        if degenerate:result['degenerate_faces'][ob.name]=degenerate
        if bm.calc_volume()<=0:result['nonpositive_volume'].append(ob.name)
        parts=shells(bm)
        if len(parts)>1:result['multi_component_objects'][ob.name]=len(parts)
        if ob.get('precision_unresolved') and degenerate:result['precision_unresolved'][ob.name]=degenerate
        bm.free()
    result['remaining_work']=['Separar componentes cerámicos agrupados antes de crear colisionadores','Crear colisionadores sin los solapes intencionados de impresión','Completar grafo de apoyos y calibrar escala, margen y pasos de física','Validar contactos e interpenetraciones entre colisionadores; no cubierto por esta auditoría']
    return result
