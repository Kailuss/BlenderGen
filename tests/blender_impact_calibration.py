"""Banco E-9 (v2): transferencia dinámica central con las formas de colisión de la casa.

Cambios frente a la v1 (cd117b1), justificados por las sondas E-9b a E-9d:
- La v1 usaba SPHERE contra SPHERE, pareja que la casa no usa y en la que Bullet suma
  +0,16 a +0,20 a la restitución por corrección de penetración. Aquí ambos cuerpos son
  CONVEX_HULL con margen 0, como las piedras y tejas convertidas por structural_physics.
- La referencia analítica es la del régimen resuelto de Bullet (impact_spec.inelastic_collision,
  e efectiva 0), no la restitución pedida, que Bullet anula en contactos anticipados.
  La restitución pedida se conserva en el informe para que la diferencia sea visible.
- Casos de control en régimen rápido (avance/radio 0,06) para comprobar que
  impact_spec.contact_regime clasifica bien; no cuentan para la aceptación energética.
No recorta trayectorias ni relaja umbrales: eta <= 0,3, error analítico <= 15 %,
convergencia 40/160 subpasos <= 15 %, tiempo < 60 s.
"""
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

FPS = 120
FRAMES = 90
SHAPE = 'CONVEX_HULL'


def body(name, x, mass, restitution):
    """IA: Esfera de radio 1 con casco convexo y margen 0 como las piezas de la casa; sin gravedad, fricción ni amortiguación."""
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=1, location=(x, 0, 0))
    ob = bpy.context.object
    ob.name = name
    bpy.ops.rigidbody.object_add()
    rb = ob.rigid_body
    rb.collision_shape = SHAPE
    rb.mass = mass
    rb.friction = 0
    rb.restitution = restitution
    rb.linear_damping = rb.angular_damping = 0
    rb.use_margin = True
    rb.collision_margin = 0
    return ob


def linearize(ob):
    """IA: Interpolación lineal en posición y constante en el estado cinemático para acciones por capas o clásicas."""
    action = ob.animation_data.action
    curves = []
    if hasattr(action, 'layers'):
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    curves.extend(bag.fcurves)
    else:
        curves = list(action.fcurves)
    for curve in curves:
        for key in curve.keyframe_points:
            key.interpolation = 'LINEAR' if curve.data_path == 'location' else 'CONSTANT'


def trial(ratio, restitution, substeps, speed=10.):
    """IA: Proyectil guiado hasta el frame 6 y libre después; compara con el modelo inelástico y con la clasificación de régimen."""
    scene = bpy.data.scenes.new('Banco E9')
    bpy.context.window.scene = scene
    scene.render.fps = FPS
    scene.frame_end = FRAMES
    scene.gravity = (0, 0, 0)
    pair = math.sqrt(restitution)
    start = -2.05 - speed * 30 / FPS
    projectile = body('Proyectil', start, ratio, pair)
    target = body('Pieza', 0, 1, pair)
    world = scene.rigidbody_world
    world.substeps_per_frame = substeps
    world.solver_iterations = 60
    world.use_split_impulse = True
    world.point_cache.frame_end = FRAMES
    for frame in (1, 6):
        projectile.location.x = start + (frame - 1) * speed / FPS
        projectile.keyframe_insert(data_path='location', frame=frame)
        projectile.rigid_body.kinematic = True
        projectile.rigid_body.keyframe_insert(data_path='kinematic', frame=frame)
    projectile.rigid_body.kinematic = False
    projectile.rigid_body.keyframe_insert(data_path='kinematic', frame=7)
    linearize(projectile)
    xs = []
    for frame in range(1, FRAMES + 1):
        scene.frame_set(frame)
        dg = bpy.context.evaluated_depsgraph_get()
        xs.append([ob.evaluated_get(dg).matrix_world.translation.x for ob in (projectile, target)])
    incoming = (xs[19][0] - xs[14][0]) * FPS / 5
    vp, vt = ((xs[89][i] - xs[79][i]) * FPS / 10 for i in (0, 1))
    regime = impact_spec.contact_regime(incoming, 1, FPS, substeps, shapes=(SHAPE, SHAPE))
    model = impact_spec.inelastic_collision(ratio, 1, incoming)
    measured_e = (vt - vp) / incoming
    result = dict(mass_ratio=ratio, restitution_requested=restitution, substeps=substeps, speed=speed,
                  shapes=[SHAPE, SHAPE], regime=regime, model=model, split_impulse=True,
                  incoming=incoming, outgoing_projectile=vp, outgoing_target=vt,
                  restitution_measured=measured_e,
                  expected_target=model['target_speed'],
                  relative_error=abs(vt - model['target_speed']) / max(abs(model['target_speed']), 1e-12),
                  eta_target=vt**2 / max(ratio * incoming**2, 1e-12),
                  energy_ratio_total=(ratio * vp**2 + vt**2) / max(ratio * incoming**2, 1e-12),
                  momentum=(ratio * vp + vt) / max(ratio * incoming, 1e-12),
                  target_displacement=xs[-1][1])
    bpy.data.batch_remove(ids=tuple(scene.objects))
    bpy.data.scenes.remove(scene)
    return result


def run():
    """IA: Barre masas, restitución pedida y subpasos en régimen resuelto, más controles rápidos; escribe el informe y falla si algún criterio no se cumple."""
    started = time.monotonic()
    results = [trial(r, e, steps) for r in (.1, 1, 10) for e in (.1, .3) for steps in (40, 160)]
    fast_speed = .06 * FPS * 40
    controls = [trial(1, .3, 40, fast_speed), trial(1, 0., 40, fast_speed)]
    convergence = [abs(b['target_displacement'] - a['target_displacement']) / max(abs(b['target_displacement']), 1e-12)
                   for a, b in zip(results[::2], results[1::2])]
    classified = all(r['regime']['resolved'] and abs(r['restitution_measured']) <= .02 for r in results) and \
        any(not c['regime']['resolved'] and c['restitution_measured'] > .02 for c in controls)
    commit = subprocess.run(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
    dirty = bool(subprocess.run(['git', '-C', str(ROOT), 'status', '--porcelain', '--untracked-files=no'],
                                capture_output=True, text=True).stdout.strip())
    report = dict(version=2, commit=commit, dirty=dirty, blender=bpy.app.version_string,
                  seconds=time.monotonic() - started, trials=results, controls=controls, convergence=convergence,
                  scope='Colisión central libre sin gravedad entre cascos convexos de radio 1; régimen resuelto de Bullet. '
                        'No valida alcance balístico, panel cohesivo ni la casa completa.',
                  accepted_eta_max=.3, anticipation_ratio=impact_spec.BULLET_ANTICIPATION_RATIO,
                  calibration_reference='e = 0 (decisión del usuario, 2026-11-03)',
                  material_restitution_evaluated=False,
                  material_restitution_note='En régimen resuelto Bullet anula la restitución; esta configuración no evalúa restitución por material. La pedida se registra solo para mostrar que no actúa.',
                  checks=dict(analytical=all(r['relative_error'] <= .15 and r['incoming'] > 0 for r in results),
                              convergence=all(e <= .15 for e in convergence),
                              energy=all(r['energy_ratio_total'] <= 1.01 for r in results),
                              momentum=all(abs(r['momentum'] - 1) <= .01 for r in results),
                              budget=all(r['eta_target'] <= .3 + 1e-6 for r in results),
                              regime_classification=classified))
    (ROOT/'reports/impact_calibration.json').write_text(json.dumps(report, indent=2), encoding='utf8')
    for r in results + controls:
        print('E9 r=%5.1f e_ped=%.1f ss=%3d paso/R=%.4f resuelto=%d -> e_med=%+.3f eta=%.3f err=%.4f' % (
            r['mass_ratio'], r['restitution_requested'], r['substeps'], r['regime']['step_ratio'],
            r['regime']['resolved'], r['restitution_measured'], r['eta_target'], r['relative_error']), flush=True)
    print('IMPACT_CALIBRATION', json.dumps(dict(checks=report['checks'], seconds=report['seconds'],
                                                convergence=convergence)), flush=True)
    assert all(report['checks'].values()), report['checks']
    assert report['seconds'] < 60, report['seconds']


if __name__ == '__main__':
    run()
