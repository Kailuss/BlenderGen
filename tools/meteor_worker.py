"""Trabajador de ensayo que deja poses de control durante el cálculo completo."""
import sys,inspect,json,os
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import bpy,ruinas_panel as addon
from ruinas_panel.services import physics_worker
addon.register()
args=sys.argv[sys.argv.index('--')+1:]
original=physics_worker.progress

def observed(path,**status):
    'IA: Conserva poses de diagnóstico, sin tocar escena ni solver; el llamador es exclusivamente physics_worker.run.'
    original(path,**status)
    frame=status.get('frame')
    if status.get('stage')=='Simulando' and frame in (30,36,45,60,120):
        state=inspect.currentframe().f_back.f_locals
        np.savez_compressed(ROOT/f'reports/meteor_v2_poses_{frame}.npz',poses=state['poses'][:frame],names=np.array([o.name for o in state['objects']]))
physics_worker.progress=observed
physics_worker.run(Path(args[0]),Path(args[1]),args[2])
print('OBSERVED_WORKER_SAVED',flush=True)
sys.stdout.flush();os._exit(0)
