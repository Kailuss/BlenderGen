"""Entrada de Blender secundario: simula y devuelve una reproducción sin cuerpos rígidos."""
import json
import os
import sys
import time
from pathlib import Path
import bpy
import numpy as np
from mathutils import Quaternion,Matrix,Vector


def progress(path,**values):
    'IA: Sustituye atómicamente el progreso; reintenta bloqueos breves de lectores Windows sin abortar la simulación por una actualización de estado.'
    temporary=path.with_suffix('.tmp');temporary.write_text(json.dumps(values),encoding='utf8')
    for attempt in range(8):
        try:temporary.replace(path);return
        except PermissionError:time.sleep(.01)
    # El siguiente fotograma vuelve a publicar; el resultado final se detecta por el proceso y el .blend.
    return


def run(output,path,name):
    'IA: Calcula contactos a escala ampliada solo en el hijo; conserva cada fotograma de poses originales para no interpolar a través de apoyos entre contactos.'
    scene=bpy.data.scenes[name];bpy.context.window.scene=scene
    from ruinas_panel.services import structural_physics
    structural_physics.reinforce_safety_floor(scene)
    attached=structural_physics.attach_collision_slivers(scene)
    dust=structural_physics.discard_collision_dust(scene)
    pruned=structural_physics.prune_static_constraints(scene)
    structural_physics.merge_ground(scene)
    if scene.ruin_settings.physics_adaptive_collisions:
        progress(path,stage='Optimizando colisiones')
        structural_physics.optimise_collisions(scene)
    if scene.ruin_settings.physics_sparse_constraints:structural_physics.sparsify_constraints(scene)
    from ruinas_panel.services import material_strength
    material_strength.apply(scene)
    world=scene.rigidbody_world
    if scene.ruin_settings.physics_precision=='BALANCED':world.substeps_per_frame=40;world.solver_iterations=30
    else:world.substeps_per_frame=80;world.solver_iterations=60
    objects=[o for o in scene.objects if o.type=='MESH' and not o.get('lab_decor')]
    if not scene.get('ruinas_physics_lab') or not objects:raise ValueError('Laboratorio vacío o inválido.')
    from ruinas_panel import config
    factor=config.PHYSICS_SOLVER_SCALE
    scale_solver(scene,factor)
    for ob in objects:
        if ob.rigid_body and ob.rigid_body.type=='ACTIVE':
            ob.rigid_body.use_deactivation=True
            ob.rigid_body.deactivate_linear_velocity=.002*factor
            ob.rigid_body.deactivate_angular_velocity=.1
    bpy.context.view_layer.update()
    scene.frame_set(0)
    samples=range(1,scene.frame_end+1)
    poses=np.zeros((len(samples),len(objects),10),dtype=np.float32);lookup={f:i for i,f in enumerate(samples)}
    started=time.perf_counter()
    floors=[o for o in objects if o.get('collision_floor')]
    monitored=[o for o in objects if o.rigid_body and o.rigid_body.type=='ACTIVE' and not o.get('impactor')]
    for frame in range(1,scene.frame_end+1):
        scene.frame_set(frame)
        deps=bpy.context.evaluated_depsgraph_get()
        if floors:
            floor=floors[0];floor_matrix=floor.evaluated_get(deps).matrix_world
            floor_top=max((floor_matrix@Vector(v)).z for v in floor.bound_box)
            for ob in monitored:
                matrix=ob.evaluated_get(deps).matrix_world
                if max((matrix@Vector(v)).z for v in ob.bound_box)<floor_top-.001*factor:
                    details={'frame':frame,'object':ob.name,'collision_shape':ob.rigid_body.collision_shape,'position_m':list(matrix.translation/factor),'previous_position_m':poses[lookup[frame-1],objects.index(ob),:3].tolist() if frame>1 else None,'floor_bounds_m':[[min((floor_matrix@Vector(v))[i] for v in floor.bound_box)/factor,max((floor_matrix@Vector(v))[i] for v in floor.bound_box)/factor] for i in range(3)],'local_bounds_m':[[min(v[i] for v in ob.bound_box)/factor,max(v[i] for v in ob.bound_box)/factor] for i in range(3)]}
                    path.with_name('escaped_body.json').write_text(json.dumps(details,indent=2),encoding='utf8')
                    raise ValueError('Fuga bajo el suelo de seguridad en fotograma %s: %s. No se entrega una reproducción inválida.'%(frame,ob.name))
        if frame in lookup:
            for index,ob in enumerate(objects):
                matrix=ob.evaluated_get(deps).matrix_world
                position,rotation,scale=matrix.decompose()
                poses[lookup[frame],index,:3]=position/factor;poses[lookup[frame],index,3:7]=rotation;poses[lookup[frame],index,7:]=scale
        progress(path,stage='Simulando',frame=frame,total=scene.frame_end,seconds=time.perf_counter()-started)
    result=bpy.data.scenes.new('RESULTADO · '+scene.name)
    result['ruinas_replay']=True;result['physics_result_scene']=True;result['source_scene']=scene.get('source_scene','');result['lab_scene']=name
    result['attached_collision_slivers']=json.dumps(attached)
    for key in ('source_signature','physics_room','structural_physics','masonry_lab','shake_report'):
        if key in scene:result[key]=scene[key]
    result['playback_instructions']='Simulación aislada calculada · Espacio';result.frame_end=scene.frame_end
    result.render.fps=scene.render.fps;result.render.fps_base=scene.render.fps_base
    for key in ('physics_memory_mb','physics_timeout_seconds','physics_export_voxel'):
        setattr(result.ruin_settings,key,getattr(scene.ruin_settings,key))
    result.unit_settings.system='METRIC';result.unit_settings.length_unit='MILLIMETERS'
    moving=0;meshes={}
    for index,original in enumerate(objects):
        if original.modifiers:
            mesh=bpy.data.meshes.new_from_object(original.evaluated_get(deps),depsgraph=deps)
            mesh.transform(Matrix.Scale(1/factor,4))
        else:
            if original.data not in meshes:
                mesh=original.data.copy();mesh.transform(Matrix.Scale(1/factor,4));meshes[original.data]=mesh
            mesh=meshes[original.data]
        ob=bpy.data.objects.new(original.name,mesh);result.collection.objects.link(ob)
        for key in original.keys():ob[key]=original[key]
        ob['replay_source_object']=original.name
        expiry=original.get('impact_expire_frame',0)
        ob.hide_render=original.hide_render
        if expiry:
            for key in ('hide_viewport','hide_render'):
                setattr(ob,key,key=='hide_render' and not original.get('impact_render_visible',True));ob.keyframe_insert(data_path=key,frame=1)
                setattr(ob,key,True);ob.keyframe_insert(data_path=key,frame=expiry)
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
                            for key in curve.keyframe_points:key.interpolation='CONSTANT' if curve.data_path in ('hide_viewport','hide_render') else 'LINEAR'
        if index%100==0:progress(path,stage='Guardando reproducción',objects=index,total=len(objects))
    result['simulation_report']=json.dumps({'objects':len(objects),'moving':moving,'seconds':time.perf_counter()-started,'sample_step':1,'static_constraints_omitted':pruned,'solver_scale':factor,'collision_dust_omitted':dust,'time_scale':world.time_scale,'duration_seconds':(scene.frame_end-1)*scene.render.fps_base/scene.render.fps})
    from ruinas_panel.services import lab_cameras
    lab_cameras.copy_to_replay(scene,result)
    result.frame_set(1);bpy.data.libraries.write(str(output),{result},fake_user=True)
    # Bullet debe liberar las referencias de uniones mientras sus cuerpos siguen vivos.
    bpy.data.batch_remove(ids=tuple(ob for ob in scene.objects if ob.rigid_body_constraint))
    progress(path,stage='Terminado',moving=moving,seconds=time.perf_counter()-started)


def scale_solver(scene,factor):
    'IA: Amplía mallas, traslaciones, trayectorias, gravedad e impulsos por el mismo factor; conserva masas, tiempos y escalas de objeto. Solo para copias aisladas sin padres ni modificadores.'
    objects=[o for o in scene.objects if (o.type=='MESH' or o.rigid_body_constraint) and not o.get('lab_decor')]
    if any(o.parent for o in objects):raise ValueError('El laboratorio físico debe contener piezas sin padres.')
    if any(o.type=='MESH' and o.modifiers for o in objects):raise ValueError('El laboratorio físico debe tener sus modificadores aplicados.')
    meshes={}
    for ob in objects:
        ob.location*=factor
        if ob.type=='MESH':
            if ob.data not in meshes:
                mesh=ob.data.copy();mesh.transform(Matrix.Scale(factor,4));meshes[ob.data]=mesh
            ob.data=meshes[ob.data]
        if ob.rigid_body:
            ob.rigid_body.collision_margin*=factor
            ob.rigid_body.collision_shape=ob.rigid_body.collision_shape
            ob.rigid_body.type=ob.rigid_body.type
            ob.data.update();ob.update_tag(refresh={'OBJECT','DATA'})
        if ob.rigid_body_constraint:ob.rigid_body_constraint.breaking_threshold*=factor
    actions={o.animation_data.action for o in objects if o.animation_data and o.animation_data.action}
    for action in actions:
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for curve in bag.fcurves:
                        if curve.data_path=='location':
                            for key in curve.keyframe_points:
                                key.co.y*=factor;key.handle_left.y*=factor;key.handle_right.y*=factor
    scene.gravity*=factor


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
    else:
        if len(args)>3 and args[3]=='SHAKE':
            from ruinas_panel.services import shake_physics
            request=json.loads((Path(args[0]).parent/'job.json').read_text(encoding='utf8'))
            scene=bpy.data.scenes[args[2]];bpy.context.window.scene=scene
            shake_physics.prepare(scene,request['selection'])
        run(Path(args[0]),Path(args[1]),args[2])
    # libraries.write es síncrono. Solo tras guardar con éxito se devuelve cero;
    # el SO libera el proceso aislado sin recorrer destructores nativos de Bullet.
    # Las excepciones anteriores conservan --python-exit-code 1 y no pasan por aquí.
    print('PHYSICS_WORKER_SAVED',args[0],flush=True)
    sys.stdout.flush();sys.stderr.flush();os._exit(0)
