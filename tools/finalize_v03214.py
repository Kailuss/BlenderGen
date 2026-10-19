"""Verificación de reapertura y manual dentro de la entrega integrada."""
import sys,json
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import ruinas_panel as addon


def run():
    'IA: Reabre la entrega, exige cuatro escenas y STL cerrado, añade instrucciones sin regenerar y deja activa la fuente editable.'
    addon.register()
    source=bpy.data.scenes['01 · Casa editable']
    lab=bpy.data.scenes['02 · Laboratorio']
    replay=bpy.data.scenes['03 · Zarandeo calculado']
    solid=bpy.data.scenes['04 · Sólido frame 10']
    assert json.loads(solid['physical_export_report'])['closed']
    assert all(len([o for o in scene.objects if o.type=='CAMERA'])==3 for scene in (lab,replay))
    text=bpy.data.texts.get('LEEME · Ruinas 0.32.14') or bpy.data.texts.new('LEEME · Ruinas 0.32.14')
    text.clear();text.write((ROOT/'docs/MANUAL_V03214.md').read_text(encoding='utf8'))
    replay.frame_set(1);bpy.context.window.scene=source;source['delivery_build']='0.32.14'
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'dist/ruinas_v03214_integrada.blend'))
    print('DELIVERY_REOPEN_PASSED',flush=True)


if __name__=='__main__':run()
