"""Mide la prefractura sobre el laboratorio grande sin cambiar el archivo de entrada."""
import sys,time,json
from pathlib import Path
import bpy,bmesh
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from stage_shrapnel_house import addon,runtime,PATHS,contact,impact_physics


def run():
    'IA: Prefractura las diez piezas del primer corredor, comprueba masa, cierre y registro de cuerpos, y mide el tiempo sin guardar el laboratorio.'
    addon.register();runtime.busy=runtime.preview=True
    lab=next(s for s in bpy.data.scenes if s.get('ruinas_physics_lab'));bpy.context.window.scene=lab;lab.frame_set(1)
    path=PATHS[0]
    stones=[o for o in lab.objects if o.rigid_body and o.rigid_body.type=='ACTIVE' and o.get('physical_role')=='stone' and not o.get('fracture_fragment') and contact(o,path) is not None]
    stones.sort(key=lambda o:(contact(o,path),o.name));chosen=stones[::max(1,len(stones)//10)][:10]
    names=[o.name for o in chosen];mass=sum(o.rigid_body.mass for o in chosen)
    started=time.perf_counter();parts=impact_physics.fracture(lab,chosen);elapsed=time.perf_counter()-started
    assert len(parts)==20
    assert abs(sum(o.rigid_body.mass for o in parts)-mass)<mass*1e-5
    assert len({o.rigid_body.as_pointer() for o in parts})==20
    for ob in parts:
        assert ob.name in lab.rigidbody_world.collection.objects
        bm=bmesh.new();bm.from_mesh(ob.data);assert all(e.is_manifold for e in bm.edges);assert bm.calc_volume()>0;bm.free()
    report=dict(seconds=elapsed,pieces=names,fragments=len(parts),mass=mass)
    (ROOT/'reports/large_prefracture.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print('LARGE_PREFRACTURE_PASSED',report,flush=True)


if __name__=='__main__':run()
