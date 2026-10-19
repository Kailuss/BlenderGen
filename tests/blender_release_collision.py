"""Regresión de colisiones al liberar y selección localizada."""
import sys,json
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import ruinas_panel as addon
from ruinas_panel.services import structural_physics,height_selection


def cube(name,z,kind):
    'IA: Crea una caja de ensayo de un metro con colisión BOX para aislar liberación de errores de malla.'
    bpy.ops.mesh.primitive_cube_add(size=1,location=(0,0,z));ob=bpy.context.object;ob.name=name
    bpy.ops.rigidbody.object_add();ob.rigid_body.type=kind;ob.rigid_body.collision_shape='BOX';ob.rigid_body.friction=.8
    ob['physical_role']='stone';return ob


def run():
    'IA: Libera una caja unida sobre apoyo pasivo y exige que se asiente sin atravesarlo; comprueba zona, acumulación y familia sin tocar uniones.'
    bpy.ops.wm.read_factory_settings(use_empty=True);addon.register();scene=bpy.context.scene
    floor=cube('Apoyo',-.5,'PASSIVE');brick=cube('Ladrillo',2,'ACTIVE');other=cube('Lejano',5,'ACTIVE');other.location.x=10
    scene['structural_physics']=True
    bpy.ops.object.empty_add();joint=bpy.context.object;bpy.ops.rigidbody.constraint_add()
    c=joint.rigid_body_constraint;c.type='FIXED';c.object1=floor;c.object2=brick;c.disable_collisions=True
    world=scene.rigidbody_world;world.substeps_per_frame=40;world.solver_iterations=60;world.point_cache.frame_end=120
    scene.frame_end=120;p=scene.ruin_settings;p.physics_selection_mode='MASTER';p.physics_selection_radii=(2,2,2);p.physics_selection_percent=100
    bpy.context.view_layer.objects.active=brick
    assert height_selection.choose(scene)==[brick]
    assert c.enabled and c.disable_collisions
    p.physics_selection_mode='CURSOR';scene.cursor.location=other.location;p.physics_selection_add=True
    assert set(height_selection.choose(scene))=={brick,other}
    structural_physics.release(scene,[brick],frame=13)
    legacy='--legacy' in sys.argv
    if legacy:
        for frame in (1,12,13):
            c.disable_collisions=True;c.keyframe_insert(data_path='disable_collisions',frame=frame)
    heights=[]
    for frame in range(1,121):
        scene.frame_set(frame);deps=bpy.context.evaluated_depsgraph_get();heights.append(brick.evaluated_get(deps).matrix_world.translation.z)
        if frame==12:assert c.enabled and c.disable_collisions
        if frame==13:assert not c.enabled and c.disable_collisions==legacy
    if not legacy:
        assert min(heights)>.40,heights
        assert abs(heights[-1]-.5)<.08,heights[-1]
    report='release_collision_legacy.json' if legacy else 'release_collision.json'
    (ROOT/'reports'/report).write_text(json.dumps({'minimum_center_z':min(heights),'final_center_z':heights[-1],'frames':120,'legacy':legacy}),encoding='utf8')
    print('RELEASE_COLLISION_PASSED',flush=True)


if __name__=='__main__':run()
