"""Tabla de piezas del Ejercicio 02 para auditar régimen de contacto y energía sin simular.

Abre 03e_laboratorio_entrega.blend en modo lectura (no guarda) y escribe
reports/e02_piece_table.json: por cuerpo rígido, forma, masa, radio envolvente,
materiales y rol físico. Las poses ya calculadas (reports/shrapnel_poses_*.npz)
se cruzan por nombre en tools/analyse_e02_energy.py, fuera de Blender.
"""
import hashlib
import json
import sys
from pathlib import Path
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT/'dist/Ejercicio02_metralla_20261028/03e_laboratorio_entrega.blend'
SCENE = '02 · Laboratorio tres impactos'


def sha256(path):
    """IA: Huella del archivo auditado por bloques, para ligar el informe a un archivo concreto."""
    digest = hashlib.sha256()
    with open(path, 'rb') as handle:
        for block in iter(lambda: handle.read(1 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def radius(ob):
    """IA: Radio de la esfera envolvente centrada en el origen del objeto, con su escala; aproxima el disco de movimiento angular que usa Bullet."""
    mesh = ob.data
    scale = ob.matrix_world.to_scale()
    best = 0.
    for v in mesh.vertices:
        co = Vector((v.co.x * scale.x, v.co.y * scale.y, v.co.z * scale.z))
        best = max(best, co.length)
    return best


def run():
    """IA: Recorre los cuerpos rígidos de la escena de laboratorio y escribe la tabla; falla si la escena no existe."""
    source = Path(sys.argv[sys.argv.index('--') + 1]) if '--' in sys.argv else SOURCE
    bpy.ops.wm.open_mainfile(filepath=str(source), load_ui=False)
    scene = bpy.data.scenes.get(SCENE)
    if scene is None:
        raise ValueError('No existe la escena ' + SCENE)
    world = scene.rigidbody_world
    rows = []
    for ob in scene.objects:
        rb = ob.rigid_body
        if ob.type != 'MESH' or rb is None:
            continue
        rows.append(dict(name=ob.name, type=rb.type, kinematic=bool(rb.kinematic), shape=rb.collision_shape,
                         margin=rb.collision_margin, mass=rb.mass, restitution=rb.restitution, friction=rb.friction,
                         linear_damping=rb.linear_damping, angular_damping=rb.angular_damping,
                         radius_m=radius(ob), location_m=list(ob.matrix_world.translation),
                         dimensions_m=list(ob.dimensions), physical_role=ob.get('physical_role'),
                         impactor=bool(ob.get('impactor')), lab_decor=bool(ob.get('lab_decor')),
                         materials=[s.material.name for s in ob.material_slots if s.material]))
    report = dict(source=str(source), sha256=sha256(source), scene=scene.name, fps=scene.render.fps,
                  fps_base=scene.render.fps_base, gravity=list(scene.gravity),
                  substeps=world.substeps_per_frame if world else None,
                  iterations=world.solver_iterations if world else None,
                  time_scale=world.time_scale if world else None, bodies=rows)
    out = ROOT/'reports/e02_piece_table.json'
    out.write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding='utf8')
    print('E02_TABLE', len(rows), 'cuerpos ->', out, flush=True)


if __name__ == '__main__':
    run()
