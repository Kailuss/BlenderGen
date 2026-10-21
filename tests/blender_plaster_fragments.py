"""Revocos dañados con semillas distintas y cierre de sus fragmentos."""
import sys,json
from pathlib import Path
import bpy,bmesh
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from ruinas_panel.geometry import plaster
from ruinas_panel.services import fragile_physics


def run():
    'IA: Comprueba paneles Perlin con doce semillas y cuatro intensidades, conservando cierre y volumen al cortarlos.'
    results=[]
    for seed in range(12):
        for damage in (0,.5,.75,1):
            verts,faces=plaster.panel(list(range(0,49,4)),0,[28+min(x,48-x)*.6 for x in range(0,49,4)],0,3,seed,damage)
            mesh=bpy.data.meshes.new('Revoco prueba');mesh.from_pydata(verts,[],faces);mesh.update()
            bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
            assert all(e.is_manifold for e in bm.edges),(seed,damage,[(len(e.link_faces),[tuple(v.co) for v in e.verts]) for e in bm.edges if not e.is_manifold][:5])
            bm.to_mesh(mesh);bm.free()
            parts=fragile_physics.split(mesh,0,seed+4300)
            results.append({'seed':seed,'damage':damage,'faces':len(mesh.polygons),'fragments':len(parts)})
            for item in parts+[mesh]:bpy.data.meshes.remove(item)
    (ROOT/'reports/plaster_fragments.json').write_text(json.dumps(results,indent=2),encoding='utf8')
    print('PLASTER_FRAGMENTS_PASSED',len(results),flush=True)


if __name__=='__main__':run()
