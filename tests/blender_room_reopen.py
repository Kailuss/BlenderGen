"""Reapertura del entregable y reimportación de su STL a escala mm."""
import sys,json
from pathlib import Path
import bpy,bmesh
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import ruinas_panel as addon
from ruinas_panel import meta,config
from ruinas_panel.services import physics


def run():
    'IA: Reabre el blend final, verifica poses persistentes, escenas de etapas y sólido; reimporta STL comprobando cierre y cotas.'
    addon.register()
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'dist/ruinas_v0324_proceso_completo.blend'))
    source=bpy.context.scene;assert source.name.startswith('04')
    assert len([s for s in bpy.data.scenes if s.name[:2] in ('01','02','03','04')])==5
    result=meta.get(source,'physics_result');assert result and result['signature']==physics.signature(source.ruin_settings)
    solid=bpy.data.objects[config.SOLID_NAME];assert solid.get('triangulacion_validada')
    bounds=[[min(v.co[i] for v in solid.data.vertices),max(v.co[i] for v in solid.data.vertices)] for i in range(3)]
    # Registrar tras cargar mantiene handlers y no altera las propiedades guardadas.
    assert len(result['poses'])==32
    bpy.ops.wm.stl_import(filepath=str(ROOT/'dist/ruinas_v0324_proceso_completo.stl'))
    imported=bpy.context.object;bm=bmesh.new();bm.from_mesh(imported.data)
    assert all(e.is_manifold for e in bm.edges)
    assert all(f.calc_area()>1e-12 for f in bm.faces);assert bm.calc_volume()>0
    bm.free()
    measured=[[min(v.co[i] for v in imported.data.vertices),max(v.co[i] for v in imported.data.vertices)] for i in range(3)]
    assert max(abs(a-b) for axis,target in zip(bounds,measured) for a,b in zip(axis,target))<.001
    report={'blend_reopened':True,'stl_reimported':True,'stl_closed':True,'poses_persist':True,'bounds_mm':measured,'triangles':len(imported.data.polygons)}
    (ROOT/'reports/room_reopen.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('ROOM_REOPEN_PASSED',report,flush=True)


if __name__=='__main__':run()
