"""Regresión de conductos largos: cierre, volumen y paso libre después de prefractura."""
import sys,json
from pathlib import Path
import bpy,bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import ruinas_panel as addon
from ruinas_panel import runtime
from ruinas_panel.geometry import primitives
from ruinas_panel.structure import roof_accessories
from ruinas_panel.services import fragile_physics


def run():
    'IA: Ocho conductos en dos alturas y orientaciones conservan volumen y luz central; la fuente no se modifica.'
    addon.register();runtime.busy=runtime.preview=True;runtime.instance_build=True
    coll=bpy.data.collections.new('Regresión conductos');bpy.context.scene.collection.children.link(coll)
    mat=primitives.material('Piedra',(.5,.5,.5));results=[]
    for height in (80,420):
        for normal in ((0,1),(1,0)):
            for seed in range(2):
                name='Hogar · conducto interior %s %s %s'%(height,normal,seed)
                source=roof_accessories.ring(coll,mat,dict(x=140,y=30,normal=normal),name,(14,10),(14,10),3,height+3,2)
                points=[tuple(v.co) for v in source.data.vertices]
                bm=bmesh.new();bm.from_mesh(source.data);before=bm.calc_volume();bm.free()
                copy=bpy.data.objects.new(name+' copia',source.data.copy());coll.objects.link(copy)
                copy['physical_role']='stone';copy['source_piece']=name
                report={};parts=fragile_physics.fragment([copy],coll,report,40)
                total=0
                for ob in parts:
                    bm=bmesh.new();bm.from_mesh(ob.data)
                    assert all(e.is_manifold for e in bm.edges),ob.name
                    assert bm.calc_volume()>0,ob.name
                    total+=bm.calc_volume();bm.free()
                    tree=BVHTree.FromPolygons([v.co for v in ob.data.vertices],[list(p.vertices) for p in ob.data.polygons])
                    assert tree.ray_cast(Vector((140,30,height+8)),Vector((0,0,-1)),height+10)[0] is None,ob.name
                assert abs(total-before)<max(.001,before*.0001),(before,total)
                assert points==[tuple(v.co) for v in source.data.vertices]
                results.append(dict(height=height,normal=normal,seed=seed,fragments=len(parts),relative_volume_error=abs(total-before)/before))
    (ROOT/'reports/tall_conduit.json').write_text(json.dumps(results,indent=2),encoding='utf8')
    print('TALL_CONDUIT_PASSED',results,flush=True)


if __name__=='__main__':run()
