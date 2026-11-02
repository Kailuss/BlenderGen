"""Trabajador de ensayo que deja poses de control durante el cálculo completo."""
import sys,inspect,json,os
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import bpy,ruinas_panel as addon
from mathutils import Matrix
from ruinas_panel.services import physics_worker
addon.register()
args=sys.argv[sys.argv.index('--')+1:]
original=physics_worker.progress


def discard_redundant_holds(scene):
    'IA: Solo en este ensayo, retira uniones cuyo intervalo habilitado nunca coincide con un socio dinámico; comprueba claves booleanas constantes y conserva cualquier unión que sí ejerza fuerza.'
    def mask(ob,path,value):
        'IA: Obtiene una máscara temporal exacta para propiedades booleanas constantes con claves enteras.'
        curve=None
        if ob.animation_data and ob.animation_data.action:
            for layer in ob.animation_data.action.layers:
                for strip in layer.strips:
                    for bag in strip.channelbags:
                        for candidate in bag.fcurves:
                            if candidate.data_path==path:curve=candidate
        if curve:
            assert all(k.interpolation=='CONSTANT' and abs(k.co.x-round(k.co.x))<1e-6 for k in curve.keyframe_points),(ob.name,path)
            return sum(1<<f for f in range(1,scene.frame_end+1) if curve.evaluate(f)>.5)
        return full if value else 0
    full=sum(1<<f for f in range(1,scene.frame_end+1));dynamic={};remove=[]
    for ob in scene.objects:
        if ob.rigid_body:
            dynamic[ob]=0 if ob.rigid_body.type=='PASSIVE' else full ^ mask(ob,'rigid_body.kinematic',ob.rigid_body.kinematic)
    for ob in scene.objects:
        c=ob.rigid_body_constraint
        if not c:continue
        enabled=mask(ob,'rigid_body_constraint.enabled',c.enabled)
        if not enabled & (dynamic.get(c.object1,full)|dynamic.get(c.object2,full)):remove.append(ob)
    count=len(remove)
    if remove:bpy.data.batch_remove(ids=tuple(remove))
    scene['directed_redundant_constraints_omitted']=count
    print('REDUNDANT_HOLDS_OMITTED',count,flush=True)

def observed(path,**status):
    'IA: Conserva poses de diagnóstico, sin tocar escena ni solver; el llamador es exclusivamente physics_worker.run.'
    original(path,**status)
    frame=status.get('frame')
    if status.get('stage')=='Simulando' and frame in (30,48,60,90,130,180,240):
        state=inspect.currentframe().f_back.f_locals
        np.savez_compressed(ROOT/f'reports/shrapnel_poses_{frame}.npz',poses=state['poses'][:frame],names=np.array([o.name for o in state['objects']]))


def merge_passive_collision(scene):
    'IA: Agrupa exactamente las superficies pasivas constantes, salvo el suelo de seguridad; conserva cada objeto visible sin cuerpo y un proxy invisible de colisión.'
    bpy.context.window.scene=scene;scene.frame_set(1)
    passive=[o for o in scene.objects if o.rigid_body and o.rigid_body.type=='PASSIVE' and not o.get('collision_floor')]
    assert all(not o.animation_data for o in passive),'No se agrupan obstáculos animados.'
    if not passive:return
    verts=[];faces=[]
    for ob in passive:
        offset=len(verts);transform=ob.matrix_world
        verts.extend(transform@v.co for v in ob.data.vertices)
        faces.extend(tuple(offset+i for i in p.vertices) for p in ob.data.polygons)
    mesh=bpy.data.meshes.new('Colisión pasiva conjunta');mesh.from_pydata(verts,[],faces);mesh.update()
    proxy=passive[0].copy();proxy.data=mesh;proxy.animation_data_clear();proxy.matrix_world=Matrix.Identity(4)
    proxy.name='Colisión pasiva conjunta';scene.collection.objects.link(proxy)
    if proxy.name not in scene.rigidbody_world.collection.objects:scene.rigidbody_world.collection.objects.link(proxy)
    for key in list(proxy.keys()):del proxy[key]
    proxy['lab_collision_proxy']=True;proxy['physical_role']='static_proxy';proxy.hide_render=True
    proxy.rigid_body.type='PASSIVE';proxy.rigid_body.collision_shape='MESH';proxy.rigid_body.mesh_source='BASE'
    proxy.rigid_body.use_margin=True;proxy.rigid_body.collision_margin=0
    with bpy.context.temp_override(scene=scene,view_layer=scene.view_layers[0],selected_objects=passive,selected_editable_objects=passive,active_object=passive[0],object=passive[0]):
        bpy.ops.rigidbody.objects_remove()
    assert all(o.rigid_body is None for o in passive)
    assert proxy.rigid_body and proxy.rigid_body.type=='PASSIVE'
    print('PASSIVE_COLLISION_MERGED',len(passive),len(mesh.polygons),flush=True)
physics_worker.progress=observed
original_scale_solver=physics_worker.scale_solver
def precise_scale_solver(scene,factor):
    'IA: Este ensayo usa 160 subpasos y 60 iteraciones para resolver impactos sobre fragmentos de menos de 1 mm; conserva gravedad, tiempo y detector de fugas.'
    original_scale_solver(scene,factor)
    scene.rigidbody_world.substeps_per_frame=160
    scene.rigidbody_world.solver_iterations=60
    print('DIRECTED_SOLVER',160,60,flush=True)
physics_worker.scale_solver=precise_scale_solver
discard_redundant_holds(bpy.data.scenes[args[2]])
merge_passive_collision(bpy.data.scenes[args[2]])
physics_worker.run(Path(args[0]),Path(args[1]),args[2])
print('OBSERVED_WORKER_SAVED',flush=True)
sys.stdout.flush();os._exit(0)
