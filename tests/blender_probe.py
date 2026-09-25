"""Prueba geométrica reproducible del monolito v20 o del paquete modular."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

import bpy
import bmesh
from mathutils import noise

ROOT = Path(__file__).resolve().parents[1]


def digest(coll):
    """IA: compara geometría y nombres sin incluir tiempos o punteros de Blender."""
    result = []
    for ob in sorted(coll.objects, key=lambda o: o.name):
        result.append((ob.name,
                       [tuple(round(float(x), 6) for x in v.co) for v in ob.data.vertices],
                       [tuple(f.vertices) for f in ob.data.polygons]))
    return hashlib.sha256(json.dumps(result, separators=(',', ':')).encode()).hexdigest()


def closure(coll):
    """IA: cuenta por pieza aristas no manifold y caras de área casi nula; no corrige la malla."""
    open_edges, degenerate = {}, {}
    for ob in coll.objects:
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        edges = sum(1 for e in bm.edges if not e.is_manifold)
        faces = sum(1 for f in bm.faces if f.calc_area() < 1e-8)
        bm.free()
        if edges:
            open_edges[ob.name] = edges
        if faces:
            degenerate[ob.name] = faces
    return {'open_edges': open_edges, 'degenerate_faces': degenerate}


def shrunk_by_cracks(coll, ratio=.5):
    """IA: detecta piezas agrietadas cuya caja cae por debajo de ratio de la caja previa guardada en parametros_grieta."""
    shrunk = {}
    for ob in coll.objects:
        if 'parametros_grieta' not in ob or not ob.data.vertices:
            continue
        lo, hi = json.loads(ob['parametros_grieta'])['bounds']
        span = [max(v.co[i] for v in ob.data.vertices) - min(v.co[i] for v in ob.data.vertices) for i in range(3)]
        if any(s < ratio * (b - a) for s, a, b in zip(span, lo, hi)):
            shrunk[ob.name] = [round(s, 2) for s in span]
    return shrunk


def session_checks(g, state, config, case):
    """IA: comprueba carga de archivo con caché llena, handlers de undo y fallo controlado del operador de sólido."""
    from ruinas_panel import registration
    _, changes, quality = case
    assert state.cache, 'la caché debería contener plantillas antes de cargar otro archivo'
    bpy.ops.wm.read_factory_settings(use_empty=True)
    assert not state.cache, ('cache_tras_carga', list(state.cache))
    p = bpy.context.scene.ruin_settings
    for key, value in changes.items():
        setattr(p, key, value)
    g.generate(bpy.context, p, quality)  # En v0.21 original: ReferenceError por plantillas liberadas.
    assert state.cache
    registration.before_data_reload()  # Simula undo: Blender invalida las referencias.
    registration.after_data_reload()
    assert not state.cache
    orphans = [o.name for o in bpy.data.objects if o.name.startswith(config.CACHE_PREFIX)]
    assert not orphans, ('plantillas_huerfanas', orphans[:3])
    # C3: con la misma calidad, exportar no reutiliza la plantilla de vista previa (sin biseles de mortero).
    def mortar_faces():
        """IA: caras de mortero de la fuente actual; la exportación bisela el mortero y la vista previa no."""
        return sum(len(o.data.polygons) for o in bpy.data.collections[config.COLLECTION].objects if o.name.startswith('Mortero'))
    g.generate(bpy.context, p, quality)
    preview_faces = mortar_faces()
    state.preview = False
    try:
        g.generate(bpy.context, p, quality)
        assert not json.loads(bpy.context.scene['ruinas_metricas'])['cached'], 'exportación reutilizó la vista previa'
        assert mortar_faces() > preview_faces, (mortar_faces(), preview_faces)
        g.generate(bpy.context, p, quality)
        assert json.loads(bpy.context.scene['ruinas_metricas'])['cached'], 'la exportación repetida debería usar su caché'
    finally:
        state.preview = True
    g.generate(bpy.context, p, quality)
    assert json.loads(bpy.context.scene['ruinas_metricas'])['cached'], 'la exportación expulsó la caché de vista previa'
    # Operador: un error de validación llega como informe, no como traza, y no toca la escena.
    before = set(bpy.data.objects.keys())
    for key, value in {'build_type': 'FORTRESS', 'layout_mode': 'TWO', 'length': 60, 'door_enabled': True}.items():
        setattr(p, key, value)
    try:
        bpy.ops.ruin.solid()
        raise AssertionError('ruin.solid debería fallar: la puerta no cabe')
    except RuntimeError as exc:
        assert 'No cabe la puerta' in str(exc), exc
    assert set(bpy.data.objects.keys()) == before, 'la validación fallida cambió la escena'
    # Fusión: un fragmento suelto aborta y se borran copias y sólido parcial.
    from ruinas_panel.geometry import primitives
    from ruinas_panel.services import export
    coll = bpy.data.collections[config.COLLECTION]
    primitives.block('Prueba · pieza suelta', 200, 206, 0, 6, 0, 6, coll, primitives.material('Temporal', (.5, .5, .5)))
    before = set(bpy.data.objects.keys())
    try:
        export.make_solid(bpy.context, .45)
        raise AssertionError('make_solid debería rechazar la pieza suelta')
    except ValueError as exc:
        assert 'Fragmento suelto' in str(exc), exc
    assert set(bpy.data.objects.keys()) == before, ('fusion_fallida_deja_objetos', set(bpy.data.objects.keys()) ^ before)
    print('SESSION_PASS', flush=True)


def run():
    """IA: usa procesos separados para baseline/modular; el fallo debe producir exit code distinto de cero."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--legacy', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--case')
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.legacy:
        spec = importlib.util.spec_from_file_location('baseline_v20', args.legacy)
        g = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(g)
        state = g
        config = g
        clear_cache = g.clear_cache
        busy, preview = '_busy', 'PREVIEW'
    else:
        sys.path.insert(0, str(ROOT/'src'))
        import ruinas_panel as g
        from ruinas_panel import runtime as state, config
        from ruinas_panel.services.cache import clear_cache
        busy, preview = 'busy', 'preview'
    g.register()
    setattr(state, busy, True)
    setattr(state, preview, True)
    cases = [
        ('basic_draft', {'layout_mode':'NONE', 'height_type':'ONE'}, 'DRAFT'),
        ('door_windows_work', {'layout_mode':'ONE', 'height_type':'ONE', 'door_enabled':True,
         'door_width':32, 'door_height':34, 'windows_enabled':True, 'collapse':.12, 'hole_count':0, 'cracks':.2}, 'WORK'),
        ('room_beams_draft', {'layout_mode':'ROOM', 'height_type':'TWO', 'door_enabled':True,
         'windows_enabled':True, 'windows_per_wall':2, 'collapse':.18, 'hole_count':0}, 'DRAFT'),
    ]
    reports=[]
    for name, changes, quality in cases:
        if args.case and name!=args.case:continue
        clear_cache()
        bpy.ops.wm.read_factory_settings(use_empty=True)
        p=bpy.context.scene.ruin_settings
        for key, value in changes.items():setattr(p,key,value)
        noise.seed_set(17)
        coll=g.generate(bpy.context,p,quality)
        first=digest(coll)
        metrics=json.loads(bpy.context.scene['ruinas_metricas'])
        assert len(coll.objects)>0
        sealed=closure(coll)
        assert not sealed['open_edges'], ('malla_abierta',name,sealed['open_edges'])
        shrunk=shrunk_by_cracks(coll)
        assert not shrunk, ('grieta_destruye_pieza',name,shrunk)
        windows=json.loads(bpy.context.scene.get('ventanas_generadas','[]'))
        if changes.get('windows_enabled'):assert windows
        beams=json.loads(bpy.context.scene.get('vigas_generadas','[]'))
        if changes['height_type']=='TWO':assert beams
        # La plantilla anterior a grietas debe producir exactamente el mismo resultado.
        coll=g.generate(bpy.context,p,quality)
        assert json.loads(bpy.context.scene['ruinas_metricas'])['cached']
        assert digest(coll)==first, ('cache_changed_geometry',name)
        shapes={ob.name:{'faces':len(ob.data.polygons),'vertices':len(ob.data.vertices),
                'bounds':[[round(float(fn(v.co[i] for v in ob.data.vertices)),5) for i in range(3)] for fn in (min,max)]}
                for ob in coll.objects if ob.data.vertices}
        reports.append({'case':name,'digest':first,'blender':bpy.app.version_string,'closure':sealed,
                        'metrics':metrics,'windows':len(windows),'beams':len(beams),
                        'shapes':shapes,'metadata':{k:bpy.context.scene[k] for k in config.CACHE_METADATA if k in bpy.context.scene}})
        print('CASE_PASS',name,metrics['faces'],flush=True)
    if not args.legacy:
        session_checks(g,state,config,cases[0])
    clear_cache()
    g.unregister();g.register()
    assert hasattr(bpy.types.Scene,'ruin_settings')
    g.unregister()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(reports,indent=2),encoding='utf-8')
    print('PROBE_PASSED',flush=True)


if __name__=='__main__':run()
