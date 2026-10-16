"""Diagnóstico reproducible de dos mallas de un encaje fallido."""
import sys,json
from pathlib import Path
import bpy,bmesh
from mathutils import Matrix,Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from ruinas_panel.geometry import primitives
from ruinas_panel.services import structural_physics as sp


def run():
    'IA: Compara diferencia original y recentrada sin modificar el edificio aportado; registra cierre y volumen.'
    fixture=Path(sys.argv[sys.argv.index('--')+1]) if '--' in sys.argv else ROOT/'tests/fixtures/joint_precision.json'
    data=json.loads(fixture.read_text(encoding='utf8'))
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for centered in (False,True):
        for solver in ('MANIFOLD','EXACT'):
            objects=[]
            center=sum((Vector(v) for v in data['target']['vertices']),Vector())/len(data['target']['vertices']) if centered else Vector()
            for key in ('target','cutter'):
                record=data[key];mesh=bpy.data.meshes.new(key)
                mesh.from_pydata([Vector(v)-center for v in record['vertices']],[],record['faces']);mesh.update()
                ob=bpy.data.objects.new(key,mesh);bpy.context.scene.collection.objects.link(ob);objects.append(ob)
            target,cutter=objects
            print('INPUT',centered,solver,sp.valid(target.data),sp.valid(cutter.data),flush=True)
            mod=target.modifiers.new('probe','BOOLEAN');mod.operation='DIFFERENCE';mod.solver=solver;mod.object=cutter
            primitives.apply_modifier(target,mod,cutter)
            for repair in (False,True):
                if repair:primitives.repair_precision(target)
                bm=bmesh.new();bm.from_mesh(target.data)
                print('OUTPUT',centered,solver,repair,'faces',len(bm.faces),'open',sum(not e.is_manifold for e in bm.edges),'volume',bm.calc_volume(),'valid',sp.valid(target.data),flush=True)
                if centered and solver=='MANIFOLD':
                    assert all(e.is_manifold for e in bm.edges) and 19.66<bm.calc_volume()<19.68
                bm.free()
            primitives.remove_objects(objects)


if __name__=='__main__':run()
