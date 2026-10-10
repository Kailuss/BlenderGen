"""Exportación del fotograma físico: unión volumétrica y STL en milímetros."""
import json,struct
from pathlib import Path
import bpy,bmesh,numpy as np
from mathutils import Matrix


def triangles(mesh):
    'IA: Obtiene triángulos float32, suelda coincidencias a 0,00001 mm y descarta área nula sin convertir millones de caras a BMesh.'
    mesh.calc_loop_triangles()
    points=np.empty((len(mesh.vertices),3),dtype=np.float32);mesh.vertices.foreach_get('co',points.ravel())
    faces=np.empty((len(mesh.loop_triangles),3),dtype=np.int32);mesh.loop_triangles.foreach_get('vertices',faces.ravel())
    _,first,inverse=np.unique(np.round(points,5),axis=0,return_index=True,return_inverse=True)
    points=points[first];faces=inverse[faces].astype(np.int32);del first,inverse
    keep=np.ones(len(faces),dtype=bool);volume=0.
    for start in range(0,len(faces),100000):
        block=points[faces[start:start+100000]].astype(np.float64)
        cross=np.cross(block[:,1]-block[:,0],block[:,2]-block[:,0]);valid=np.linalg.norm(cross,axis=1)>2e-12
        keep[start:start+len(block)]=valid
        volume+=np.einsum('ij,ij->i',block[valid,0],np.cross(block[valid,1],block[valid,2])).sum()/6
    faces=faces[keep]
    if not len(faces) or volume<=0:raise ValueError('El resultado no tiene volumen positivo exportable.')
    # La orientación de cada pareja de aristas debe ser opuesta.
    edges=np.concatenate((faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]))
    direction=np.where(edges[:,0]<edges[:,1],1,-1).astype(np.int8);edges.sort(axis=1)
    _,inverse,counts=np.unique(edges,axis=0,return_inverse=True,return_counts=True)
    if not np.all(counts==2) or not np.all(np.bincount(inverse,weights=direction)==0):raise ValueError('El resultado no es una malla cerrada orientada; no se escribe STL.')
    return points,faces,float(volume)


def export(scene,path,voxel=.35):
    'IA: Fusiona copias de poses en mm a resolución explícita; permite escombros separados, excluye suelo y proyectiles y valida STL por bloques sin BMesh de alta densidad.'
    scene.frame_set(scene.frame_current);bpy.context.window.scene=scene
    deps=bpy.context.evaluated_depsgraph_get();combined=bmesh.new();pieces=0
    try:
        for ob in scene.objects:
            if ob.type!='MESH' or ob.get('collision_floor') or ob.get('impactor'):continue
            evaluated=ob.evaluated_get(deps);mesh=bpy.data.meshes.new_from_object(evaluated,depsgraph=deps)
            mesh.transform(Matrix.Scale(1000,4)@evaluated.matrix_world)
            combined.from_mesh(mesh);bpy.data.meshes.remove(mesh);pieces+=1
        if not pieces:raise ValueError('No hay geometría física para exportar.')
        mesh=bpy.data.meshes.new('Resultado físico en mm');combined.to_mesh(mesh)
    finally:combined.free()
    print('EXPORT_COMBINED',pieces,len(mesh.polygons),flush=True)
    result=bpy.data.scenes.new('EXPORTACIÓN · resultado físico');result.unit_settings.system='METRIC';result.unit_settings.scale_length=.001
    result['ruinas_replay']=True;result['source_scene']=scene.get('source_scene','');result['lab_scene']=scene.get('lab_scene','');result['playback_instructions']='STL validado · geometría en mm'
    ob=bpy.data.objects.new('Sólido físico · mm',mesh);result.collection.objects.link(ob)
    bpy.context.window.scene=result;result.view_layers[0].objects.active=ob;ob.select_set(True)
    mod=ob.modifiers.new('Fusión volumétrica explícita','REMESH');mod.mode='VOXEL';mod.voxel_size=voxel
    bpy.ops.object.modifier_apply(modifier=mod.name)
    print('EXPORT_REMESH',len(ob.data.polygons),flush=True)
    points,faces,volume=triangles(ob.data)
    old=ob.data;ob.data=bpy.data.meshes.new('Resultado físico validado');bpy.data.meshes.remove(old)
    mesh=ob.data;mesh.vertices.add(len(points));mesh.vertices.foreach_set('co',points.ravel())
    mesh.loops.add(faces.size);mesh.loops.foreach_set('vertex_index',faces.ravel())
    mesh.polygons.add(len(faces));mesh.polygons.foreach_set('loop_start',np.arange(0,faces.size,3,dtype=np.int32));mesh.polygons.foreach_set('loop_total',np.full(len(faces),3,dtype=np.int32));mesh.update(calc_edges=True)
    target=Path(path);temporary=target.with_suffix('.stl.tmp');target.parent.mkdir(parents=True,exist_ok=True)
    dtype=np.dtype([('normal','<f4',(3,)),('vertices','<f4',(3,3)),('attribute','<u2')])
    with temporary.open('wb') as stream:
        stream.write(b'Ruinas physical result in mm'.ljust(80,b'\0'));stream.write(struct.pack('<I',len(faces)))
        for start in range(0,len(faces),100000):
            block=points[faces[start:start+100000]];normals=np.cross(block[:,1]-block[:,0],block[:,2]-block[:,0]);normals/=np.linalg.norm(normals,axis=1)[:,None]
            records=np.zeros(len(block),dtype=dtype);records['normal']=normals;records['vertices']=block;records.tofile(stream)
    temporary.replace(target)
    report={'pieces':pieces,'triangles':len(faces),'voxel_mm':voxel,'volume_mm3':volume,'closed':True,'path':str(target),'frame':scene.frame_current}
    ob['physical_export_report']=json.dumps(report);result['physical_export_report']=json.dumps(report)
    target.with_suffix('.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    return result