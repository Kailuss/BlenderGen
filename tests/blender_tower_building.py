"""Torreón, paso 2: mallas cerradas de torre circular y cuadrada desde el aparejo puro."""
import sys,json
from pathlib import Path
import bpy,bmesh
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'tests'))
import ruinas_panel as addon
from ruinas_panel import runtime
from ruinas_panel.geometry import primitives
from ruinas_panel.structure import tower_plan,tower_building
from blender_probe import closure
from blender_v032 import render


def run():
    'IA: Construye ambas torres (3 plantas, saeteras), exige mallas cerradas con volumen positivo y marcas de aparejo; renderiza dos vistas.'
    bpy.ops.wm.read_factory_settings(use_empty=True);addon.register();runtime.preview=True;runtime.quality='DRAFT'
    scene=bpy.context.scene;stone=primitives.material('Piedra · torreón',(.46,.45,.42));core=primitives.material('Núcleo · torreón',(.38,.37,.35))
    report={}
    for kind,plan,origin in (('round',tower_plan.round_plan(30,10,120,6.5,seed=7,slits=3,floors=3),(-45,0,0)),
                             ('square',tower_plan.square_plan(56,12,120,6.5,seed=7,slits=1,floors=3),(45,0,0))):
        coll=bpy.data.collections.new('Torreón '+kind);scene.collection.children.link(coll)
        made=(tower_building.build_round if kind=='round' else tower_building.build_square)(coll,plan,stone,core,origin)
        sealed=closure(coll);assert not sealed['open_edges'],sealed
        for ob in made:
            bm=bmesh.new();bm.from_mesh(ob.data);volume=bm.calc_volume(signed=True);bm.free()
            assert volume>0,(ob.name,volume)
            assert 'layout_kind' in ob
        report[kind]={'pieces':len(made),'stones':sum(o.name.startswith('Piedra') for o in made),'courses':len(plan)}
        print('TOWER_BUILDING',kind,report[kind],flush=True)
    render(scene,ROOT/'reports/tower_building.png',focus=(0,0,60),location=(220,-260,200),scale=230)
    (ROOT/'reports/tower_building.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print('TOWER_BUILDING_PASSED',flush=True)


if __name__=='__main__':run()
