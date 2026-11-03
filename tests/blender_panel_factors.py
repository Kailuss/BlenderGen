"""Sonda de factores sobre el banco de panel: qué ingrediente de la casa provoca las expulsiones.

Parte de la variante B de tests/blender_panel_bench.py (bola convexa soltada antes del
contacto, subpasos por régimen) y añade un factor cada vez:
- F1 piedras con forma MESH (como las piezas cóncavas que la casa conserva);
- F2 bola con forma SPHERE (como el proyectil del add-on);
- F3 uniones FIXED rompibles entre piedras vecinas (como el laboratorio estructural);
- F4 tejas pequeñas sobre la coronación;
- F5 piedras retenidas cinemáticas hasta el contacto (hold_until_impact del Ejercicio 02);
- F6 variante A (bola guiada a través del muro) como referencia.
Es una sonda: informa, no falla por resultado. Escribe reports/panel_factors.json.
"""
import json
import math
import subprocess
import sys
import time
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'tests')]
import blender_panel_bench as bench
from ruinas_panel.services import impact_spec

TILE = (0.75, 0.53, 0.39)


def add_tiles(scene):
    """IA: Una hilada de tejas pequeñas CONVEX_HULL sobre la coronación del muro."""
    top = bench.COURSES * (bench.STONE[2] + bench.GAP)
    tiles = []
    for index in range(40):
        x = -15 + index * .77
        tiles.append(bench.hull_box(f'Teja {index:02d}', TILE, (x, 0, top + TILE[2] / 2)))
    return tiles


def add_joints(scene, stones, threshold):
    """IA: Une cada piedra con sus vecinas en contacto mediante restricciones FIXED rompibles."""
    count = 0
    for i, a in enumerate(stones):
        for b in stones[i + 1:]:
            d = a.location - b.location
            close_x = abs(abs(d.x) - bench.STONE[0]) < 1e-3 and abs(d.z) < 1e-3
            close_z = abs(abs(d.z) - bench.STONE[2]) < 1e-3 and abs(d.x) < bench.STONE[0]
            if not (close_x or close_z):
                continue
            joint = bpy.data.objects.new(f'Unión {count}', None)
            joint.location = (a.location + b.location) / 2
            scene.collection.objects.link(joint)
            with bpy.context.temp_override(object=joint, active_object=joint, selected_objects=[joint]):
                bpy.ops.rigidbody.constraint_add(type='FIXED')
            c = joint.rigid_body_constraint
            c.object1, c.object2 = a, b
            c.use_breaking = True
            c.breaking_threshold = threshold
            count += 1
    return count


def retain(stones, until):
    """IA: Piedras cinemáticas hasta el fotograma de contacto y dinámicas después."""
    for ob in stones:
        rb = ob.rigid_body
        rb.kinematic = True
        rb.keyframe_insert(data_path='kinematic', frame=1)
        rb.keyframe_insert(data_path='kinematic', frame=until)
        rb.kinematic = False
        rb.keyframe_insert(data_path='kinematic', frame=until + 1)
        for curve in ob.animation_data.action.fcurves if hasattr(ob.animation_data.action, 'fcurves') else []:
            for key in curve.keyframe_points:
                key.interpolation = 'CONSTANT'


def trial(label, substeps, release_offset, factor):
    """IA: Prepara la escena de banco con el factor indicado, simula y mide como bench.variant."""
    original_hull, original_ball = bench.hull_box, bench.ball
    extra = {}

    def shaped_box(name, size, location, passive=False):
        """IA: Caja del banco con forma MESH en lugar de CONVEX_HULL para las piedras (F1)."""
        ob = original_hull(name, size, location, passive)
        if factor == 'F1' and name.startswith('Piedra'):
            ob.rigid_body.collision_shape = 'MESH'
            ob.rigid_body.mesh_source = 'BASE'
        return ob

    def shaped_ball(scene, release_frame, contact_frame):
        """IA: Bola del banco con forma SPHERE (F2) y escena ampliada con tejas, uniones o retención."""
        ob = original_ball(scene, release_frame, contact_frame)
        if factor == 'F2':
            ob.rigid_body.collision_shape = 'SPHERE'
        stones = [o for o in scene.objects if o.name.startswith('Piedra')]
        if factor == 'F3':
            extra['joints'] = add_joints(scene, stones, 30.0)
        if factor == 'F4':
            extra['tiles'] = len(add_tiles(scene))
        if factor == 'F5':
            retain(stones, contact_frame)
        return ob

    bench.hull_box, bench.ball = shaped_box, shaped_ball
    try:
        result = bench.variant(label, substeps, release_offset)
    finally:
        bench.hull_box, bench.ball = original_hull, original_ball
    result.update(factor=factor, **extra)
    return result


def run():
    """IA: Ejecuta F0 a F6 y escribe el informe; no aplica criterios de aceptación."""
    radius = math.dist((0, 0, 0), [s / 2 for s in bench.STONE])
    sub = max(impact_spec.contact_regime(bench.BALL_SPEED, radius, bench.FPS, 1)['substeps_required'], 10)
    plan = [('F0 base B', sub, -2, 'F0'), ('F1 piedras MESH', sub, -2, 'F1'), ('F2 bola SPHERE', sub, -2, 'F2'),
            ('F3 uniones', sub, -2, 'F3'), ('F4 tejas', sub, -2, 'F4'), ('F5 retenidas', sub, -2, 'F5'),
            ('F6 guiada (A)', 40, 6, 'F6')]
    started = time.monotonic()
    rows = [trial(*item) for item in plan]
    commit = subprocess.run(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
    (ROOT/'reports/panel_factors.json').write_text(json.dumps(dict(commit=commit, blender=bpy.app.version_string,
        seconds=time.monotonic() - started, rows=rows), indent=2), encoding='utf8')
    for r in rows:
        print('FACTOR %-16s ss=%3d deriva=%.3fmm movidas=%3d p99/v=%.2f max/v=%.2f eta=%.3f arriba=%d fugas=%d t=%.1fs %s' % (
            r['variant'], r['substeps'], r['settle_drift_mm'], r['moved'], r['launch_p99_over_v'], r['launch_max_over_v'],
            r['eta_horizontal'], r['upward_faster_than_ball'], r['escaped'], r['seconds'],
            ' '.join(f'{k}={r[k]}' for k in ('joints', 'tiles') if k in r)), flush=True)
    print('PANEL_FACTORS_DONE', round(time.monotonic() - started, 1), flush=True)


if __name__ == '__main__':
    run()
