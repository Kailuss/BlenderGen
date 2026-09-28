"""Lee ajustes del archivo de referencia sin ejecutar sus textos embebidos."""
from pathlib import Path
import json
import sys
import bpy

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))


def run():
    """IA: inspecciona la escena aportada con use_scripts=False y guarda solo ajustes/metadatos para pruebas reproducibles."""
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'dist/reference_v031/ruina_v031.blend'),use_scripts=False)
    import ruinas_panel
    from ruinas_panel import config,meta,runtime
    ruinas_panel.register()
    runtime.busy=True
    p=bpy.context.scene.ruin_settings
    data={'settings':{k:getattr(p,k) for k in config.FIELDS},
          'walls':meta.get(bpy.context.scene,'paredes_generadas',[]),
          'windows':meta.get(bpy.context.scene,'ventanas_generadas',[]),
          'stairs':meta.get(bpy.context.scene,'escalera_generada',{}),
          'chimney':meta.get(bpy.context.scene,'chimeneas_generadas',[])}
    (ROOT/'reports/house_reference.json').write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps(data,ensure_ascii=False),flush=True)


if __name__=='__main__':run()
