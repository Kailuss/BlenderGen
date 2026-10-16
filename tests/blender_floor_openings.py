"""Regresión de postes de refuerzo atravesando vanos."""
import sys
from pathlib import Path
import bpy
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'tests'))
import ruinas_panel as addon
from ruinas_panel import runtime,meta
from ruinas_panel.geometry import primitives
from ruinas_panel.structure import floors
from blender_probe import closure,digest


def run():
    'IA: Fuerza bastidor suplementario con puerta y ventanas opuestas; comprueba postes libres, cierre y caché en dos y tres plantas.'
    bpy.ops.wm.read_factory_settings(use_empty=True);addon.register();runtime.busy=True;runtime.preview=True
    scene=bpy.context.scene;p=scene.ruin_settings;p.live_preview=False
    for key,value in dict(layout_mode='ROOM',length=180,building_depth=120,pillar_count=0,door_enabled=True,windows_enabled=True,windows_per_wall=3,balconies=True,damage_enabled=False,ground_roughness=0,stair_type='NONE',batch_preview=False,use_instances=False).items():setattr(p,key,value)
    for height in ('TWO','THREE'):
        p.height_type=height
        with patch('ruinas_panel.structure.openings.beam_positions',return_value=[]):
            coll=addon.generate(bpy.context,p,'WORK')
        windows=meta.get(scene,'ventanas_generadas');door=meta.get(scene,'puerta_generada')
        posts=[o for o in coll.objects if primitives.piece_key(o)=='Madera · poste forjado'];assert posts
        for ob in posts:
            co=primitives.coords(ob);lo=co.min(axis=0);hi=co.max(axis=0)
            for h in windows:
                if h['wall'] not in ('front','back'):continue
                assert not (lo[0]<h['x1']+2 and hi[0]>h['x0']-2 and lo[2]<h['z1']+2 and hi[2]>h['z0']-2),(ob.name,h)
            assert not (lo[0]<door['right']+2 and hi[0]>door['left']-2 and lo[2]<door['top']+2),ob.name
        assert not closure(coll)['open_edges']
        before=digest(coll);assert digest(addon.generate(bpy.context,p,'WORK'))==before
        print('FLOOR_OPENINGS_PASSED',height,len(posts),flush=True)
    assert floors.support_positions([0],[],(-40,40),[],{'left':-10,'right':10,'top':40},0,50)==[-15]


if __name__=='__main__':run()
