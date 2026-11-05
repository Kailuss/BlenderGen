"""Torreón desde el panel: operador ruin.tower_generate en sus dos plantas."""
import sys,json
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'tests'))
import ruinas_panel as addon
from ruinas_panel.structure import tower_building
from blender_probe import closure


def run():
    'IA: Genera torre circular y cuadrada con el operador, exige mallas cerradas, una sola colección y piedras retiradas por la ruina.'
    bpy.ops.wm.read_factory_settings(use_empty=True);addon.register();scene=bpy.context.scene;p=scene.ruin_settings
    p.preview_quality='DRAFT';report={}
    for shape in ('ROUND','SQUARE'):
        p.tower_shape=shape;p.tower_ruin=.4;p.seed=11
        assert bpy.ops.ruin.tower_generate()=={'FINISHED'}
        coll=bpy.data.collections[tower_building.COLLECTION]
        assert sum(c.name.startswith(tower_building.COLLECTION) for c in bpy.data.collections)==1
        sealed=closure(coll);assert not sealed['open_edges'],sealed
        stones=sum(o.name.startswith('Piedra') for o in coll.objects);assert stones>50,stones
        report[shape]={'objects':len(coll.objects),'stones':stones}
        print('TOWER_OPERATOR',shape,report[shape],flush=True)
    print('TOWER_OPERATOR_PASSED',flush=True)


if __name__=='__main__':run()
