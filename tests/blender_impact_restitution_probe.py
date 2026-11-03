"""Sonda E-9b: origen del exceso de restitución de Bullet en colisión central.

El banco E-9 mide e_medido = e_pedido + ~0,2 (40 subpasos) con y sin split impulse
y con momento conservado. Hipótesis: corrección de penetración por velocidad (ERP)
en contactos poco profundos, que Bullet no pasa al split impulse por encima de su
umbral de penetración. Esta sonda barre forma, margen, subpasos y split impulse.
No toca código del add-on ni umbrales: solo mide.
"""
import json
import math
import subprocess
import sys
import time
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parents[1]
FPS = 120
FRAMES = 90
SPEED = 10.0


def body(name, x, mass, restitution, shape, margin):
    """IA: Cuerpo de semitamaño 1 sin gravedad, fricción ni amortiguación; forma y margen explícitos para aislar el contacto."""
    if shape == 'BOX':
        bpy.ops.mesh.primitive_cube_add(size=2, location=(x, 0, 0))
    else:
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=1, location=(x, 0, 0))
    ob = bpy.context.object
    ob.name = name
    bpy.ops.rigidbody.object_add()
    rb = ob.rigid_body
    rb.collision_shape = shape
    rb.mass = mass
    rb.friction = 0
    rb.restitution = restitution
    rb.linear_damping = rb.angular_damping = 0
    rb.use_margin = True
    rb.collision_margin = margin
    return ob


def linearize(ob):
    """IA: Interpolación lineal en posición y constante en el estado cinemático, compatible con acciones por capas de Blender 5."""
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


def trial(shape, margin, substeps, split, restitution, ratio=1.0):
    """IA: Proyectil guiado a 10 u/s hasta antes del contacto y luego libre; devuelve restitución medida, exceso y momento normalizado."""
    scene = bpy.data.scenes.new('Sonda E9b')
    bpy.context.window.scene = scene
    scene.render.fps = FPS
    scene.frame_end = FRAMES
    scene.gravity = (0, 0, 0)
    pair = math.sqrt(restitution)
    projectile = body('Proyectil', -5, ratio, pair, shape, margin)
    target = body('Pieza', 0, 1, pair, shape, margin)
    world = scene.rigidbody_world
    world.substeps_per_frame = substeps
    world.solver_iterations = 60
    world.use_split_impulse = split
    world.point_cache.frame_end = FRAMES
    step = SPEED / FPS
    for frame in (1, 13):
        projectile.location.x = -5 + (frame - 1) * step
        projectile.keyframe_insert(data_path='location', frame=frame)
        projectile.rigid_body.kinematic = True
        projectile.rigid_body.keyframe_insert(data_path='kinematic', frame=frame)
    projectile.rigid_body.kinematic = False
    projectile.rigid_body.keyframe_insert(data_path='kinematic', frame=14)
    linearize(projectile)
    xs = []
    for frame in range(1, FRAMES + 1):
        scene.frame_set(frame)
        dg = bpy.context.evaluated_depsgraph_get()
        xs.append([ob.evaluated_get(dg).matrix_world.translation.x for ob in (projectile, target)])
    incoming = (xs[24][0] - xs[19][0]) * FPS / 5
    vp, vt = ((xs[89][i] - xs[79][i]) * FPS / 10 for i in (0, 1))
    measured = (vt - vp) / incoming if incoming > 0 else float('nan')
    result = dict(shape=shape, margin=margin, substeps=substeps, split_impulse=split,
                  ratio=ratio, restitution_requested=restitution, incoming=incoming,
                  outgoing_projectile=vp, outgoing_target=vt,
                  restitution_measured=measured, excess=measured - restitution,
                  momentum=(ratio * vp + vt) / max(ratio * incoming, 1e-12),
                  eta=vt**2 / max(ratio * incoming**2, 1e-12))
    bpy.data.batch_remove(ids=tuple(scene.objects))
    bpy.data.scenes.remove(scene)
    return result


def run():
    """IA: Barrido completo y por razón de masas; escribe reports/impact_restitution_probe.json y no falla por resultado (es una sonda)."""
    started = time.monotonic()
    grid = []
    for shape in ('SPHERE', 'CONVEX_HULL', 'BOX'):
        for margin in (0.0, 0.001, 0.01, 0.04):
            for substeps in (40, 160):
                for split in (True, False):
                    for e in (0.0, 0.3):
                        grid.append(trial(shape, margin, substeps, split, e))
    ratios = [trial(shape, .04, 40, True, .095445, r) for shape in ('SPHERE', 'CONVEX_HULL', 'BOX') for r in (.1, 1, 10)]
    commit = subprocess.run(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
    report = dict(commit=commit, blender=bpy.app.version_string, seconds=time.monotonic() - started,
                  grid=grid, ratios=ratios,
                  scope='Dos cuerpos libres sin gravedad, choque central; mide restitución efectiva de Bullet, no alcance ni panel.')
    (ROOT / 'reports/impact_restitution_probe.json').write_text(json.dumps(report, indent=1), encoding='utf8')
    for r in grid:
        print('PROBE %-11s m=%.3f ss=%3d split=%d e=%.2f -> e_med=%.3f exceso=%+.3f mom=%.4f' % (
            r['shape'], r['margin'], r['substeps'], r['split_impulse'], r['restitution_requested'],
            r['restitution_measured'], r['excess'], r['momentum']), flush=True)
    for r in ratios:
        print('RATIO %-11s r=%5.1f e_med=%.3f eta=%.3f' % (r['shape'], r['ratio'], r['restitution_measured'], r['eta']), flush=True)
    print('SECONDS', report['seconds'], flush=True)


if __name__ == '__main__':
    run()
