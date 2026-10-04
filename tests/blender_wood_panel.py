"""Relieve imprimible de tabiques sin booleanos."""
import sys
from pathlib import Path
import bpy,bmesh
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from ruinas_panel.structure.interiors import wood_panel
from ruinas_panel.geometry import primitives


def run():
    'IA: Dos orientaciones y veta 0/1: malla cerrada tras triangular, caras positivas, mínimo 2,3 mm y topología constante.'
    coll=bpy.data.collections.new('Wood test');bpy.context.scene.collection.children.link(coll)
    mat=primitives.material('Madera · interior',(.37,.255,.145))
    for axis in ('x','y'):
        counts=[];coords=[]
        for grain in (0,1):
            ob=wood_panel(coll,mat,{'axis':axis,'fixed':10},0,42,3,54,grain,17)
            bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.triangulate(bm,faces=list(bm.faces))
            assert all(e.is_manifold for e in bm.edges)
            assert all(f.calc_area()>1e-8 for f in bm.faces)
            assert bm.calc_volume()>0
            bm.free();counts.append(len(ob.data.polygons));coords.append([tuple(v.co) for v in ob.data.vertices])
            n=len(ob.data.vertices)//2;cross=1 if axis=='x' else 0
            assert min(ob.data.vertices[i+n].co[cross]-ob.data.vertices[i].co[cross] for i in range(n))>=2.2999
        assert counts[0]==counts[1] and coords[0]!=coords[1]
    print('WOOD_PANEL_PASSED',flush=True)


if __name__=='__main__':run()
