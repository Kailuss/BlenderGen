"""Cruces soldados de balcones: no restar tubos finos entre sí."""
import sys,json
from pathlib import Path
from types import SimpleNamespace
import bpy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'tests'))
import ruinas_panel as addon
from ruinas_panel import config,runtime
from ruinas_panel.geometry import primitives,balconies
from ruinas_panel.services import structural_physics
from blender_probe import digest

def run():
    'IA: Conserva balcones torcidos y partidos en física; comprueba uniones soldadas sin colisión y fuente intacta.'
    bpy.ops.wm.read_factory_settings(use_empty=True);addon.register();runtime.instance_build=True
    source=bpy.context.scene;source.ruin_settings.live_preview=False
    coll=bpy.data.collections.new(config.COLLECTION);source.collection.children.link(coll)
    stone=primitives.material('Piedra',(.5,.5,.5))
    primitives.block('Piedra muro',0,140,-4.5,4.5,0,100,coll,stone)
    for i,mode in enumerate(('TWIST','BROKEN')):
        p=SimpleNamespace(thickness=9,iron_damage='3',iron_mode=mode)
        w={'id':'front','origin':(i*65,0),'axis':(1,0)}
        balconies.balcony(coll,p,w,12,36,59,17)
    before=digest(coll);lab=structural_physics.prepare(source);assert digest(coll)==before
    report=json.loads(lab['preparation_report']);assert len(report['metal_welds'])>10
    welded=[o for o in lab.objects if o.rigid_body_constraint and not o.rigid_body_constraint.use_breaking]
    assert welded and all(o.rigid_body_constraint.disable_collisions for o in welded)
    weld_names={o.name for o in welded}
    structural_physics.optimise_collisions(lab)
    reduced=structural_physics.sparsify_constraints(lab)
    assert weld_names<={o.name for o in lab.objects if o.rigid_body_constraint},'Se pierden soldaduras al reducir contactos'
    assert structural_physics.sparsify_constraints(lab)==reduced,'La optimización debe ser idempotente'
    bpy.context.window.scene=lab
    for frame in range(1,25):lab.frame_set(frame)
    print('BALCONY_PHYSICS_PASSED',len(welded),flush=True)
if __name__=='__main__':run()
