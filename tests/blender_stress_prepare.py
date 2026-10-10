"""Preparación reproducible del escenario máximo guardado."""
import sys,time,json
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import ruinas_panel as addon
from ruinas_panel.services import structural_physics

def run():
    'IA: Materializa la casa máxima y guarda el laboratorio antes de simular; registra el coste y todas las familias presentes.'
    addon.register();source=bpy.context.scene;started=time.perf_counter()
    lab=structural_physics.prepare(source);bpy.context.window.scene=lab
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'dist/stress_max_lab.blend'))
    report=json.loads(lab['preparation_report']);report['total_seconds']=time.perf_counter()-started
    (ROOT/'reports/stress_max_preparation.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print('STRESS_PREPARED',report,flush=True)
if __name__=='__main__':run()
