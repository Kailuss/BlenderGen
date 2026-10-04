"""Comprobación del encaje entre filas de tejas."""
import sys
from pathlib import Path
from types import SimpleNamespace
import bpy
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from ruinas_panel.structure import roof
from ruinas_panel.geometry import primitives


def run():
    'IA: Detecta cruces triangulares entre la superficie de tejas de filas consecutivas en la misma columna.'
    for curve,edge in ((c,e) for c in (0,.6,1) for e in (-55,55)):
        coll=bpy.data.collections.new('test');bpy.context.scene.collection.children.link(coll)
        p=SimpleNamespace(roof_curve=curve,wood_damage=0,wear=0)
        mat=primitives.material('Tejas',(.4,.2,.1))
        roof.tile_bay(coll,mat,p,edge,0,0,11,59.2,52,13,1)
        ob=list(coll.objects)[0];meshes=[]
        for i in range(ob['tile_count']):
            vertices=[tuple(v.co) for v in ob.data.vertices[i*36:(i+1)*36]]
            faces=[tuple(v-i*36 for v in f.vertices) for f in ob.data.polygons[i*34:(i+1)*34]]
            meshes.append(BVHTree.FromPolygons(vertices,faces))
        pairs=[i for i in range(len(meshes)-2) if meshes[i].overlap(meshes[i+2])]
        print('TILE_INTERSECTIONS',curve,pairs,flush=True)
        assert not pairs,(curve,pairs)
    coll=bpy.data.collections.new('ridge');bpy.context.scene.collection.children.link(coll)
    roof.ridge_cap(coll,mat,0,0,40,100)
    ob=list(coll.objects)[0];meshes=[]
    for i in range(ob['tile_count']):
        vertices=[tuple(v.co) for v in ob.data.vertices[i*36:(i+1)*36]]
        faces=[tuple(v-i*36 for v in f.vertices) for f in ob.data.polygons[i*34:(i+1)*34]]
        meshes.append(BVHTree.FromPolygons(vertices,faces))
    assert not any(a.overlap(b) for a,b in zip(meshes,meshes[1:])), 'cruce cumbrera'
    print('TILE_FIT_PASSED',flush=True)


if __name__=='__main__':run()
