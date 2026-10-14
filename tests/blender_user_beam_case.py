"""Reproducción del error de piedra junto a los alojamientos de entreplanta."""
import sys,json
from pathlib import Path
import bpy,bmesh
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import ruinas_panel as addon
from ruinas_panel import config,runtime
from ruinas_panel.services import structural_physics


def run():
    'IA: Audita la pieza de la captura antes y después de triangular, conserva el caso numérico y permite regenerar la fuente con el código corregido.'
    addon.register();runtime.busy=True;runtime.preview=True
    coll=bpy.data.collections.get(config.COLLECTION)
    scene=next(s for s in bpy.data.scenes if any(o.name in s.objects for o in coll.objects));bpy.context.window.scene=scene
    p=scene.ruin_settings;p.live_preview=False
    print('USER_SETTINGS',{key:getattr(p,key) for key in ('seed','length','height_type','ground_storey_height','upper_storey_height','building_depth','stone_size','bond_subdivisions','floor_beams','roof_curve')},flush=True)
    if '--regenerate' in sys.argv:coll=addon.generate(bpy.context,p,'WORK')
    for ob in coll.objects:
        records=json.loads(ob['ruin_parts']) if ob.get('ruin_batch') else [{'name':ob.name,'vertex_start':0,'vertex_count':len(ob.data.vertices)}]
        for record in records:
            if 'hilada 10.00' not in record['name']:continue
            mesh=structural_physics.extract(ob.data,list(range(record['vertex_start'],record['vertex_start']+record['vertex_count'])),record['name'])
            fixture={'vertices':[list(v.co) for v in mesh.vertices],'faces':[list(f.vertices) for f in mesh.polygons]}
            (ROOT/'reports/user_beam_piece.json').write_text(json.dumps(fixture),encoding='utf8')
            for method in ('BEAUTY','EAR_CLIP'):
                bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.triangulate(bm,faces=list(bm.faces),ngon_method=method)
                print('TRI_METHOD',method,sum(not e.is_manifold for e in bm.edges),bm.calc_volume(),flush=True);bm.free()
            for stage in ('original','triangulated'):
                if stage=='triangulated':structural_physics.triangulate(mesh)
                bm=bmesh.new();bm.from_mesh(mesh)
                print('USER_PIECE',stage,len(bm.verts),len(bm.faces),'nonmanifold',sum(not e.is_manifold for e in bm.edges),'volume',bm.calc_volume(),'zero',sum(f.calc_area()<1e-8 for f in bm.faces),flush=True)
                bm.free()
    if '--regenerate' in sys.argv or '--snapshot' in sys.argv:
        copy=bpy.data.collections.new('Validación de preparación');scene.collection.children.link(copy)
        objects=structural_physics.snapshot(coll,copy,{'binder_excluded':0})
        print('USER_REGENERATED_SNAPSHOT_PASSED',len(objects),flush=True)


if __name__=='__main__':run()
