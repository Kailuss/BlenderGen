"""Banco de panel con gravedad (B1-C6 paso 2; V0 del Ejercicio 03): muro seco de 10 × 20 piedras.

Unidades del solver como el laboratorio: metros de modelo × 100 (1 u = 1 cm de modelo) y
gravedad × 100. Piedras de 17 × 7,3 × 13,9 mm de modelo (medianas de 03e), CONVEX_HULL y
margen 0 como en la casa, sin uniones: mide solo contacto y gravedad.

Variantes (misma bola de 20 mm de radio, densidad 3,5 veces la piedra, a 0,326 m/s):
- A · actual: bola guiada a través del muro hasta 6 fotogramas después del contacto, 40 subpasos.
- B · propuesta: bola dinámica soltada antes del contacto; subpasos de impact_spec.contact_regime
  para la velocidad de la bola y el radio de la piedra.
- C · B y además subpasos para la velocidad de caída desde lo alto del muro.

Criterios (orden B1-C5, sección 4): deriva en reposo < 0,1 mm; lanzamiento horizontal
p99 <= 1,5 · v_bola; eta (energía cinética horizontal de lanzamiento / energía de la bola) <= 0,3;
ninguna fuga bajo el suelo; tiempo total < 60 s. Se exigen en B y C; A se informa como control.
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

SCALE = 100.0
FPS = 24
FRAMES = 96
SETTLE = 24
STONE = (1.70, 0.73, 1.39)
GAP = 0.02
COURSES, PER_COURSE = 10, 20
BALL_RADIUS = 2.0
BALL_SPEED = 0.326 * SCALE
DENSITY_STONE = 1.0
DENSITY_BALL = 3.5
G = 9.81 * SCALE


def hull_box(name, size, location, passive=False):
    """IA: Caja cerrada con forma de colisión CONVEX_HULL y margen 0; masa = volumen × densidad de piedra."""
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    ob = bpy.context.object
    ob.name = name
    ob.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bpy.ops.rigidbody.object_add(type='PASSIVE' if passive else 'ACTIVE')
    rb = ob.rigid_body
    rb.collision_shape = 'CONVEX_HULL'
    rb.use_margin = True
    rb.collision_margin = 0
    rb.friction = .8
    rb.restitution = 0
    rb.linear_damping = rb.angular_damping = .04
    rb.use_deactivation = False
    rb.mass = size[0] * size[1] * size[2] * DENSITY_STONE
    return ob


def build(scene):
    """IA: Suelo pasivo y muro de hiladas alternas desplazadas media piedra; devuelve la lista de piedras."""
    hull_box('Suelo', (80, 80, 1), (0, 0, -.5), passive=True)
    stones = []
    width = PER_COURSE * (STONE[0] + GAP)
    for course in range(COURSES):
        offset = (STONE[0] + GAP) / 2 if course % 2 else 0
        z = STONE[2] / 2 + course * (STONE[2] + GAP)
        for index in range(PER_COURSE):
            x = -width / 2 + offset + (index + .5) * (STONE[0] + GAP)
            stones.append(hull_box(f'Piedra {course:02d}.{index:02d}', STONE, (x, 0, z)))
    return stones


def ball(scene, release_frame, contact_frame):
    """IA: Bola convexa guiada en línea recta hacia el muro (+Y) hasta release_frame y dinámica después."""
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=BALL_RADIUS)
    ob = bpy.context.object
    ob.name = 'Bola'
    bpy.ops.rigidbody.object_add(type='ACTIVE')
    rb = ob.rigid_body
    rb.collision_shape = 'CONVEX_HULL'
    rb.use_margin = True
    rb.collision_margin = 0
    rb.friction = .8
    rb.restitution = 0
    rb.linear_damping = rb.angular_damping = 0
    rb.use_deactivation = False
    rb.mass = 4 / 3 * math.pi * BALL_RADIUS**3 * DENSITY_BALL
    z = COURSES * (STONE[2] + GAP) / 2
    face = -STONE[1] / 2 - BALL_RADIUS
    y = lambda frame: face - (contact_frame - frame) * BALL_SPEED / FPS
    for frame in (1, release_frame):
        ob.location = (0, y(frame), z)
        ob.keyframe_insert(data_path='location', frame=frame)
        rb.kinematic = True
        rb.keyframe_insert(data_path='kinematic', frame=frame)
    rb.kinematic = False
    rb.keyframe_insert(data_path='kinematic', frame=release_frame + 1)
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
    return ob


def variant(label, substeps, release_offset):
    """IA: Construye la escena, simula y mide deriva en reposo, lanzamientos, eta, fugas y tiempo; release_offset < 0 suelta antes del contacto."""
    scene = bpy.data.scenes.new('Banco panel ' + label)
    bpy.context.window.scene = scene
    scene.render.fps = FPS
    scene.frame_start, scene.frame_end = 1, FRAMES
    bpy.ops.rigidbody.world_add()
    scene.gravity = (0, 0, -G)
    world = scene.rigidbody_world
    world.substeps_per_frame = substeps
    world.solver_iterations = 60
    world.use_split_impulse = True
    world.point_cache.frame_start, world.point_cache.frame_end = 1, FRAMES
    stones = build(scene)
    contact = SETTLE + 8
    projectile = ball(scene, contact + release_offset, contact)
    started = time.monotonic()
    track = stones + [projectile]
    xs = []
    for frame in range(1, FRAMES + 1):
        scene.frame_set(frame)
        dg = bpy.context.evaluated_depsgraph_get()
        xs.append([tuple(ob.evaluated_get(dg).matrix_world.translation) for ob in track])
    seconds = time.monotonic() - started
    dist = lambda a, b: math.dist(a, b)
    drift = max(dist(xs[SETTLE - 1][i], xs[0][i]) for i in range(len(stones))) * 10
    vel = lambda f, i, axes: math.dist([xs[f + 1][i][k] for k in axes], [xs[f - 1][i][k] for k in axes]) * FPS / 2
    launch, up, moved = [], 0, 0
    for i in range(len(stones)):
        start = next((f for f in range(SETTLE, FRAMES) if dist(xs[f][i], xs[SETTLE - 1][i]) > .02), None)
        if start is None:
            continue
        moved += 1
        window = range(max(start, 1), min(start + 3, FRAMES - 1))
        launch.append((i, max(vel(f, i, (0, 1)) for f in window)))
        if max((xs[f + 1][i][2] - xs[f - 1][i][2]) * FPS / 2 for f in window) > BALL_SPEED:
            up += 1
    speeds = sorted(v for _, v in launch)
    p99 = speeds[min(len(speeds) - 1, int(.99 * len(speeds)))] if speeds else 0.
    mass = {i: stones[i].rigid_body.mass for i in range(len(stones))}
    ke_ball = .5 * projectile.rigid_body.mass * BALL_SPEED**2
    eta = sum(.5 * mass[i] * v**2 for i, v in launch) / ke_ball
    escaped = sum(1 for i in range(len(stones)) if min(x[i][2] for x in xs) < -1)
    regime = impact_spec.contact_regime(BALL_SPEED, math.dist((0, 0, 0), [s / 2 for s in STONE]), FPS, substeps)
    report = dict(variant=label, substeps=substeps, release_frame=contact + release_offset, contact_frame=contact,
                  settle_drift_mm=drift, moved=moved, launch_p99_over_v=p99 / BALL_SPEED,
                  launch_max_over_v=(speeds[-1] / BALL_SPEED) if speeds else 0., upward_faster_than_ball=up,
                  eta_horizontal=eta, escaped=escaped, seconds=seconds, ball_regime=regime)
    bpy.data.batch_remove(ids=tuple(scene.objects))
    bpy.data.scenes.remove(scene)
    return report


def run():
    """IA: Calcula los subpasos de B y C con contact_regime, simula A, B y C, escribe reports/panel_bench.json y falla si B o C incumplen."""
    started = time.monotonic()
    radius = math.dist((0, 0, 0), [s / 2 for s in STONE])
    sub_ball = impact_spec.contact_regime(BALL_SPEED, radius, FPS, 1)['substeps_required']
    fall = math.sqrt(2 * G * COURSES * (STONE[2] + GAP))
    sub_fall = impact_spec.contact_regime(fall, radius, FPS, 1)['substeps_required']
    results = [variant('A', 40, 6), variant('B', max(sub_ball, 10), -2), variant('C', max(sub_ball, sub_fall, 10), -2)]
    checks = {}
    for r in results[1:]:
        checks[r['variant']] = dict(settle=r['settle_drift_mm'] < .1, launch=r['launch_p99_over_v'] <= 1.5,
                                    eta=r['eta_horizontal'] <= .3, escaped=r['escaped'] == 0)
    commit = subprocess.run(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
    report = dict(commit=commit, blender=bpy.app.version_string, seconds=time.monotonic() - started,
                  stones=COURSES * PER_COURSE, ball_speed_model_m_s=BALL_SPEED / SCALE, fall_speed_model_m_s=fall / SCALE,
                  substeps_ball=sub_ball, substeps_fall=sub_fall, variants=results, checks=checks,
                  scope='Muro seco sin uniones sobre suelo; mide contacto, gravedad y lanzamiento, no resistencia ni fractura.')
    (ROOT/'reports/panel_bench.json').write_text(json.dumps(report, indent=2), encoding='utf8')
    for r in results:
        print('PANEL %s ss=%3d suelta=f%d deriva=%.3fmm movidas=%3d p99/v=%.2f max/v=%.2f eta=%.3f arriba=%d fugas=%d t=%.1fs' % (
            r['variant'], r['substeps'], r['release_frame'], r['settle_drift_mm'], r['moved'], r['launch_p99_over_v'],
            r['launch_max_over_v'], r['eta_horizontal'], r['upward_faster_than_ball'], r['escaped'], r['seconds']), flush=True)
    print('PANEL_BENCH', json.dumps(dict(checks=checks, seconds=report['seconds'], substeps_ball=sub_ball, substeps_fall=sub_fall)), flush=True)
    assert all(all(c.values()) for c in checks.values()), checks
    assert report['seconds'] < 60, report['seconds']


if __name__ == '__main__':
    run()
