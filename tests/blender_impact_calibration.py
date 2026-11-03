"""Banco E-9: transferencia dinámica central y convergencia temporal."""
import json
import math
import subprocess
import sys
import time
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from ruinas_panel.services import impact_spec


def body(name, location, mass, restitution):
    """IA: Esfera convexa de radio 1 sin margen, gravedad ni amortiguación para aislar la colisión central."""
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=1, location=location)
    ob = bpy.context.object
    ob.name = name
    bpy.ops.rigidbody.object_add()
    rb = ob.rigid_body
    rb.collision_shape = 'SPHERE'
    rb.mass = mass
    rb.friction = 0
    rb.restitution = restitution
    rb.linear_damping = rb.angular_damping = 0
    rb.use_margin = True
    rb.collision_margin = 0
    return ob


def trial(ratio, restitution, substeps):
    """IA: Libera antes del contacto; aplica restitución efectiva del modelo disipativo y compara con su referencia sin recortar poses."""
    model = impact_spec.dissipative_collision(ratio, 1, 10, restitution)
    effective = model['restitution_effective']
    scene = bpy.data.scenes.new('Banco E9')
    bpy.context.window.scene = scene
    scene.render.fps = 120
    scene.frame_end = 90
    scene.gravity = (0, 0, 0)
    projectile = body('Proyectil', (-5, 0, 0), ratio, math.sqrt(effective))
    target = body('Pieza', (0, 0, 0), 1, math.sqrt(effective))
    world = scene.rigidbody_world
    world.substeps_per_frame = substeps
    world.solver_iterations = 60
    world.use_split_impulse = True
    world.point_cache.frame_end = 90
    # 10 unidades/s durante el lanzamiento; contacto previsto hacia el frame 37.
    for frame, x in ((1, -5), (13, -4)):
        projectile.location.x = x
        projectile.keyframe_insert(data_path='location', frame=frame)
        projectile.rigid_body.kinematic = True
        projectile.rigid_body.keyframe_insert(data_path='kinematic', frame=frame)
    projectile.rigid_body.kinematic = False
    projectile.rigid_body.keyframe_insert(data_path='kinematic', frame=14)
    for layer in projectile.animation_data.action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for curve in bag.fcurves:
                    for key in curve.keyframe_points:
                        key.interpolation = 'LINEAR' if curve.data_path == 'location' else 'CONSTANT'
    positions = []
    for frame in range(1, 91):
        scene.frame_set(frame)
        dg = bpy.context.evaluated_depsgraph_get()
        positions.append([list(ob.evaluated_get(dg).matrix_world.translation) for ob in (projectile, target)])
    incoming = (positions[24][0][0] - positions[19][0][0]) * 120 / 5
    outgoing = [(positions[89][i][0] - positions[79][i][0]) * 120 / 10 for i in (0, 1)]
    expected = (1 + effective) * incoming * ratio / (ratio + 1)
    result = dict(mass_ratio=ratio, restitution_pair=restitution, substeps=substeps,
                  dissipation_model=model, split_impulse=True,
                  incoming=incoming, outgoing_projectile=outgoing[0], outgoing_target=outgoing[1],
                  expected_target=expected, relative_error=abs(outgoing[1]-expected)/max(abs(expected), 1e-12),
                  eta_target=outgoing[1]**2/max(ratio*incoming**2, 1e-12),
                  energy_ratio_total=(ratio*outgoing[0]**2+outgoing[1]**2)/max(ratio*incoming**2, 1e-12),
                  target_displacement=positions[-1][1][0])
    bpy.data.batch_remove(ids=tuple(scene.objects))
    bpy.data.scenes.remove(scene)
    return result


def run():
    """IA: Barre masas y restitución con 40/160 subpasos; informa incumplimientos sin alterar umbrales ni recalcular la casa."""
    started = time.monotonic()
    results = [trial(r, e, steps) for r in (.1, 1, 10) for e in (.1, .3) for steps in (40, 160)]
    convergence = [abs(b['target_displacement']-a['target_displacement'])/max(abs(b['target_displacement']), 1e-12)
                   for a, b in zip(results[::2], results[1::2])]
    report = dict(commit=subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip(),
                  seconds=time.monotonic()-started, trials=results, convergence=convergence,
                  scope='Colisión central libre sin gravedad; desplazamiento a tiempo fijo, no alcance balístico ni panel cohesivo.',
                  accepted_eta_max=.3,
                  checks=dict(analytical=all(r['relative_error'] <= .15 and r['incoming'] > 0 for r in results),
                              convergence=all(e <= .15 for e in convergence),
                              energy=all(r['energy_ratio_total'] <= 1.01 for r in results),
                              budget=all(r['eta_target'] <= .3 + 1e-6 for r in results)))
    (ROOT/'reports/impact_calibration.json').write_text(json.dumps(report, indent=2), encoding='utf8')
    print('IMPACT_CALIBRATION', json.dumps(report), flush=True)
    assert all(report['checks'].values()), report['checks']
    assert report['seconds'] < 60, report['seconds']


if __name__ == '__main__':
    run()
