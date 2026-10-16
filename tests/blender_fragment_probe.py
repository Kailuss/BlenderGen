"""Inspección de precisión de un componente aislado por booleanas."""
import sys,json
from pathlib import Path
import bpy,bmesh
from mathutils import Matrix,Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from ruinas_panel.services import structural_physics


def run():
    'IA: Compara volumen global y recentrado, cierre y extensión de un fragmento; no altera archivos aportados.'
    path=Path(sys.argv[sys.argv.index('--')+1]) if '--' in sys.argv else ROOT/'tests/fixtures/fragment_precision.json'
    record=json.loads(path.read_text(encoding='utf8'))
    mesh=bpy.data.meshes.new('fragment');mesh.from_pydata(record['vertices'],[],record['faces']);mesh.update()
    closed,volume=structural_physics.component_measure(mesh)
    assert closed and volume<1e-7,(closed,volume)
    bm=bmesh.new();bm.from_mesh(mesh)
    print('FRAGMENT',record['name'],'global',bm.calc_volume(),'closed',all(e.is_manifold for e in bm.edges),'edges',[(e.index,len(e.link_faces)) for e in bm.edges if not e.is_manifold],flush=True)
    center=sum((v.co for v in bm.verts),Vector())/len(bm.verts)
    print('BOUNDS',[max(v.co[k] for v in bm.verts)-min(v.co[k] for v in bm.verts) for k in range(3)],flush=True)
    bm.transform(Matrix.Translation(-center));print('LOCAL',bm.calc_volume(),flush=True)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));print('NORMALS',bm.calc_volume(),flush=True)
    print('FACES',record['faces'],'VERTS',record['vertices'],flush=True);bm.free()


if __name__=='__main__':run()
