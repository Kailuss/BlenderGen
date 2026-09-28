"""Comparación reproducible de desgaste: volumen, cierre, coste y vista con luz rasante."""
import json
from pathlib import Path
import sys
import time

import bpy
import bmesh
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'tests'))
from ruinas_panel import runtime
from ruinas_panel.geometry import primitives, weather


def run():
    """IA: compara intensidades con tres semillas y la misma piedra; guarda métricas y render sin alterar referencias."""
    label = sys.argv[sys.argv.index('--') + 1]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    runtime.quality = 'DETAIL'
    runtime.preview = False
    from types import SimpleNamespace
    runtime.instance_build = False
    runtime.settings = SimpleNamespace(microdetail_preview=True, export_density=1.0)
    scene = bpy.context.scene
    coll = bpy.data.collections.new('Comparación de desgaste')
    scene.collection.children.link(coll)
    mat = primitives.material('Caliza', (.55, .49, .39))
    rows = []
    for row, seed in enumerate((17, 43, 91)):
        for column, amount in enumerate((0, .3, .55, .85, 1)):
            ob = primitives.block('Piedra prueba', -6, 6, -4, 4, 0, 6, coll, mat)
            original = primitives.mesh_volume(ob.data)
            start = time.perf_counter()
            weather.weather_stone(ob, amount, seed)
            elapsed = time.perf_counter() - start
            bm = bmesh.new()
            bm.from_mesh(ob.data)
            opened = sum(not edge.is_manifold for edge in bm.edges)
            degenerate = sum(face.calc_area() < 1e-8 for face in bm.faces)
            bm.free()
            volume = primitives.mesh_volume(ob.data)
            assert not opened and not degenerate, (seed, amount, opened, degenerate)
            assert 0 < volume <= original + 1e-5, (seed, amount, volume, original)
            rows.append(dict(seed=seed, amount=amount, loss=1-volume/original,
                             faces=len(ob.data.polygons), seconds=elapsed))
            ob.location = (column * 16, 0, row * 10)
    primitives.drop_stage()
    if label != 'before':
        for seed in (17, 43, 91):
            samples = [r for r in rows if r['seed'] == seed]
            assert all(a['loss'] < b['loss'] for a, b in zip(samples, samples[1:])), samples
            # La base completa añade recortes de desconchones: su topología depende de wear.
    bpy.ops.object.camera_add(location=(80, -130, 95))
    camera = bpy.context.object
    camera.rotation_euler = (Vector((32, 0, 13))-camera.location).to_track_quat('-Z', 'Y').to_euler()
    camera.data.type = 'ORTHO'
    camera.data.ortho_scale = 87
    scene.camera = camera
    scene.render.engine = 'BLENDER_WORKBENCH'
    scene.display.shading.light = 'STUDIO'
    scene.display.shading.studiolight_rotate_z = .6
    scene.display.shading.color_type = 'MATERIAL'
    scene.display.shading.show_shadows = True
    scene.display.shading.show_cavity = True
    scene.display.shading.cavity_type = 'BOTH'
    scene.render.resolution_x = 1400
    scene.render.resolution_y = 800
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(ROOT / 'reports' / ('weather_' + label + '.png'))
    bpy.ops.render.render(write_still=True)
    (ROOT / 'reports' / ('weather_' + label + '.json')).write_text(json.dumps(rows, indent=2)+'\n', encoding='utf-8')
    print('WEATHER_PASSED', label, flush=True)


def integration():
    """IA: CUSTOM cambia la geometría y su caché en Detalle; extremos cerrados y máximo fusionable."""
    import ruinas_panel as addon
    from ruinas_panel import config
    from ruinas_panel.services import cache, export
    from blender_probe import closure, digest, stored
    bpy.ops.wm.read_factory_settings(use_empty=True)
    addon.register()
    runtime.busy = True
    runtime.preview = False
    p = bpy.context.scene.ruin_settings
    for key, value in dict(wear_level='CUSTOM', length=60, height_type='RUIN',
                           hole_count=0, pillar_count=0, collapse=.15,
                           cracks=0, rubble_amount=0, ground_roughness=0).items():
        setattr(p, key, value)
    previous = None
    for amount in (0, .55, 1):
        p.wear = amount
        coll = addon.generate(bpy.context, p, 'DETAIL')
        assert abs(p.wear - amount) < 1e-6
        assert not stored('ruinas_metricas')['cached']
        current = digest(coll)
        assert current != previous
        sealed = closure(coll)
        assert not sealed['open_edges'] and not sealed['degenerate_faces'], sealed
        addon.generate(bpy.context, p, 'DETAIL')
        assert stored('ruinas_metricas')['cached']
        assert digest(bpy.data.collections[config.COLLECTION]) == current
        previous = current
    solid = addon.make_solid(bpy.context)
    bm = bmesh.new()
    bm.from_mesh(solid.data)
    assert all(e.is_manifold for e in bm.edges) and len(export.shells(bm)) == 1
    bm.free()
    cache.clear_cache()
    addon.unregister()
    print('WEATHER_INTEGRATION_PASSED', flush=True)


if __name__ == '__main__':
    run()
    if '--integration' in sys.argv:
        integration()
