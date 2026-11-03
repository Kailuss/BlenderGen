"""Sonda E-9d: umbral de contacto anticipado de Bullet relativo al tamaño de pieza.

Hipótesis a contrastar: el contacto convexo se crea antes de tocar si el avance relativo
por subpaso es menor que ~0,02 veces el radio envolvente de la pieza menor; entonces
Bullet anula la restitución (contacto ya «viejo») y no inyecta energía por penetración.
Se barre radio y avance por subpaso. Solo mide.
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
SUBSTEPS = 40


def body(name, x, radius, mass, restitution, shape):
    """IA: Esfera de radio dado con la forma de colisión indicada, margen nulo, sin fricción, gravedad ni amortiguación."""
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=radius, location=(x, 0, 0))
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


def trial(radius_projectile, radius_target, step_ratio, restitution, shape_projectile, shape_target):
    """IA: Fija el avance por subpaso como fracción del radio del blanco; devuelve e medida, eta y la razón de paso usada."""
    speed = step_ratio * min(radius_projectile, radius_target) * FPS * SUBSTEPS
    scene = bpy.data.scenes.new('Sonda E9d')
    bpy.context.window.scene = scene
    scene.render.fps = FPS
    scene.frame_end = FRAMES
    scene.gravity = (0, 0, 0)
    pair = math.sqrt(restitution)
    gap = radius_projectile + radius_target
    start = -gap * 1.02 - speed * 30 / FPS
    projectile = body('Proyectil', start, radius_projectile, 1, pair, shape_projectile)
    target = body('Pieza', 0, radius_target, 1, pair, shape_target)
    world = scene.rigidbody_world
    world.substeps_per_frame = SUBSTEPS
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
    result = dict(radius_projectile=radius_projectile, radius_target=radius_target,
                  shape_projectile=shape_projectile, shape_target=shape_target,
                  step_ratio=step_ratio, speed=speed, restitution_requested=restitution,
                  restitution_measured=measured, eta=vt**2 / max(incoming**2, 1e-12),
                  momentum=(vp + vt) / max(incoming, 1e-12))
    bpy.data.batch_remove(ids=tuple(scene.objects))
    bpy.data.scenes.remove(scene)
    return result


def run():
    """IA: Barre radio y avance relativo por subpaso para parejas convexas; escribe reports/impact_threshold_probe.json; no falla por resultado."""
    started = time.monotonic()
    ratios = (0.002, 0.005, 0.01, 0.015, 0.02, 0.025, 0.03, 0.04, 0.06, 0.1)
    rows = []
    for shapes in (('CONVEX_HULL', 'CONVEX_HULL'), ('SPHERE', 'CONVEX_HULL')):
        for radius in (0.25, 1.0, 4.0):
            for ratio in ratios:
                for e in (0.0, 0.3):
                    rows.append(trial(radius, radius, ratio, e, *shapes))
        for big, small in ((4.0, 0.5), (0.5, 4.0)):
            for ratio in ratios:
                rows.append(trial(big, small, ratio, 0.3, *shapes))
    commit = subprocess.run(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
    report = dict(commit=commit, blender=bpy.app.version_string, seconds=time.monotonic() - started, rows=rows,
                  scope='Choque central sin gravedad, masas iguales, 120 fps y 40 subpasos; razón = avance por subpaso / radio menor.')
    (ROOT / 'reports/impact_threshold_probe.json').write_text(json.dumps(report, indent=1), encoding='utf8')
    for r in rows:
        print('THR %-11s>%-11s Rp=%4.2f Rt=%4.2f paso/R=%.3f e=%.1f -> e_med=%+.3f eta=%.3f mom=%.4f' % (
            r['shape_projectile'], r['shape_target'], r['radius_projectile'], r['radius_target'], r['step_ratio'],
            r['restitution_requested'], r['restitution_measured'], r['eta'], r['momentum']), flush=True)
    print('SECONDS', report['seconds'], flush=True)


if __name__ == '__main__':
    run()
