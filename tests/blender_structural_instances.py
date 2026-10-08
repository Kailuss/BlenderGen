"""Preparación física desde la vista habitual agrupada con Geometry Nodes."""
import sys,json
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'tests'))
import ruinas_panel as addon
from ruinas_panel import runtime
from ruinas_panel.services import structural_physics
from blender_probe import digest


def run():
    'IA: Verifica materialización real de GN sin alterar fuente ni depender de desactivar agrupación; conserva sólidos y sus identidades.'
    bpy.ops.wm.read_factory_settings(use_empty=True);addon.register();runtime.busy=True;runtime.preview=True
    source=bpy.context.scene;p=source.ruin_settings;p.live_preview=False;p.length=80;p.height_type='RUIN';p.layout_mode='NONE'
    p.damage_enabled=False;p.use_instances=True;p.batch_preview=True;p.roof_frame=False;p.door_enabled=False;p.windows_enabled=False
    coll=addon.generate(bpy.context,p,'WORK');assert any(o.get('ruin_instances') for o in coll.objects)
    initial=digest(coll);lab=structural_physics.prepare(source);assert digest(coll)==initial
    report=json.loads(lab['preparation_report']);assert report['roles']['stone']>20 and report['binder_excluded']>0
    assert all(o.get('source_piece') for o in lab.objects if o.rigid_body)
    print('STRUCTURAL_INSTANCES_PASSED',report,flush=True)


if __name__=='__main__':run()
