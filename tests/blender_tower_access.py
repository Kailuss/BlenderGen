"""Cotas extremas y recorrido del torreón en ambos sentidos."""
import sys
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'tests'))
import ruinas_panel as addon
from ruinas_panel import runtime,meta
from ruinas_panel.geometry import primitives
from blender_probe import closure


def run():
    'IA: Verifica madera y piedra, ambos sentidos y alturas máximas; losas no invaden el hueco y el grafo conecta las tres plantas con terraza.'
    bpy.ops.wm.read_factory_settings(use_empty=True);addon.register();runtime.busy=True;runtime.preview=True
    scene=bpy.context.scene;p=scene.ruin_settings;p.live_preview=False
    for key,value in dict(layout_mode='ROOM',height_type='THREE',length=180,building_depth=120,pillar_count=0,damage_enabled=False,windows_enabled=False,roof_frame=True,roof_type='TOWER',ground_floor=True,upper_floor=True,floor_beams=True,ground_roughness=0,batch_preview=False,use_instances=True).items():setattr(p,key,value)
    for kind,side,ground,upper in [('WOOD','RIGHT',35,75),('STONE','LEFT',75,75)]:
        p.stair_type=kind;p.stair_side=side;p.ground_storey_height=ground;p.upper_storey_height=upper
        coll=addon.generate(bpy.context,p,'WORK');assert p.height==2+ground+2*upper
        records=meta.get(scene,'escaleras_generadas');assert len(records)==3
        for a,b in zip(records,records[1:]):assert abs(a['top']-b['bottom'])<1e-6
        assert records[-1]['top']==p.height+7
        hole=meta.get(scene,'cubierta_detalles')['access_opening'];assert hole
        for ob in coll.objects:
            if ob.get('tower_part')!='deck':continue
            coords=primitives.coords(ob);lo=coords.min(axis=0);hi=coords.max(axis=0)
            assert not (lo[0]<hole[1]-.001 and hi[0]>hole[0]+.001 and lo[1]<hole[3]-.001 and hi[1]>hole[2]+.001),ob.name
        assert not closure(coll)['open_edges']
        assert ['stair.2','roof','access'] in meta.get(scene,'architectural_graph')['relations']
        print('TOWER_ACCESS_PASSED',kind,side,p.height,flush=True)


if __name__=='__main__':run()
