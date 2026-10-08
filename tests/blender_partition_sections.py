"""Secciones de tabiques: apoyos locales, pasos y daño sin booleanos."""
import sys,json
from pathlib import Path
from types import SimpleNamespace
import bpy,bmesh
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from ruinas_panel import meta,runtime
from ruinas_panel.structure import interiors,floor_plan


def run():
    'IA: Comprueba 35 mm de paso, IDs únicos y apoyo inferior de cada sección; el derrumbe reduce la geometría sin abrir mallas.'
    runtime.preview=True;runtime.quality='WORK'
    p=SimpleNamespace(interior_layout='THREE',layout_mode='ROOM',height=112,ground_floor=True,wood_grain=.8,wood_damage=0,seed=47,collapse=0,lock_distribution=False,building_depth=190,thickness=9,length=220,projection=2,break_position=.5)
    plan=floor_plan.plan(p,(-100,100,5,185),{'left':-20,'right':20},{'y0':155})
    assert 'error' not in plan,plan
    meta.put(bpy.context.scene,'plano_interior',plan)
    counts=[];volumes=[]
    for damage in (0,.8):
        p.collapse=damage;p.wood_damage=damage
        coll=bpy.data.collections.new('sections');bpy.context.scene.collection.children.link(coll)
        interiors.build(coll,p,bpy.context.scene)
        ids={ob['partition_section'] for ob in coll.objects};assert len(ids)==len(coll.objects)
        volume=0
        for ob in coll.objects:
            assert ob['rests_on'] in ids|{'ground','jambs'},ob.name
            bm=bmesh.new();bm.from_mesh(ob.data)
            assert all(e.is_manifold for e in bm.edges)
            assert all(f.calc_area()>1e-8 for f in bm.faces)
            volume+=bm.calc_volume();bm.free()
            co=[v.co for v in ob.data.vertices]
            for part in plan['partitions']:
                for door in part['doors']:
                    for offset in (-17.49,0,17.49):
                        point=(door+offset,part['fixed'],20)
                        assert not all(min(v[i] for v in co)<point[i]<max(v[i] for v in co) for i in range(3)),ob.name
        counts.append(len(coll.objects));volumes.append(volume)
    assert volumes[1]<volumes[0] and counts[1]<=counts[0],(counts,volumes)
    report={'sections':counts,'volume_mm3':volumes,'passage_mm':35,'closed':True,'support_ids_resolve':True}
    (ROOT/'reports/partition_sections.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('PARTITION_SECTIONS_PASSED',report,flush=True)


if __name__=='__main__':run()
