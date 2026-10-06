"""Selección de las tres estancias y encuentros de colisionadores."""
import sys
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import ruinas_panel as addon
from ruinas_panel import runtime,config,meta
from ruinas_panel.structure import interiors,floor_plan,layout
from ruinas_panel.services import physics


def run():
    'IA: Las tres zonas conservan cajas positivas sin solapes; daño apagado no libera secciones y el origen queda intacto.'
    bpy.ops.wm.read_factory_settings(use_empty=True);addon.register();runtime.busy=True;runtime.preview=True
    source=bpy.context.scene;p=source.ruin_settings;p.live_preview=False;p.length=220;p.building_depth=190;p.layout_mode='ROOM';p.interior_layout='THREE';p.height_type='ONE';p.collapse=.4;p.wood_damage=.5
    layout.apply_profiles(p);plan=floor_plan.plan(p,(-100,100,4,180));meta.put(source,'plano_interior',plan)
    coll=bpy.data.collections.new(config.COLLECTION);source.collection.children.link(coll);interiors.build(coll,p,source)
    for target in ('ROOM1','ROOM2','ROOM3'):
        p.physics_target=target;lab=physics.prepare(source)
        bodies=[o for o in lab.objects if 'source_section' in o]
        assert bodies
        bounds=[]
        for ob in bodies:
            co=[ob.matrix_world@v.co for v in ob.data.vertices]
            lo=[min(v[i] for v in co) for i in range(3)];hi=[max(v[i] for v in co) for i in range(3)]
            assert min(b-a for a,b in zip(lo,hi))>0
            for l,h in bounds:assert not all(min(h[i],hi[i])-max(l[i],lo[i])>1e-8 for i in range(3)),(target,ob.name)
            bounds.append((lo,hi))
        print('ROOM_ZONE',target,len(bodies),flush=True)
    p.damage_enabled=False;lab=physics.prepare(source)
    assert all(o.rigid_body.type=='PASSIVE' for o in lab.objects)
    assert not source.rigidbody_world
    bpy.context.window.scene=lab
    try:physics.accept(lab);raise AssertionError('accepted without simulation')
    except ValueError as exc:assert 'Simular' in str(exc)
    physics.simulate(lab);assert physics.accept(lab)==source
    runtime.physics_simulations.clear()
    try:physics.accept(lab);raise AssertionError('accepted stale cache')
    except ValueError as exc:assert 'Simular' in str(exc)
    print('ROOM_ZONES_PASSED',flush=True)


if __name__=='__main__':run()
