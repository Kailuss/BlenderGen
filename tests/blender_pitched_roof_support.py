"""Cubierta inclinada (roof.py): tras el derrumbe, ningún durmiente ni tirante de cercha queda sobre un hueco."""
import sys,json
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'tests'))
import ruinas_panel as addon
from ruinas_panel import runtime,meta
from ruinas_panel.geometry import primitives
from ruinas_panel.structure import roof
from blender_probe import closure


def masonry_tree(coll):
    'IA: Auditoría independiente: un solo BVH con toda la piedra y pilares finales (sin escombro ni mortero).'
    verts=[];polys=[]
    for ob in coll.objects:
        if ob.type!='MESH' or ob.get('escombro'):continue
        if not primitives.piece_key(ob).startswith(('Piedra','Pilar')):continue
        mw=ob.matrix_world;start=len(verts)
        verts+=[tuple(mw@v.co) for v in ob.data.vertices];polys+=[tuple(start+i for i in p.vertices) for p in ob.data.polygons]
    return BVHTree.FromPolygons(verts,polys)


def seat(tree,points,gap=.6):
    'IA: Fracción de puntos de la base con piedra a menos de gap mm debajo (o embebidos).'
    return sum(tree.ray_cast(Vector((x,y,z+3)),Vector((0,0,-1)),3+gap)[0] is not None for x,y,z in points)/max(1,len(points))


def audit(coll,p,scene):
    'IA: Devuelve durmientes por debajo de PLATE_SEAT y tirantes sin ninguna cabeza con TIE_SEAT, medidos contra toda la piedra final.'
    tree=masonry_tree(coll);walls={w['id']:w for w in meta.get(scene,'paredes_generadas',[])}
    x0,x1=walls['left']['origin'][0],walls['right']['origin'][0];t=p.thickness;bad=[];plates=[]
    for ob in coll.objects:
        key=primitives.piece_key(ob);co=primitives.coords(ob) if ob.type=='MESH' else []
        if not len(co):continue
        zb=float(co[:,2].min())
        if key.startswith('Madera · durmiente de alero'):
            f=seat(tree,[(float(co[:,0].mean()),y,zb) for y in np.linspace(co[:,1].min()+.3,co[:,1].max()-.3,12)]);plates.append(f)
            if f<roof.PLATE_SEAT:bad.append((ob.name,round(f,2)))
        elif key.startswith('Madera · cercha cubierta') and co[:,2].max()-co[:,2].min()<=6:
            xa,xb=float(co[:,0].min()),float(co[:,0].max());ya,yb=float(co[:,1].min()),float(co[:,1].max());ends=[]
            for wall_x in (x0,x1):
                lo,hi=max(xa,wall_x-t/2),min(xb,wall_x+t/2)
                if hi-lo<.6:continue
                ends.append(seat(tree,[(x,y,zb) for x in np.linspace(lo+.2,hi-.2,4) for y in np.linspace(ya+.3,yb-.3,3)]))
            if not ends or max(ends)<roof.TIE_SEAT:bad.append((ob.name,ends))
    return bad,plates


def run():
    'IA: Casa con cubierta inclinada, intacta y con derrumbes 0,1–0,6 en varias semillas: nada de la cubierta sobre huecos; intacta no retira nada; mallas cerradas.'
    bpy.ops.wm.read_factory_settings(use_empty=True);addon.register();runtime.busy=True;runtime.preview=True
    scene=bpy.context.scene;p=scene.ruin_settings;p.live_preview=False
    for key,value in dict(layout_mode='ROOM',height_type='TWO',roof_type='PITCHED',roof_frame=True,roof_tiles=True,stair_type='NONE',
                          windows_enabled=False,cracks=0,rubble_amount=0,ground_roughness=0,batch_preview=False,use_instances=False).items():setattr(p,key,value)
    cases=[]
    for seed,collapse in ((17,0.),(17,.1),(17,.2),(17,.3),(3,.3),(29,.45),(41,.6)):
        p.seed=seed;p.collapse=collapse
        coll=addon.generate(bpy.context,p,'DRAFT')
        bad,plates=audit(coll,p,scene);removed=meta.get(scene,'cubierta_sin_apoyo',[])
        assert not bad,(seed,collapse,bad[:6])
        if collapse==0:assert not removed,removed
        sealed=closure(coll);assert not sealed['open_edges'],sealed
        cases.append({'seed':seed,'collapse':collapse,'removed':len(removed),'plates':len(plates),'plate_min':round(min(plates),2) if plates else None,
                      'trusses':meta.get(scene,'cubierta_detalles',{}).get('supported_trusses')})
        print('PITCHED_SUPPORT',json.dumps(cases[-1]),flush=True)
    (ROOT/'reports/pitched_roof_support.json').write_text(json.dumps(cases,indent=2),encoding='utf8')
    print('PITCHED_SUPPORT_PASSED',flush=True)


if __name__=='__main__':run()
