"""Entrada de Blender secundario: simula y devuelve una reproducción sin cuerpos rígidos."""
import json
import sys
import time
from pathlib import Path
import bpy
import numpy as np
from mathutils import Quaternion


def progress(path,**values):
    'IA: Sustituye atómicamente el progreso para que la interfaz nunca lea un JSON incompleto.'
    temporary=path.with_suffix('.tmp');temporary.write_text(json.dumps(values),encoding='utf8');temporary.replace(path)


def run(output,path,name):
    'IA: Evalúa todos los fotogramas en un proceso aislado y conserva poses muestreadas cada cuatro; no exporta colisionadores ni altera el laboratorio.'
    scene=bpy.data.scenes[name];bpy.context.window.scene=scene
    from ruinas_panel.services import structural_physics
    structural_physics.merge_ground(scene)
    if scene.ruin_settings.physics_adaptive_collisions:
        progress(path,stage='Optimizando colisiones')
        structural_physics.optimise_collisions(scene)
    if scene.ruin_settings.physics_sparse_constraints:structural_physics.sparsify_constraints(scene)
    world=scene.rigidbody_world
    if scene.ruin_settings.physics_precision=='BALANCED':world.substeps_per_frame=12;world.solver_iterations=30
    else:world.substeps_per_frame=40;world.solver_iterations=60
    objects=[o for o in scene.objects if o.type=='MESH']
    if not scene.get('ruinas_physics_lab') or not objects:raise ValueError('Laboratorio vacío o inválido.')
    samples=sorted(set(range(1,scene.frame_end+1,4))|{scene.frame_end})
    poses=np.zeros((len(samples),len(objects),10),dtype=np.float32);lookup={f:i for i,f in enumerate(samples)}
    started=time.perf_counter()
    for frame in range(1,scene.frame_end+1):
        scene.frame_set(frame)
        deps=bpy.context.evaluated_depsgraph_get()
        if frame in lookup:
            for index,ob in enumerate(objects):
                matrix=ob.evaluated_get(deps).matrix_world
                position,rotation,scale=matrix.decompose()
                poses[lookup[frame],index,:3]=position;poses[lookup[frame],index,3:7]=rotation;poses[lookup[frame],index,7:]=scale
        progress(path,stage='Simulando',frame=frame,total=scene.frame_end,seconds=time.perf_counter()-started)
    result=bpy.data.scenes.new('RESULTADO · '+scene.name)
    result['ruinas_replay']=True;result['physics_result_scene']=True;result['source_scene']=scene.get('source_scene','');result['lab_scene']=name
    for key in ('source_signature','physics_room','structural_physics','masonry_lab'):
        if key in scene:result[key]=scene[key]
    result['playback_instructions']='Simulación aislada calculada · Espacio';result.frame_end=scene.frame_end
    result.render.fps=scene.render.fps;result.render.fps_base=scene.render.fps_base
    result.unit_settings.system='METRIC';result.unit_settings.length_unit='MILLIMETERS'
    moving=0
    for index,original in enumerate(objects):
        mesh=bpy.data.meshes.new_from_object(original.evaluated_get(deps),depsgraph=deps) if original.modifiers else original.data
        ob=bpy.data.objects.new(original.name,mesh);result.collection.objects.link(ob)
        for key in original.keys():ob[key]=original[key]
        ob.rotation_mode='QUATERNION'
        track=poses[:,index];ob.location=track[0,:3];ob.rotation_quaternion=Quaternion(track[0,3:7]);ob.scale=track[0,7:]
        changed=np.max(np.linalg.norm(track[:,:3]-track[0,:3],axis=1))>.00002 or np.min(np.abs(track[:,3:7]@track[0,3:7]))<.99999 or np.max(np.abs(track[:,7:]-track[0,7:]))>1e-6
        if changed:
            moving+=1
            for frame,pose in zip(samples,track):
                ob.location=pose[:3];ob.rotation_quaternion=Quaternion(pose[3:7]);ob.scale=pose[7:]
                ob.keyframe_insert(data_path='location',frame=frame);ob.keyframe_insert(data_path='rotation_quaternion',frame=frame);ob.keyframe_insert(data_path='scale',frame=frame)
            action=ob.animation_data.action
            for layer in action.layers:
                for strip in layer.strips:
                    for bag in strip.channelbags:
                        for curve in bag.fcurves:
                            for key in curve.keyframe_points:key.interpolation='LINEAR'
        if index%100==0:progress(path,stage='Guardando reproducción',objects=index,total=len(objects))
    result['simulation_report']=json.dumps({'objects':len(objects),'moving':moving,'seconds':time.perf_counter()-started,'sample_step':4})
    result.frame_set(1);bpy.data.libraries.write(str(output),{result},fake_user=True)
    progress(path,stage='Terminado',moving=moving,seconds=time.perf_counter()-started)


if __name__=='__main__':
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
    import ruinas_panel
    ruinas_panel.register()
    args=sys.argv[sys.argv.index('--')+1:]
    if len(args)>3 and args[3]=='PREPARE':
        from ruinas_panel.services import physics
        scene=bpy.data.scenes[args[2]];bpy.context.window.scene=scene
        progress(Path(args[1]),stage='Preparando geometría y contactos')
        result=physics.prepare(scene)
        bpy.data.libraries.write(args[0],{result},fake_user=True)
    elif len(args)>3 and args[3]=='EXPORT':
        from ruinas_panel.services import physical_export
        scene=bpy.data.scenes[args[2]]
        progress(Path(args[1]),stage='Fusionando para STL')
        result=physical_export.export(scene,args[4],scene.ruin_settings.physics_export_voxel)
        bpy.data.libraries.write(args[0],{result},fake_user=True)
    else:run(Path(args[0]),Path(args[1]),args[2])
