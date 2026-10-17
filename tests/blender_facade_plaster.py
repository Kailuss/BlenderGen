"""Daño reproducible y prefractura de los nuevos paños de mirador."""
import sys
from pathlib import Path
import bpy
import bmesh
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from ruinas_panel.geometry import plaster,primitives
from ruinas_panel.services import fragile_physics


def volume(ob):
    'IA: Exige sólidos cerrados y volumen positivo antes y después de fragmentar.'
    bm=bmesh.new();bm.from_mesh(ob.data)
    bmesh.ops.triangulate(bm,faces=list(bm.faces))
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data)
    assert all(e.is_manifold for e in bm.edges),ob.name
    result=bm.calc_volume();bm.free();assert result>0
    return result


def run():
    'IA: Verifica pérdida Perlin real, repetibilidad y conservación de volumen al prefracturar un panel; no depende del render.'
    bpy.ops.wm.read_factory_settings(use_empty=True)
    coll=bpy.data.collections.new('Ensayo revoco');bpy.context.scene.collection.children.link(coll)
    xs=list(range(0,41,4));args=(xs,0,[40]*len(xs),-1,1,173)
    intact=plaster.panel(*args,damage=0);damaged=plaster.panel(*args,damage=.95)
    assert damaged==plaster.panel(*args,damage=.95)
    mat=primitives.material('Revoco · cal',(.66,.60,.47))
    a=primitives.mesh_obj('Intacto',*intact,coll,mat)
    b=primitives.mesh_obj('Revoco · entreventana mirador',*damaged,coll,mat)
    before=volume(b);assert before<volume(a)*.95
    b['physical_role']='stone';report={}
    parts=fragile_physics.fragment([b],coll,report,size=20)
    assert len(parts)>1 and all(o['fragile_material']=='plaster' for o in parts)
    assert abs(sum(volume(o) for o in parts)-before)<before*.001
    print('FACADE_PLASTER_PASSED',len(parts),flush=True)


if __name__=='__main__':run()
