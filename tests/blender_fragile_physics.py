"""Revoco y conducto hueco: conservación, reposo y separación física de fragmentos."""
import sys,json,time
from pathlib import Path
import bpy,bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'tests'))
import ruinas_panel as addon
from ruinas_panel import config,runtime
from ruinas_panel.geometry import primitives
from ruinas_panel.structure import roof_accessories
from ruinas_panel.services import structural_physics,physics_jobs,impact_physics
from blender_probe import digest
from blender_v032 import render
from ruinas_panel.ui.operators import frame_view


def run():
    'IA: Exige prefractura cerrada, luz del conducto libre, identidad reproducible y fuente intacta; calcula reposo e impacto sobre fragmentos.'
    bpy.ops.wm.read_factory_settings(use_empty=True);addon.register();runtime.instance_build=True
    source=bpy.context.scene;source.name='01 FUENTE FRAGIL';source.ruin_settings.live_preview=False
    coll=bpy.data.collections.new(config.COLLECTION);source.collection.children.link(coll)
    mat=primitives.material('Revoco · cal',(.6,.56,.5));stone=primitives.material('Piedra',(.5,.5,.5))
    primitives.block('Piedra · base',-55,55,-6,6,0,3,coll,stone)
    primitives.block('Revoco · prueba',-50,50,-1.6,1.6,3,63,coll,mat)
    primitives.block('Piedra · base conducto',124,156,-12,12,0,3,coll,stone)
    roof_accessories.ring(coll,stone,{'x':140,'y':0,'normal':(0,1)},'Hogar · conducto interior',(14,10),(14,10),3,83,2.5)
    expected={}
    for ob in coll.objects:
        bm=bmesh.new();bm.from_mesh(ob.data);expected[ob.name]=abs(bm.calc_volume());bm.free()
    before=digest(coll);lab=structural_physics.prepare(source);lab.name='02 LABORATORIO FRAGIL';assert digest(coll)==before
    fragments=[o for o in lab.objects if o.get('fracture_parent')]
    assert 20<len(fragments)<=config.PHYSICS_FRAGILE_LIMIT
    ids=[o['physical_piece_id'] for o in fragments];assert len(set(ids))==len(ids)
    volumes={}
    for ob in fragments:
        bm=bmesh.new();bm.from_mesh(ob.data);assert all(e.is_manifold for e in bm.edges),ob.name
        volumes[ob['fracture_parent']]=volumes.get(ob['fracture_parent'],0)+bm.calc_volume()*1e9;bm.free()
        if 'conducto' in ob['fracture_parent']:
            tree=BVHTree.FromPolygons([ob.matrix_world@v.co for v in ob.data.vertices],[list(p.vertices) for p in ob.data.polygons])
            assert tree.ray_cast(Vector((.14,0,.1)),Vector((0,0,-1)),.11)[0] is None,'El conducto se ha tapado'
    for name,volume in volumes.items():assert abs(volume-expected[name])<max(.01,expected[name]*.0001),(name,volume,expected[name])
    bpy.context.window.scene=lab;lab.frame_end=72;lab.rigidbody_world.point_cache.frame_end=72
    physics_jobs.start(lab)
    while True:
        status=physics_jobs.poll()
        if 'finished' in status:break
        time.sleep(.5)
    resting=status['finished'];bpy.context.window.scene=resting;resting.frame_set(1)
    start={o:o.matrix_world.translation.copy() for o in resting.objects if o.get('fracture_parent')}
    resting.frame_set(72)
    rest_without_impact=max((o.matrix_world.translation-pos).length*1000 for o,pos in start.items())
    assert rest_without_impact<1,('Reposo inestable',rest_without_impact)
    resting.name='03 REPOSO SIN IMPACTO';resting.frame_set(1)
    bpy.context.window.scene=lab;lab.frame_end=72;lab.rigidbody_world.point_cache.frame_end=72
    lab.ruin_settings.impact_mode='PRESS';lab.ruin_settings.impact_speed=500;lab.ruin_settings.impact_radius=12;lab.ruin_settings.impact_mass=3;lab.ruin_settings.impact_direction=(0,1,0)
    targets=[o for o in fragments if o.get('fragile_material')=='plaster']
    impact_physics.launch(lab,targets)
    physics_jobs.start(lab)
    while True:
        status=physics_jobs.poll()
        if 'finished' in status:break
        time.sleep(.5)
    replay=status['finished'];bpy.context.window.scene=replay
    source_fragments=[o for o in replay.objects if o.get('fracture_parent')]
    replay.frame_set(1);initial={o:o.matrix_world.translation.copy() for o in source_fragments}
    replay.frame_set(2);rest=max((o.matrix_world.translation-pos).length*1000 for o,pos in initial.items())
    replay.frame_set(72);motions=[(o.matrix_world.translation-pos).length*1000 for o,pos in initial.items()]
    assert rest<1,('Impulso inicial artificial',rest)
    assert sum(m>2 for m in motions)>3,('No se desprenden fragmentos',motions)
    report={'fragments':len(fragments),'volumes_mm3':volumes,'initial_max_motion_mm':rest,'moved_over_2mm':sum(m>2 for m in motions),'max_motion_mm':max(motions),'source_unchanged':digest(coll)==before,'flue_open':True,'rest_without_impact_mm':rest_without_impact}
    replay.frame_set(72)
    render(replay,ROOT/'reports/fragile_after.png',focus=(.045,0,.04),location=(.25,-.3,.21),scale=.25)
    replay.frame_set(1);replay.name='00 REPRODUCCION FRAGIL'
    render(replay,ROOT/'reports/fragile_before.png',focus=(.045,0,.04),location=(.25,-.3,.21),scale=.25)
    frame_view(bpy.context)
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'dist/ruinas_v0329_fragmentos.blend'))
    (ROOT/'reports/fragile_physics.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print('FRAGILE_PHYSICS_PASSED',report,flush=True)


if __name__=='__main__':run()
