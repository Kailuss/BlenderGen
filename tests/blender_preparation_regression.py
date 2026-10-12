"""Regresión del ladrillo cuya triangulación creaba caras opuestas duplicadas."""
import sys,json
from pathlib import Path
import bpy,bmesh
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from ruinas_panel.services import structural_physics


def run():
    'IA: El caso real conserva coordenadas y volumen al triangular; una cara ausente no se rellena para forzar la validación.'
    data=json.loads((ROOT/'tests/fixtures/triangulation_back_stone.json').read_text(encoding='utf8'))
    mesh=bpy.data.meshes.new('Regresión');mesh.from_pydata(data['vertices'],[],data['faces'])
    bm=bmesh.new();bm.from_mesh(mesh);assert all(e.is_manifold for e in bm.edges);bmesh.ops.triangulate(bm,faces=list(bm.faces));assert any(not e.is_manifold for e in bm.edges);before=bm.calc_volume();bm.free();assert before>0
    coordinates=[tuple(v.co) for v in mesh.vertices]
    structural_physics.triangulate(mesh);after=structural_physics.valid(mesh)
    assert after>0 and abs(before-after)<1e-5
    assert coordinates==[tuple(v.co) for v in mesh.vertices]
    bm=bmesh.new();bm.from_mesh(mesh);bm.faces.ensure_lookup_table();bmesh.ops.delete(bm,geom=[bm.faces[0]],context='FACES_ONLY');bm.to_mesh(mesh);bm.free()
    structural_physics.triangulate(mesh);assert not structural_physics.valid(mesh)
    print('PREPARATION_REGRESSION_PASSED',before,after,flush=True)


if __name__=='__main__':run()
