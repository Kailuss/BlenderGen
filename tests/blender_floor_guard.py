"""Ejercita el detector dentro del trabajador real sin una casa completa."""
import sys,tempfile
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import ruinas_panel as addon
from ruinas_panel import runtime
from ruinas_panel.services import physics_worker


def cube(scene,name,center,size,kind):
    'IA: Crea un cubo métrico de colisión sin modificadores y con dimensiones aplicadas.'
    bpy.context.window.scene=scene
    bpy.ops.mesh.primitive_cube_add(size=1,location=center)
    ob=bpy.context.object;ob.name=name;ob.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    bpy.ops.rigidbody.object_add();ob.rigid_body.type=kind
    ob.rigid_body.collision_shape='BOX';ob.rigid_body.use_margin=True;ob.rigid_body.collision_margin=0
    return ob


def run():
    'IA: El trabajador debe guardar una caída exterior y rechazar el mismo cuerpo bajo la huella interior, sin alterar el umbral de fuga.'
    addon.register();runtime.busy=True
    folder=Path(tempfile.mkdtemp(prefix='ruinas_floor_guard_'))
    for outside in (True,False):
        scene=bpy.data.scenes.new('Exterior' if outside else 'Interior')
        bpy.context.window.scene=scene;scene['ruinas_physics_lab']=True
        scene.frame_end=2;scene.ruin_settings.physics_adaptive_collisions=False
        scene.ruin_settings.physics_sparse_constraints=False
        floor=cube(scene,'Suelo',(0,0,-.25),(10,10,.5),'PASSIVE');floor['collision_floor']=True
        body=cube(scene,'Control exterior' if outside else 'Control interior',(6 if outside else 0,0,-.02),(.01,.01,.01),'ACTIVE')
        body.rigid_body.kinematic=True
        output=folder/(scene.name+'.blend');progress=folder/(scene.name+'.json')
        try:
            physics_worker.run(output,progress,scene.name)
        except ValueError as error:
            assert not outside and 'Fuga bajo el suelo' in str(error),str(error)
        else:
            assert outside and output.is_file(),'No se detectó la penetración interior.'
    print('FLOOR_WORKER_GUARD_PASSED',flush=True)


if __name__=='__main__':run()
