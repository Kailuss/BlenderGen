"""Placa de prueba para resina: ranuras en V, profundidades, pivotes y piedras reales agrietadas.

Uso: python dev.py calibrate  (ejecuta Blender en segundo plano y deja STL y leyenda en dist/).
"""
import argparse
from pathlib import Path
import sys

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
PLATE = (72.0, 44.0, 2.5)
TOP = PLATE[2]
PITCH = 7.5
WIDTHS = (.05, .08, .10, .12, .15, .20, .25, .30, .40)
DEPTHS = (.10, .15, .20, .30, .50, .80)
PINS = (.2, .3, .4, .5, .6, .8, 1.0)


def mesh(name, verts, faces, coll):
    """IA: crea una malla exacta en mm sin bisel ni desgaste; la enlaza a coll."""
    data = bpy.data.meshes.new(name)
    data.from_pydata(verts, [], faces)
    data.update()
    ob = bpy.data.objects.new(name, data)
    coll.objects.link(ob)
    return ob


def box(name, x0, x1, y0, y1, z0, z1, coll):
    """IA: caja cerrada con normales hacia fuera."""
    verts = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    return mesh(name, verts, [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)], coll)


def groove(name, x, y0, y1, width, depth, coll):
    """IA: cortador en V como el de las grietas: ancho width exacto en la superficie plana y fondo a depth."""
    half = width / 2 * (depth + .2) / depth
    verts = [(x - half, y0, TOP + .2), (x + half, y0, TOP + .2), (x, y0, TOP - depth),
             (x - half, y1, TOP + .2), (x + half, y1, TOP + .2), (x, y1, TOP - depth)]
    faces = [(0, 2, 1), (3, 4, 5), (0, 1, 4, 3), (1, 2, 5, 4), (2, 0, 3, 5)]
    return mesh(name, verts, faces, coll)


def pin(name, x, y, diameter, height, coll, sides=16):
    """IA: pivote cilíndrico hundido 0,3 mm en la placa para quedar unido a ella."""
    import math
    r = diameter / 2
    verts = [(x + r * math.cos(k * math.tau / sides), y + r * math.sin(k * math.tau / sides), z)
             for z in (TOP - .3, TOP + height) for k in range(sides)]
    faces = [tuple(reversed(range(sides))), tuple(range(sides, 2 * sides))]
    faces += [(k, (k + 1) % sides, (k + 1) % sides + sides, k + sides) for k in range(sides)]
    return mesh(name, verts, faces, coll)


def real_stone(coll, x, y, amount, seed, split):
    """IA: piedra del generador (bisel, desgaste y grietas en Detalle) tumbada con su cara frontal hacia arriba."""
    from ruinas_panel import runtime
    from ruinas_panel.geometry import fracture, primitives, weather
    mat = primitives.material('Piedra · neutro', (.52, .52, .52))
    ob = primitives.block('Piedra de prueba %s' % seed, 0, 10.5, -2, 2, 0, 5.7, coll, mat)
    weather.weather_stone(ob, runtime.settings.wear, seed)
    fracture.crack_stone(ob, amount, seed, coll, mat, (Vector((1, 0, 0)), Vector((0, -1, 0))), split)
    for v in ob.data.vertices:
        px, py, pz = v.co
        # Giro de -90° en X: la cara frontal (−Y) queda hacia +Z; la base se hunde 0,3 mm en la placa.
        v.co = (px + x, pz + y, -py + TOP + 2 - .3)
    ob.data.update()
    return ob


def apply_boolean(base, coll, operation):
    """IA: aplica un booleano Manifold con operando de colección sobre base."""
    mod = base.modifiers.new(operation, 'BOOLEAN')
    mod.operation = operation
    mod.operand_type = 'COLLECTION'
    mod.collection = coll
    mod.solver = 'MANIFOLD'
    bpy.context.view_layer.objects.active = base
    bpy.ops.object.modifier_apply(modifier=mod.name)


def build(output):
    """IA: construye la placa, la valida (cerrada y de una pieza) y exporta STL y leyenda en mm."""
    sys.path.insert(0, str(ROOT / 'src'))
    import bmesh
    import ruinas_panel as g
    from ruinas_panel import runtime
    from ruinas_panel.services import export
    g.register()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    runtime.busy = True
    runtime.preview = False
    runtime.quality = 'DETAIL'
    runtime.settings = scene.ruin_settings
    runtime.timings = {}
    cutters = bpy.data.collections.new('cortadores')
    extras = bpy.data.collections.new('relieves')
    for coll in (cutters, extras):
        scene.collection.children.link(coll)
    plate = box('Placa de prueba', 0, PLATE[0], 0, PLATE[1], 0, TOP, scene.collection)
    legend = ['# Placa de prueba para resina', '', 'Medidas en mm. El triángulo en relieve marca la esquina de inicio (x=0, y=44).', '']
    legend.append('## Fila A · ancho en superficie (profundidad 0,5)')
    for i, width in enumerate(WIDTHS):
        groove('A %.2f' % width, 6 + PITCH * i, 4, 14, width, .5, cutters)
        legend.append('- A%d (x=%.1f): %.2f mm' % (i + 1, 6 + PITCH * i, width))
    legend += ['', '## Fila B · profundidad (ancho 0,20)']
    for i, depth in enumerate(DEPTHS):
        groove('B %.2f' % depth, 6 + PITCH * i, 18, 28, .20, depth, cutters)
        legend.append('- B%d (x=%.1f): %.2f mm' % (i + 1, 6 + PITCH * i, depth))
    legend += ['', '## Fila C · pivotes de 1 mm de alto (diámetro)']
    for i, diameter in enumerate(PINS):
        pin('C %.1f' % diameter, 6 + PITCH * i, 36, diameter, 1.0, extras)
        legend.append('- C%d (x=%.1f): %.1f mm' % (i + 1, 6 + PITCH * i, diameter))
    legend += ['', '## Piedras reales (calidad Detalle, config.CRACK_PRINT actual)',
               '- D1 (x=48–58,5): grietas 0,3', '- D2 (x=60–70,5): grietas 0,6 con partida']
    real_stone(extras, 48, 18, .3, 4101, False)
    real_stone(extras, 60, 18, .6, 4102, True)
    mesh('Marca de inicio', [(1.5, 38.5, TOP - .3), (4.5, 38.5, TOP - .3), (3, 42, TOP - .3),
                             (1.5, 38.5, TOP + .8), (4.5, 38.5, TOP + .8), (3, 42, TOP + .8)],
         [(0, 2, 1), (3, 4, 5), (0, 1, 4, 3), (1, 2, 5, 4), (2, 0, 3, 5)], extras)
    from ruinas_panel.geometry import primitives
    primitives.drop_stage()
    apply_boolean(plate, cutters, 'DIFFERENCE')
    apply_boolean(plate, extras, 'UNION')
    bm = bmesh.new()
    bm.from_mesh(plate.data)
    closed = all(e.is_manifold for e in bm.edges)
    pieces = len(export.shells(bm))
    bm.free()
    if not closed or pieces != 1:
        raise RuntimeError('La placa no es una sola pieza cerrada: cerrada=%s, piezas=%s' % (closed, pieces))
    for ob in list(scene.objects):
        ob.select_set(ob == plate)
    output.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.stl_export(filepath=str(output), export_selected_objects=True, global_scale=1.0, use_scene_unit=False,
                          apply_modifiers=True)
    legend += ['', 'Tras imprimir e imprimar: anota el ancho mínimo de la fila A y la profundidad mínima de la fila B que',
               'siguen visibles, y el pivote más fino que sobrevive. Con eso se ajusta config.CRACK_PRINT.']
    output.with_suffix('.md').write_text('\n'.join(legend) + '\n', encoding='utf-8')
    print('PLATE_READY', output, len(plate.data.polygons), 'caras', flush=True)


def main():
    """IA: lee --output tras «--» en la línea de Blender y construye la placa."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    build(args.output)


if __name__ == '__main__':
    main()
