"""Torreón, pasos 6 a 8: forjados sobre ménsulas, escalera de caracol, terraza de losas y escombro interior caído desde el generador del panel."""
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
    'IA: Genera torre circular y cuadrada con interior (intacta con terraza, ruina leve y fuerte con escombro caído sin choques), exige mallas cerradas, volumen positivo, peldaños sin chocar con madera ni ménsulas y algo perdido con ruina fuerte; guarda .blend y vista en corte.'
    bpy.ops.wm.read_factory_settings(use_empty=True);addon.register();runtime.preview=True
    scene=bpy.context.scene;p=scene.ruin_settings;p.preview_quality='DRAFT';p.seed=11;p.wear_level='CUSTOM';p.wear=0.
    p.tower_floors=3;p.tower_height=120;report={}
    out=ROOT/'dist'/'pruebas';out.mkdir(parents=True,exist_ok=True)
    for shape,size in (('ROUND',60),('SQUARE',56),('ROUND',40)):
        for ruin in (0.,.35,.85):
            p.tower_shape=shape;p.tower_size=size;p.tower_ruin=ruin
            result=tower_building.generate(scene,p);coll=bpy.data.collections[tower_building.COLLECTION]
            sealed=closure(coll);assert not sealed['open_edges'],sealed
            pieces=[o for o in coll.objects if o.type=='MESH']
            for ob in pieces:
                if ob.name.startswith(('Madera','Piedra · peldaño','Piedra · losa')) or ob.get('corbel'):
                    bm=bmesh.new();bm.from_mesh(ob.data);volume=bm.calc_volume(signed=True);bm.free()
                    assert volume>0,(ob.name,volume)
            fallen=[o for o in pieces if o.get('tower_fallen')]
            steps=[o for o in pieces if o.name.startswith('Piedra · peldaño') and not o.get('tower_fallen')]
            others=[o for o in pieces if (o.name.startswith(('Madera','Piedra · losa')) or o.get('corbel')) and not o.get('tower_fallen')]
            trees={o.name:shrunk_tree(o) for o in steps+others+fallen}
            clashes=[(s.name,o.name) for s in steps for o in others if trees[s.name].overlap(trees[o.name])]
            # El escombro caído no atraviesa peldaños, madera, losas, ménsulas ni otro escombro.
            clashes+=[(f.name,o.name) for i,f in enumerate(fallen) for o in steps+others+fallen[:i] if trees[f.name].overlap(trees[o.name])]
            assert not clashes,clashes[:5]
            inside=result['interior']
            if ruin==0:assert inside['terrace'] and inside['slabs']>=(15 if size>=50 else 5),inside
            if ruin>.5:assert inside['fallen']>0 and inside['fallen']==len(fallen),inside
            # Lo que no cupo dentro está en el montón del pie: maderos cerrados con volumen, posados en la tierra.
            heap=[o for o in pieces if o.get('tower_heap')]
            if ruin>.5:assert inside['outside']['wood']<3 or heap,(inside,len(heap))
            for ob in heap:
                bm=bmesh.new();bm.from_mesh(ob.data);volume=bm.calc_volume(signed=True);bm.free()
                assert volume>0 and min(v.co.z for v in ob.data.vertices)>=.04-1e-6,(ob.name,volume)
            inside['heap_timber']=len(heap)
            # Los maderos del montón no se cruzan con las piedras partidas ni entre sí (encogidos: los contactos no cuentan).
            heap_stones=[o for o in pieces if o.get('escombro') and o.name.startswith('Piedra') and not o.get('tower_fallen')]
            heap_trees={o.name:shrunk_tree(o) for o in heap+heap_stones}
            crossing=[(a.name,b.name) for i,a in enumerate(heap) for b in heap_stones+heap[:i] if heap_trees[a.name].overlap(heap_trees[b.name])]
            assert not crossing,crossing[:5]
            if ruin==0 and size<50:assert inside['ladders']>=2 and inside['steps']==0,inside
            if ruin<.5 and size>=50:assert inside['beams']>=4 and inside['boards']>=10 and inside['steps']>=20,inside
            name=shape.lower()+('' if size>=50 else str(int(size)));key='%s_%s'%(name,ruin);report[key]=inside
            print('TOWER_INTERIOR',key,inside,flush=True)
            if ruin in (0.,.35,.85):
                tag={0.:'terraza',.35:'ruina',.85:'derrumbe'}[ruin]
                bpy.ops.wm.save_as_mainfile(filepath=str(out/('torreon_paso8_%s_%s.blend'%(name,tag))),copy=True)
                # Vista en corte: se ocultan las piezas de muro de la mitad delantera para ver forjados y escalera.
                # Se ocultan todos los núcleos (anillos que taparían el corte) y escombro y piedras de la mitad delantera.
                for ob in pieces:
                    if ob.name.startswith(('Madera','Piedra · peldaño','Piedra · losa')):continue
                    ys=[v.co.y for v in ob.data.vertices]
                    if ob.get('tower_fallen'):continue
                    ob.hide_render=ob.name.startswith('Mortero') or bool(ob.get('escombro')) or sum(ys)/len(ys)<0
                render(scene,ROOT/('reports/tower_interior_%s_%s.png'%(name,tag)),focus=(0,0,62),location=(60,-300,150),scale=150)
    (ROOT/'reports/tower_interior.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print('TOWER_INTERIOR_PASSED',flush=True)


if __name__=='__main__':run()
