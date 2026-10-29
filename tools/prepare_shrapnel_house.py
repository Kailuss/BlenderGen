"""Auditoría de la casa completa y preparación sin regenerar geometría."""
import sys,json
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests'),str(ROOT/'tools')]
import ruinas_panel as addon
from ruinas_panel import runtime,meta,config
from ruinas_panel.structure import layout
from blender_probe import closure
from build_meteor_tower import wait_job
addon.register();runtime.busy=runtime.preview=True
s=bpy.context.scene;p=s.ruin_settings
coll=bpy.data.collections[config.COLLECTION]
windows=meta.get(s,'ventanas_generadas',[])
conflicts=[(a,b) for i,a in enumerate(windows) for b in windows[i+1:] if layout.openings_conflict(p,a,b)]
sealed=closure(coll)
report={'conflicts':conflicts,'closure':sealed,'openings':len(windows),'stairs':meta.get(s,'escaleras_generadas',[])}
(ROOT/'reports/ejercicio02_source_audit.json').write_text(json.dumps(report,indent=2),encoding='utf8')
assert not conflicts,conflicts
assert not sealed['open_edges'],sealed
assert len(report['stairs'])==2,report['stairs']
print('SOURCE_AUDIT_PASSED',len(windows),sealed,flush=True)
if '--prepare' in sys.argv:
    lab,peak=wait_job(s,'PREPARE');lab.name='02 · Laboratorio tres impactos'
    bpy.context.window.scene=lab
    report['preparation']=json.loads(lab['preparation_report']);report['prepare_peak_mb']=peak
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'dist/Ejercicio02_metralla_20261028/02_laboratorio_base.blend'))
    (ROOT/'reports/ejercicio02_source_audit.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print('PREPARE_PASSED',report['preparation'],flush=True)
