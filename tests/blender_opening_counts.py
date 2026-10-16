"""Cuotas independientes y diagnóstico de balcones que no caben."""
import sys
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import ruinas_panel as addon
from ruinas_panel import runtime,meta


def run():
    'IA: Apagar ventanas conserva balcones; variar su cuota no cambia la otra y un acceso demasiado alto informa la limitación sin deformarlo.'
    bpy.ops.wm.read_factory_settings(use_empty=True);addon.register();runtime.busy=True;runtime.preview=True
    scene=bpy.context.scene;p=scene.ruin_settings;p.live_preview=False
    for key,value in dict(layout_mode='ROOM',height_type='TWO',length=180,building_depth=120,pillar_count=0,damage_enabled=False,windows_enabled=False,balconies=True,balconies_per_wall=1,ground_roughness=0,stair_type='NONE').items():setattr(p,key,value)
    addon.generate(bpy.context,p,'WORK');items=meta.get(scene,'ventanas_generadas');assert items and all(o['balcony'] for o in items)
    p.windows_enabled=True;p.windows_per_wall=2
    addon.generate(bpy.context,p,'WORK');items=meta.get(scene,'ventanas_generadas')
    assert any(not o['balcony'] for o in items)
    assert all(sum(o['wall']==wall and o['balcony'] for o in items)<=1 for wall in ('front','back','left','right'))
    p.balcony_height=100
    addon.generate(bpy.context,p,'WORK');items=meta.get(scene,'ventanas_generadas')
    assert items and not any(o['balcony'] for o in items)
    assert any(w['family']=='balcony' and w['reason']=='dimensions' for w in meta.get(scene,'vanos_limitaciones'))
    print('OPENING_COUNTS_PASSED',flush=True)


if __name__=='__main__':run()
