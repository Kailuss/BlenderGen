"""Reapertura del archivo entregado y comprobación de todas las etapas."""
import sys,json,struct,hashlib
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import ruinas_panel as addon
from ruinas_panel.services import physics


def run():
    'IA: Reabre la entrega, exige fuente parametrizada, laboratorio con cuerpos, reproducción sin física, sólido y STL íntegro con el mismo número de triángulos.'
    addon.register()
    names=('01 · Casa editable','02 · Laboratorio editable','03 · Reproducción','04 · Sólido exportado')
    assert all(name in bpy.data.scenes for name in names),list(bpy.data.scenes.keys())
    source,lab,replay,solid=[bpy.data.scenes[name] for name in names]
    assert physics.source_matches(lab) is True,'La fuente no corresponde al laboratorio entregado.'
    assert abs(source.ruin_settings.length-220)<1e-4 and source.ruin_settings.chimneys and source.ruin_settings.balconies
    bodies=sum(o.rigid_body is not None for o in lab.objects);assert bodies>5000
    assert not any(o.rigid_body for o in replay.objects)
    bpy.context.window.scene=replay;replay.frame_set(1);bpy.context.view_layer.update()
    positions={o.name:o.matrix_world.translation.copy() for o in replay.objects if o.type=='MESH'}
    replay.frame_set(72);bpy.context.view_layer.update()
    moved=sum((o.matrix_world.translation-positions[o.name]).length>.00002 for o in replay.objects if o.type=='MESH')
    assert moved>1000,moved
    report=json.loads(solid['physical_export_report']);assert report['closed'] and report['frame']==72
    target=ROOT/'dist/ruinas_v03211_integrada.stl'
    with target.open('rb') as stream:
        stream.seek(80);count=struct.unpack('<I',stream.read(4))[0]
    assert count==report['triangles'] and target.stat().st_size==84+50*count
    assert sum(len(o.data.polygons) for o in solid.objects if o.type=='MESH')==count
    assert 'Memoria y escala' in bpy.data.texts['LEEME · Prueba integrada'].as_string()
    result={'scenes':list(names),'source_matches':True,'build':addon.config.BUILD_ID,'lab_bodies':bodies,'moved':moved,'stl_triangles':count,'stl_bytes':target.stat().st_size}
    with Path(bpy.data.filepath).open('rb') as stream:result['blend_sha256']=hashlib.file_digest(stream,'sha256').hexdigest()
    (ROOT/'reports/delivery_audit.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    print('DELIVERY_AUDIT_PASSED',result,flush=True)


if __name__=='__main__':run()
