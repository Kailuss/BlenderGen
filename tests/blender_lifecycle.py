"""Comprueba recarga, compatibilidad .blend e instalación aislada del ZIP."""
import argparse
import importlib
import json
from pathlib import Path
import runpy
import sys
import tempfile
import zipfile

import bpy
import bmesh

ROOT=Path(__file__).resolve().parents[1]


def run():
    """IA: prueba el ZIP extraído sin modificar preferencias ni instalar globalmente en Blender."""
    parser=argparse.ArgumentParser()
    parser.add_argument('--input',type=Path,required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    bpy.ops.wm.open_mainfile(filepath=str(args.input.resolve()))
    runpy.run_path(str(ROOT/'tools/load_in_blender.py'),run_name='__main__')
    import ruinas_panel
    from ruinas_panel import runtime
    from ruinas_panel.ui import preview
    p=bpy.context.scene.ruin_settings
    assert p.windows_enabled and p.layout_mode=='ONE'
    p.seed=314
    old_timer=preview.refresh_timer
    assert bpy.app.timers.is_registered(old_timer)
    runpy.run_path(str(ROOT/'tools/load_in_blender.py'),run_name='__main__')
    assert not bpy.app.timers.is_registered(old_timer)
    assert bpy.context.scene.ruin_settings.seed==314
    bpy.app.driver_namespace['ruinas_cleanup']()
    for name in tuple(sys.modules):
        if name=='ruinas_panel' or name.startswith('ruinas_panel.'):del sys.modules[name]
    with tempfile.TemporaryDirectory(prefix='ruinas_zip_') as folder:
        with zipfile.ZipFile(ROOT/'dist/ruinas_panel_v021.zip') as archive:archive.extractall(folder)
        sys.path.insert(0,folder);importlib.invalidate_caches()
        addon=importlib.import_module('ruinas_panel');addon.register()
        assert Path(addon.__file__).is_relative_to(folder)
        from ruinas_panel import runtime
        runtime.busy=True;runtime.preview=True
        p=bpy.context.scene.ruin_settings
        p.layout_mode='NONE';p.height_type='ONE';p.door_enabled=False;p.windows_enabled=False
        p.cracks=0;p.hole_count=0;p.collapse=.1;p.export_quality='DRAFT'
        coll=addon.generate(bpy.context,p,'DRAFT')
        solid=addon.make_solid(bpy.context)
        bm=bmesh.new();bm.from_mesh(solid.data)
        assert all(e.is_manifold for e in bm.edges)
        bm.free()
        report={'hot_reload':True,'timer_cancelled':True,'blend_v20_properties_preserved':True,
                'zip_registration':True,'fused_solid_manifold':True,'faces':len(solid.data.polygons)}
        addon.unregister();sys.path.remove(folder)
    (ROOT/'reports/lifecycle.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('LIFECYCLE_PASSED',flush=True)


if __name__=='__main__':run()
