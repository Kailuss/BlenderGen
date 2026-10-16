"""Añade instrucciones a la entrega sin reconstruir su geometría validada."""
import sys,json
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import ruinas_panel as addon


def run():
    'IA: Reabre las cuatro etapas, verifica enlaces/cámaras, añade manual de texto y guarda la entrega sobre sí misma con fuente activa.'
    addon.register()
    source=bpy.data.scenes['01 · Torre editable'];lab=bpy.data.scenes['02 · Laboratorio torre'];replay=bpy.data.scenes['03 · Zarandeo calculado'];solid=bpy.data.scenes['04 · Sólido frame 10']
    assert all(len([o for o in s.objects if o.type=='CAMERA'])==3 for s in (lab,replay))
    assert json.loads(solid['physical_export_report'])['closed']
    from ruinas_panel.services import physics
    assert physics.source_matches(lab) is not False
    replay.frame_set(1)
    text=bpy.data.texts.get('LEEME · Ruinas 0.32.12') or bpy.data.texts.new('LEEME · Ruinas 0.32.12')
    text.clear();text.write((ROOT/'docs/MANUAL_V03212.md').read_text(encoding='utf8'))
    source['delivery_build']='0.32.12';bpy.context.window.scene=source
    sys.path.insert(0,str(ROOT/'tests'))
    from blender_v032 import render
    from ruinas_panel import config
    coll=bpy.data.collections[config.COLLECTION];hidden={o:o.hide_render for o in coll.objects}
    try:
        for ob in coll.objects:ob.hide_render=not ('Madera' in ob.name or 'Escalera' in ob.name)
        render(source,ROOT/'reports/v03212_tower_interior.png',focus=(0,70,90),location=(290,350,270),scale=300)
    finally:
        for ob,value in hidden.items():ob.hide_render=value
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'dist/ruinas_v03212_torre_integrada.blend'))
    print('DELIVERY_REOPEN_PASSED',flush=True)


if __name__=='__main__':run()
