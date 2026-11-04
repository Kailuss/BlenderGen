"""Comprueba que scale_solver escala los umbrales de rotura por el factor del solver y por 40/subpasos."""
import sys
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from ruinas_panel import config
from ruinas_panel.services import physics_worker


def run():
    """IA: Dos cubos con unión FIXED; para 40, 80 y 400 subpasos el umbral queda multiplicado por 100·40/subpasos."""
    for substeps in (40, 80, 400):
        scene = bpy.data.scenes.new('Umbral %d' % substeps)
        bpy.context.window.scene = scene
        bpy.ops.rigidbody.world_add()
        scene.rigidbody_world.substeps_per_frame = substeps
        cubes = []
        for x in (0, 1):
            bpy.ops.mesh.primitive_cube_add(size=1, location=(x, 0, 0))
            bpy.ops.rigidbody.object_add()
            cubes.append(bpy.context.object)
        joint = bpy.data.objects.new('Unión', None)
        scene.collection.objects.link(joint)
        with bpy.context.temp_override(object=joint, active_object=joint, selected_objects=[joint]):
            bpy.ops.rigidbody.constraint_add(type='FIXED')
        c = joint.rigid_body_constraint
        c.object1, c.object2 = cubes
        c.use_breaking = True
        c.breaking_threshold = 2.0
        physics_worker.scale_solver(scene, 100)
        expected = 2.0 * 100 * config.THRESHOLD_REFERENCE_SUBSTEPS / substeps
        assert abs(c.breaking_threshold - expected) < 1e-4 * expected, (substeps, c.breaking_threshold, expected)
        print('WORKER_THRESHOLD', substeps, c.breaking_threshold, flush=True)
    print('WORKER_THRESHOLD_PASSED', flush=True)


if __name__ == '__main__':
    run()
