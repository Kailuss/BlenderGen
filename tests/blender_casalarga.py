"""Reproduce la preparación del archivo aportado sin sobrescribirlo."""
import sys,json,time
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import ruinas_panel as addon
from ruinas_panel import config,runtime
from ruinas_panel.services import structural_physics


def run():
    'IA: Prepara la fuente real o regenerada, registra parámetros y coste y guarda solo un resultado nuevo en dist.'
    addon.register();runtime.busy=True;runtime.preview=True
    coll=bpy.data.collections.get(config.COLLECTION)
    scene=next(s for s in bpy.data.scenes if coll and any(o.name in s.objects for o in coll.objects));bpy.context.window.scene=scene
    p=scene.ruin_settings;p.live_preview=False
    params={k:getattr(p,k) for k in config.FIELDS}
    (ROOT/'reports/casalarga_parameters.json').write_text(json.dumps(params,indent=2),encoding='utf8')
    if '--regenerate' in sys.argv:addon.generate(bpy.context,p,'WORK')
    started=time.perf_counter();lab=structural_physics.prepare(scene)
    bpy.context.window.scene=lab
    (ROOT/'reports/casalarga_preparation.json').write_text(lab['preparation_report'],encoding='utf8')
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'dist/ruinas_v03212_casalarga_laboratorio.blend'))
    print('CASALARGA_PREPARED',time.perf_counter()-started,flush=True)


if __name__=='__main__':run()
