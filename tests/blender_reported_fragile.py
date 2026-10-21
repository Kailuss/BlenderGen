"""Reproduce el fallo de revoco comunicado el 20 de octubre."""
import sys
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import ruinas_panel as addon
from ruinas_panel import runtime
from ruinas_panel.services import structural_physics,fragile_physics


def run():
    'IA: Prepara la instantánea del fallo con código fuente actual y conserva la malla exacta si la prefractura falla.'
    addon.register();runtime.busy=True
    source=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else r'C:\Users\yhora\AppData\Local\Temp\ruinas_physics_zih647eb\input.blend'
    bpy.ops.wm.open_mainfile(filepath=source)
    original=fragile_physics.split
    def capture(mesh,axis,seed):
        'IA: Guarda el sólido fallido y el plano reproducible antes de propagar el error.'
        try:return original(mesh,axis,seed)
        except Exception:
            ob=bpy.data.objects.new('FALLO_REVOCO',mesh.copy())
            bpy.context.scene.collection.objects.link(ob)
            ob['axis']=axis;ob['seed']=str(seed)
            bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'dist/repro_revoco.blend'))
            raise
    fragile_physics.split=capture
    result=structural_physics.prepare(bpy.context.scene)
    bpy.context.window.scene=result
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'dist/repro_revoco_laboratorio_corregido.blend'))
    print('REPORTED_PREPARE_PASSED',result,flush=True)


if __name__=='__main__':run()
