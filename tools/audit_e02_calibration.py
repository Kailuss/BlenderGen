"""Inventario no destructivo de la etapa física para la orden B1-C5."""
import collections
import hashlib
import json
import math
import subprocess
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parents[1]


def run():
    """IA: Lee cuerpos, masas mínimas y coeficientes reales de la etapa abierta; nunca guarda ni simula la escena."""
    records = []
    for scene in bpy.data.scenes:
        if not scene.get('ruinas_physics_lab'):
            continue
        scene.frame_set(1)
        groups = collections.defaultdict(list)
        projectiles = []
        floor_mass = []
        for ob in scene.objects:
            rb = ob.rigid_body
            if not rb:
                continue
            family = ob.name.split(' · ')[0]
            row = dict(name=ob.name, family=family, role=ob.get('physical_role'), type=rb.type,
                       mass=rb.mass, volume_mm3=ob.get('physical_volume_mm3'),
                       friction=rb.friction, restitution=rb.restitution,
                       linear_damping=rb.linear_damping, angular_damping=rb.angular_damping)
            groups[family].append(row)
            if rb.mass <= .00100001:
                floor_mass.append(row)
            if ob.get('impactor'):
                radius=max(ob.dimensions)/2
                projectiles.append(dict(row, radius_model_m=radius,
                                        nominal_density_kg_m3=rb.mass/(4/3*math.pi*radius**3)/10000,
                                        release_frame=ob.get('release_frame')))
        records.append(dict(scene=scene.name, substeps=scene.rigidbody_world.substeps_per_frame,
                            iterations=scene.rigidbody_world.solver_iterations,
                            family_counts={key:len(value) for key,value in groups.items()},
                            coefficients={key:sorted({tuple(row[k] for k in ('friction','restitution','linear_damping','angular_damping')) for row in value}) for key,value in groups.items()},
                            minimum_mass_count=len(floor_mass), minimum_mass_pieces=floor_mass,
                            projectiles=projectiles))
    source=Path(bpy.data.filepath)
    report=dict(source=str(source), sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                commit=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip(),
                scenes=records)
    (ROOT/'reports/e02_calibration_inventory.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf8')
    print('E02_CALIBRATION_INVENTORY',[(r['scene'],r['minimum_mass_count']) for r in records],flush=True)


if __name__ == '__main__':
    run()
