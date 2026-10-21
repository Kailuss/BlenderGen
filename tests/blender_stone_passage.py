"""Geometría de escalera de piedra y conservación de las tejas."""
import sys,json
from pathlib import Path
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'tests'))
import ruinas_panel as addon
from ruinas_panel import runtime,meta
from ruinas_panel.structure import roof,stairs,openings,layout
from ruinas_panel.geometry import primitives
from blender_probe import closure
from blender_v032 import render


def run():
    'IA: Verifica invariancia de distancias cerámicas y cierre de tres tramos de piedra con intradós hueco; guarda una vista para inspección.'
    addon.register();runtime.busy=True;runtime.preview=True
    scene=bpy.context.scene;p=scene.ruin_settings
    p.use_instances=False
    for key,value in dict(layout_mode='ROOM',height_type='THREE',length=190,building_depth=90,ground_storey_height=75,upper_storey_height=55,stair_type='STONE',roof_frame=True,roof_type='TOWER',collapse=0,hole_count=0,cracks=0,rubble_amount=0,ground_roughness=0,wood_damage=0,batch_preview=False).items():setattr(p,key,value)
    coll=addon.generate(bpy.context,p,'WORK')
    assert not closure(coll)['open_edges']
    plans=meta.get(scene,'escaleras_generadas',[])
    assert sum(bool(s.get('hollow')) for s in plans)>=2,plans
    walls=meta.get(scene,'paredes_generadas')
    back=next(w for w in walls if w['id']=='back');tree=openings.wall_tree(coll,back)
    checked=0
    for beam in meta.get(scene,'vigas_generadas',[]):
        base=min(layout.floor_bases(p)[1:],key=lambda z:abs(z-3.6-beam['z']))
        if stairs.beam_end(p,walls,beam['x'],base) is not None:
            assert any(openings.wall_hit(tree,back,p,beam['x']+dx,beam['z']+dz) for dx in (-1.5,1.5) for dz in (-1,0,1)),beam
            checked+=1
    assert checked
    trees=[(o.name,BVHTree.FromPolygons(primitives.coords(o).tolist(),[tuple(face.vertices) for face in o.data.polygons])) for o in coll.objects if o.type=='MESH' and o.data.polygons]
    clearance=[]
    for stair in plans[:-1]:
        a,b=stair['landing'];y=(stair['y0']+stair['y1'])/2
        for x in (a+3,(a+b)/2,b-3):
            origin=Vector((x,y,stair['top']+.2))
            blocked=[name for name,tree in trees if tree.ray_cast(origin,Vector((0,0,1)),35)[0] is not None]
            assert not blocked,(origin,blocked)
            clearance.append(list(origin))
    original_sag=roof.roof_damage.sag
    roof.roof_damage.sag=lambda x,y,patches: .8*x
    start,end=(0,0,20),(8,0,27)
    moved=roof.settled_tile(start,end,())
    roof.roof_damage.sag=original_sag
    before=[];after=[]
    roof.curved_tile(before,[],start,end,5,2)
    roof.curved_tile(after,[],*moved,5,2)
    error=max(abs((Vector(a)-Vector(b)).length-(Vector(c)-Vector(d)).length) for a,c in zip(before,after) for b,d in zip(before,after))
    assert error<1e-5,error
    hidden={o:o.hide_render for o in coll.objects}
    for ob in coll.objects:ob.hide_render=not ob.get('stair')
    render(scene,ROOT/'reports/stone_passage.png',focus=(0,55,90),location=(220,-220,220),scale=265)
    for ob,value in hidden.items():ob.hide_render=value
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'dist/ruinas_escalera_piedra_revision.blend'))
    (ROOT/'reports/stone_passage.json').write_text(json.dumps({'tile_distance_error_mm':error,'closed_unused_sockets':checked,'clearance_35mm_samples':clearance,'plans':plans},indent=2),encoding='utf8')
    print('STONE_AND_TILE_PASSED',flush=True)


if __name__=='__main__':run()
