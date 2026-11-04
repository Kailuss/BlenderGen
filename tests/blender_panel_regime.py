"""Sonda: qué energía crece con los subpasos en Régimen (40 frente a 400) sobre el banco de panel.

Hipótesis principal: sin impulso dividido, Bullet corrige la penetración inicial con una velocidad
proporcional a penetración / paso; con 10 veces más subpasos el paso es 10 veces menor y la
expulsión crece. El laboratorio no usa impulso dividido y sus piezas reales se solapan algo.
Matriz: subpasos 40/400 × impulso dividido sí/no × solape inicial 0/0,1/0,3 mm, más uniones FIXED
rompibles con umbral escalado 40/subpasos. Es una sonda: informa, no falla por resultado.
"""
import json
import subprocess
import sys
import time
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'tests')]
import blender_panel_bench as bench


def joints(threshold40):
    """IA: Devuelve un setup que une piedras vecinas con FIXED rompibles, umbral escalado por 40/subpasos."""
    def setup(scene, stones, substeps):
        """IA: Une vecinas en hilada y entre hiladas con tolerancia al solape; devuelve el recuento."""
        count = 0; pitch_x = bench.STONE[0] + bench.GAP; pitch_z = bench.STONE[2] + bench.GAP
        for i, a in enumerate(stones):
            for b in stones[i + 1:]:
                d = a.location - b.location
                same = abs(d.z) < 1e-3 and abs(abs(d.x) - pitch_x) < 1e-3
                above = abs(abs(d.z) - pitch_z) < 1e-3 and abs(d.x) < bench.STONE[0]
                if not (same or above):
                    continue
                joint = bpy.data.objects.new(f'Unión {count}', None)
                joint.location = (a.location + b.location) / 2
                scene.collection.objects.link(joint)
                with bpy.context.temp_override(object=joint, active_object=joint, selected_objects=[joint]):
                    bpy.ops.rigidbody.constraint_add(type='FIXED')
                c = joint.rigid_body_constraint
                c.object1, c.object2 = a, b
                c.use_breaking = True
                c.breaking_threshold = threshold40 * 40 / substeps
                count += 1
        return {'joints': count}
    return setup


def trial(label, substeps, split, overlap_mm, setup=None):
    """IA: Una celda de la matriz; el solape se impone con GAP negativo (u = 1 cm de modelo)."""
    gap0 = bench.GAP
    bench.GAP = -overlap_mm / 10
    try:
        row = bench.variant(label, substeps, -2, split=split, setup=setup)
    finally:
        bench.GAP = gap0
    row.update(overlap_mm=overlap_mm)
    print('REGIMEN %-22s ss=%3d split=%d solape=%.1fmm deriva=%.3fmm movidas=%3d p99/v=%.2f max/v=%.2f eta=%.3f arriba=%d fugas=%d t=%.1fs %s' % (
        label, substeps, split, overlap_mm, row['settle_drift_mm'], row['moved'], row['launch_p99_over_v'], row['launch_max_over_v'],
        row['eta_horizontal'], row['upward_faster_than_ball'], row['escaped'], row['seconds'], 'uniones=%s' % row['joints'] if 'joints' in row else ''), flush=True)
    return row


def run():
    """IA: Recorre la matriz y escribe reports/panel_regime.json."""
    started = time.monotonic(); rows = []
    for overlap in (0.0, 0.1, 0.3):
        for split in (False, True):
            for substeps in (40, 400):
                rows.append(trial('solape %.1f' % overlap, substeps, split, overlap))
    for split in (False, True):
        for substeps in (40, 400):
            rows.append(trial('uniones solape 0.1', substeps, split, 0.1, joints(30.0)))
    commit = subprocess.run(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
    (ROOT/'reports/panel_regime.json').write_text(json.dumps(dict(commit=commit, blender=bpy.app.version_string,
        seconds=time.monotonic() - started, rows=rows), indent=2), encoding='utf8')
    print('PANEL_REGIME_DONE', round(time.monotonic() - started, 1), flush=True)


if __name__ == '__main__':
    run()
