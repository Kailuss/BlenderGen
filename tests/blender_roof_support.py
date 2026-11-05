"""Regresión «imposible.blend»: ninguna pieza de terraza de torreón sin apoyo real tras el derrumbe."""
import sys,json
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'tests'))
import ruinas_panel as addon
from ruinas_panel import runtime,meta
from ruinas_panel.structure import tower_roof
from ruinas_panel.construction_core import roof_support
from blender_probe import closure


def floating(coll,p):
    'IA: Reclasifica la cubierta final contra la fábrica final (sin instancias agrupadas); devuelve las piezas que seguirían sin apoyo.'
    roof={o for o in coll.objects if o.get('roof_timber') or o.get('tower_part') in ('deck','parapet','merlon')}
    before=set(coll.objects)-roof
    pieces,_=tower_roof.roof_pieces(coll,before)
    return roof_support.unsupported(pieces,tower_roof.masonry_boxes(coll,before),p.thickness/2),len(pieces)


def run():
    'IA: Torreón de Muralla de tres plantas como el caso real (semilla 17, derrumbe 0,30) y un barrido; intacto no pierde nada; dañado no deja nada flotando.'
    bpy.ops.wm.read_factory_settings(use_empty=True);addon.register();runtime.busy=True;runtime.preview=True
    scene=bpy.context.scene;p=scene.ruin_settings;p.live_preview=False
    for key,value in dict(layout_mode='ROOM',height_type='THREE',build_type='FORTRESS',roof_type='TOWER',roof_frame=True,stair_type='NONE',
                          windows_enabled=False,cracks=0,rubble_amount=0,ground_roughness=0,batch_preview=False,use_instances=False).items():setattr(p,key,value)
    cases=[]
    # Derrumbes pequeños (0,05–0,15): parte de la terraza debe poder quedarse; los grandes la pierden entera.
    for seed,collapse in ((17,0.),(17,.05),(17,.10),(3,.15),(17,.30),(17,.60),(3,.30),(29,.30),(41,.45),(53,.60)):
        p.seed=seed;p.collapse=collapse
        coll=addon.generate(bpy.context,p,'DRAFT')
        left,total=floating(coll,p)
        details=meta.get(scene,'cubierta_detalles');removed=meta.get(scene,'cubierta_sin_apoyo',[])
        assert not left,(seed,collapse,left[:10])
        if collapse==0:assert not removed,removed
        sealed=closure(coll);assert not sealed['open_edges'],sealed
        cases.append({'seed':seed,'collapse':collapse,'roof_pieces':total,'removed_unsupported':len(removed),'deck':details['deck_slabs'],'parapet':details['parapet_blocks']})
        print('ROOF_SUPPORT',json.dumps(cases[-1]),flush=True)
    (ROOT/'reports/roof_support.json').write_text(json.dumps(cases,indent=2),encoding='utf8')
    print('ROOF_SUPPORT_PASSED',flush=True)


if __name__=='__main__':run()
