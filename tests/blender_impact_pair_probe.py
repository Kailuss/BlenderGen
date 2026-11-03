"""Sonda E-9c: restitución efectiva de Bullet por pareja de formas y velocidad.

La sonda E-9b mostró dos regímenes: primitivas (esfera, caja) con exceso constante
de restitución (+0,197 a 40 subpasos) y cascos convexos con restitución nula.
La casa del Ejercicio 02 combina proyectil SPHERE con piezas MESH y CONVEX_HULL,
así que aquí se miden esas parejas y la dependencia con la velocidad.
Solo mide; no cambia código del add-on.
"""
import json
import math
import subprocess
import time
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parents[1]
FPS = 120
FRAMES = 90


def body(name, x, mass, restitution, shape):
    """IA: Esfera de radio 1 con forma de colisión dada, margen nulo como en la casa, sin fricción, gravedad ni amortiguación."""
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=1, location=(x, 0, 0))
    ob = bpy.context.object
    ob.name = name
    bpy.ops.rigidbody.object_add()
    rb = ob.rigid_body
    rb.collision_shape = shape
    if shape == 'MESH':
        rb.mesh_source = 'BASE'
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


def trial(shape_projectile, shape_target, speed, restitution, substeps=40, ratio=1.0):
    """IA: Proyectil guiado hasta el frame 6 y libre después, contacto hacia el frame 31; devuelve e medida, exceso, momento y eta."""
    scene = bpy.data.scenes.new('Sonda E9c')
    bpy.context.window.scene = scene
    scene.render.fps = FPS
    scene.frame_end = FRAMES
    scene.gravity = (0, 0, 0)
    pair = math.sqrt(restitution)
    start = -2.05 - speed * 30 / FPS
    projectile = body('Proyectil', start, ratio, pair, shape_projectile)
    target = body('Pieza', 0, 1, pair, shape_target)
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
    measured = (vt - vp) / incoming if incoming > 0 else float('nan')
    result = dict(projectile_shape=shape_projectile, target_shape=shape_target, speed=speed,
                  substeps=substeps, ratio=ratio, restitution_requested=restitution,
                  incoming=incoming, outgoing_projectile=vp, outgoing_target=vt,
                  restitution_measured=measured, excess=measured - restitution,
                  momentum=(ratio * vp + vt) / max(ratio * incoming, 1e-12),
                  eta=vt**2 / max(ratio * incoming**2, 1e-12),
                  target_moved=abs(xs[-1][1]) > 1e-6)
    bpy.data.batch_remove(ids=tuple(scene.objects))
    bpy.data.scenes.remove(scene)
    return result


def run():
    """IA: Barre parejas de formas de la casa, velocidades y restitución; escribe reports/impact_pair_probe.json; es una sonda y no falla por resultado."""
    started = time.monotonic()
    pairs = [('SPHERE', 'SPHERE'), ('SPHERE', 'CONVEX_HULL'), ('SPHERE', 'MESH'),
             ('CONVEX_HULL', 'CONVEX_HULL'), ('CONVEX_HULL', 'MESH'), ('MESH', 'MESH')]
    rows = []
    for a, b in pairs:
        for speed in (0.5, 2, 10, 50, 200):
            for e in (0.0, 0.3):
                rows.append(trial(a, b, speed, e))
    steps = [trial(a, b, 10, .3, s) for a, b in pairs for s in (10, 160, 400)]
    commit = subprocess.run(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
    report = dict(commit=commit, blender=bpy.app.version_string, seconds=time.monotonic() - started,
                  rows=rows, substeps=steps,
                  scope='Choque central libre sin gravedad entre esferas de radio 1 con formas de colisión de la casa; margen 0.')
    (ROOT / 'reports/impact_pair_probe.json').write_text(json.dumps(report, indent=1), encoding='utf8')
    for r in rows + steps:
        print('PAIR %-11s>%-11s v=%6.1f ss=%3d e=%.1f -> e_med=%+.3f exceso=%+.3f mom=%.4f eta=%.3f mov=%d' % (
            r['projectile_shape'], r['target_shape'], r['speed'], r['substeps'], r['restitution_requested'],
            r['restitution_measured'], r['excess'], r['momentum'], r['eta'], r['target_moved']), flush=True)
    print('SECONDS', report['seconds'], flush=True)


if __name__ == '__main__':
    run()
