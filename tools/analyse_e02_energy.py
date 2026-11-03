"""Auditoría de expulsiones, fugas y régimen de contacto del Ejercicio 02 desde poses guardadas.

Sin Blender: cruza reports/shrapnel_poses_<N>.npz con reports/e02_piece_table.json
(tools/audit_e02_regime.py) y escribe reports/e02_energy_regime.json.

Métricas (criterios de la orden B1-C5, sección 4):
- Velocidad de lanzamiento horizontal: máximo de |v_xy| en los 3 primeros fotogramas
  desde que la pieza se mueve (> 2 mm). La gravedad no contribuye en horizontal, así
  que separa expulsión de caída. Se compara con 1,5 veces la velocidad del proyectil.
- Lanzamiento vertical ascendente con el mismo criterio.
- Fugas: cuerpos que bajan más de 20 mm por debajo de la cara superior del suelo.
- Régimen de contacto: avance por subpaso / radio envolvente propio frente a
  impact_spec.BULLET_ANTICIPATION_RATIO (aproximación: el radio menor de la pareja
  puede ser otro).
Requiere numpy: en Windows, ejecutar con el Python de Blender
(`blender -b --factory-startup --python tools/analyse_e02_energy.py`).
Limitaciones: traslación solamente, velocidades a 24 fps (subestiman picos de contacto),
masas de solver (válidas para cocientes) y el proyectil guiado aporta energía sin límite.
"""
import collections
import json
import sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from ruinas_panel.services import impact_spec

PROJECTILE_SPEED = .8
MOVE_M = .002
LAUNCH_FRAMES = 3
ESCAPE_M = .02


def family(name):
    """IA: Familia de pieza: prefijo del nombre antes del primer separador «·»."""
    return name.split(' · ')[0]


def run(frames=240, substeps=160):
    """IA: Calcula lanzamientos, fugas y régimen por forma; escribe el informe y lo devuelve; no falla por resultado."""
    data = np.load(ROOT/f'reports/shrapnel_poses_{frames}.npz')
    poses, names = data['poses'].astype(np.float64), data['names'].tolist()
    table = json.loads((ROOT/'reports/e02_piece_table.json').read_text(encoding='utf8'))
    bodies = {b['name']: b for b in table['bodies']}
    fps = table['fps'] / table['fps_base']
    floor = bodies.get('Suelo de seguridad')
    floor_top = floor['location_m'][2] + floor['dimensions_m'][2] / 2 if floor else 0.
    pieces = [i for i, n in enumerate(names) if n in bodies and bodies[n]['type'] == 'ACTIVE'
              and not n.startswith('Metralla')]
    label = [names[i] for i in pieces]
    mass = np.array([bodies[n]['mass'] for n in label])
    radius = np.array([max(bodies[n]['radius_m'], 1e-6) for n in label])
    shape = np.array([bodies[n]['shape'] for n in label])
    pos = poses[:, pieces, :3]
    vel = np.zeros_like(pos)
    vel[1:-1] = (pos[2:] - pos[:-2]) * fps / 2
    speed = np.linalg.norm(vel, axis=2)
    horizontal = np.linalg.norm(vel[:, :, :2], axis=2)
    moved = np.linalg.norm(pos - pos[0], axis=2) > MOVE_M
    start = np.where(moved.any(0), moved.argmax(0), -1)
    active = start >= 0
    launch_h = np.array([horizontal[s:s + LAUNCH_FRAMES, j].max() if s >= 0 else 0. for j, s in enumerate(start)])
    launch_up = np.array([vel[s:s + LAUNCH_FRAMES, j, 2].max() if s >= 0 else 0. for j, s in enumerate(start)])
    limit = 1.5 * PROJECTILE_SPEED
    over = active & (launch_h > limit)
    upward = active & (launch_up > PROJECTILE_SPEED)
    escaped = (pos[:, :, 2] < floor_top - ESCAPE_M).any(0)
    paths = json.loads((ROOT/'dist/Ejercicio02_metralla/impactos.json').read_text(encoding='utf8'))['paths']
    edges = [1] + [p['release_frame'] for p in paths] + [frames + 1]
    window = np.digitize(start + 1, edges)
    ratio = speed / (fps * substeps) / radius[None, :]
    moving = speed > .005
    fast = moving & (ratio > impact_spec.BULLET_ANTICIPATION_RATIO)
    regime = {}
    for s in sorted(set(shape.tolist())):
        cols = shape == s
        samples = int(moving[:, cols].sum())
        regime[s] = dict(bodies=int(cols.sum()), moving_samples=samples, fast_samples=int(fast[:, cols].sum()),
                         fast_fraction=float(fast[:, cols].sum() / samples) if samples else None)
    need = speed[moving] / (fps * impact_spec.BULLET_ANTICIPATION_RATIO * np.broadcast_to(radius, speed.shape)[moving])
    shots = [bodies[p['name']] if p['name'] in bodies else None for p in paths]
    nominal = sum(.5 * b['mass'] * PROJECTILE_SPEED**2 for b in bodies.values() if b['name'].startswith('Metralla'))
    pct = lambda a, q: float(np.percentile(a, q)) if a.size else None
    report = dict(
        source=table['source'], sha256=table['sha256'], fps=fps, substeps_assumed=substeps,
        projectile_speed_m_s=PROJECTILE_SPEED, active_pieces=len(pieces), moving_pieces=int(active.sum()),
        launch_horizontal_m_s={f'p{q}': pct(launch_h[active], q) for q in (50, 90, 95, 99)},
        launch_horizontal_over_1_5v=int(over.sum()),
        launch_horizontal_over_by_shape=dict(collections.Counter(shape[over].tolist())),
        launch_horizontal_over_by_family=dict(collections.Counter(family(n) for n, o in zip(label, over) if o).most_common()),
        launch_horizontal_over_by_window={('antes de liberar 01' if k == 1 else f'tras liberar {k - 1:02d}'): int(v)
                                          for k, v in sorted(collections.Counter(window[over].tolist()).items())},
        launch_upward_over_v=int(upward.sum()), launch_upward_p99_m_s=pct(launch_up[active], 99),
        anomalous_horizontal_kinetic=float((.5 * mass[over] * launch_h[over]**2).sum()),
        projectiles_nominal_kinetic=float(nominal),
        anomalous_to_projectile_energy=float((.5 * mass[over] * launch_h[over]**2).sum() / nominal) if nominal else None,
        escaped_below_floor=int(escaped.sum()),
        escaped=[dict(name=n, shape=str(s), start_frame=int(st + 1), launch_horizontal_m_s=float(lh))
                 for n, s, st, lh, e in zip(label, shape, start, launch_h, escaped) if e],
        regime_by_shape=regime,
        substeps_required_p50=int(np.ceil(np.percentile(need, 50))) if need.size else None,
        substeps_required_p95=int(np.ceil(np.percentile(need, 95))) if need.size else None,
        limits='Traslación solamente; velocidades a 24 fps; masas de solver; radio propio como aproximación del radio menor de la pareja.')
    out = ROOT/'reports/e02_energy_regime.json'
    out.write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding='utf8')
    print(json.dumps({k: v for k, v in report.items() if k not in ('escaped', 'source')}, indent=1, ensure_ascii=False))
    return report


if __name__ == '__main__':
    run()
