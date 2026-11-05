"""Torreón, paso 6: forjados sobre ménsulas y escalera de caracol desde el generador del panel."""
import sys,json
from pathlib import Path
import bpy,bmesh
import numpy as np
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'tests'))
import ruinas_panel as addon
from ruinas_panel import runtime
from ruinas_panel.structure import tower_building
from blender_probe import closure
from blender_v032 import render


def shrunk_tree(ob,factor=.97):
    'IA: Árbol BVH de la pieza encogida hacia su centro, para que los contactos cara con cara no cuenten como choque.'
    co=np.array([v.co[:] for v in ob.data.vertices]);centre=co.mean(axis=0)
    co=centre+(co-centre)*factor
    return BVHTree.FromPolygons([tuple(c) for c in co],[tuple(p.vertices) for p in ob.data.polygons])


def run():
    'IA: Genera torre circular y cuadrada con interior (ruina leve y fuerte), exige mallas cerradas, volumen positivo, peldaños sin chocar con madera ni ménsulas y algo perdido con ruina fuerte; guarda .blend y vista en corte.'
    bpy.ops.wm.read_factory_settings(use_empty=True);addon.register();runtime.preview=True
    scene=bpy.context.scene;p=scene.ruin_settings;p.preview_quality='DRAFT';p.seed=11;p.wear_level='CUSTOM';p.wear=0.
    p.tower_floors=3;p.tower_height=120;report={}
    out=ROOT/'dist'/'pruebas';out.mkdir(parents=True,exist_ok=True)
    for shape,size in (('ROUND',60),('SQUARE',56)):
        for ruin in (.35,.85):
            p.tower_shape=shape;p.tower_size=size;p.tower_ruin=ruin
            result=tower_building.generate(scene,p);coll=bpy.data.collections[tower_building.COLLECTION]
            sealed=closure(coll);assert not sealed['open_edges'],sealed
            pieces=[o for o in coll.objects if o.type=='MESH']
            for ob in pieces:
                if ob.name.startswith(('Madera','Piedra · peldaño')) or ob.get('corbel'):
                    bm=bmesh.new();bm.from_mesh(ob.data);volume=bm.calc_volume(signed=True);bm.free()
                    assert volume>0,(ob.name,volume)
            steps=[o for o in pieces if o.name.startswith('Piedra · peldaño')]
            others=[o for o in pieces if o.name.startswith('Madera') or o.get('corbel')]
            trees={o.name:shrunk_tree(o) for o in steps+others}
            clashes=[(s.name,o.name) for s in steps for o in others if trees[s.name].overlap(trees[o.name])]
            assert not clashes,clashes[:5]
            inside=result['interior']
            if ruin<.5:assert inside['beams']>=4 and inside['boards']>=10 and inside['steps']>=20,inside
            key='%s_%s'%(shape.lower(),ruin);report[key]=inside
            print('TOWER_INTERIOR',key,inside,flush=True)
            if ruin<.5:
                bpy.ops.wm.save_as_mainfile(filepath=str(out/('torreon_paso6_%s.blend'%shape.lower())),copy=True)
                # Vista en corte: se ocultan las piezas de muro de la mitad delantera para ver forjados y escalera.
                # Se ocultan todos los núcleos (anillos que taparían el corte) y escombro y piedras de la mitad delantera.
                for ob in pieces:
                    if ob.name.startswith(('Madera','Piedra · peldaño')):continue
                    ys=[v.co.y for v in ob.data.vertices]
                    ob.hide_render=ob.name.startswith('Mortero') or bool(ob.get('escombro')) or sum(ys)/len(ys)<0
                render(scene,ROOT/('reports/tower_interior_%s.png'%shape.lower()),focus=(0,0,60),location=(60,-300,110),scale=140)
    (ROOT/'reports/tower_interior.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print('TOWER_INTERIOR_PASSED',flush=True)


if __name__=='__main__':run()
