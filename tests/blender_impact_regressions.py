"""Regresiones del laboratorio: fuente real, vista, impactos múltiples y prefractura."""
import sys,json
from pathlib import Path
import bpy,bmesh
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'tests'))
import ruinas_panel as addon
from ruinas_panel import config,runtime
from ruinas_panel.services import structural_physics as structural,impact_physics as impact
from ruinas_panel.geometry import primitives
from ruinas_panel.ui.operators import frame_view
from blender_probe import digest

def volume(mesh):
    'IA: Mide cierre, normales y volumen positivo de una malla física en metros.'
    bm=bmesh.new();bm.from_mesh(mesh);assert all(e.is_manifold for e in bm.edges);v=bm.calc_volume();bm.free();assert v>0;return v

def run():
    'IA: Conserva la fuente, divide piedra en sólidos unidos, lanza dos impactos y comprueba transferencia de movimiento y vista en ambas escalas.'
    bpy.ops.wm.read_factory_settings(use_empty=True);addon.register();runtime.busy=True;runtime.instance_build=True
    source=bpy.context.scene;source.name='CASA ORIGINAL';p=source.ruin_settings;p.live_preview=False;p.physics_strength=.1
    assert p.physics_target=='BUILDING'
    coll=bpy.data.collections.new(config.COLLECTION);source.collection.children.link(coll)
    mat=primitives.material('Piedra',(.5,.4,.3))
    for i in range(4):primitives.block('Ladrillo real '+str(i),i*12,i*12+11.96,-3,3,0,6,coll,mat)
    original=digest(coll);lab=structural.prepare(source);bpy.context.window.scene=lab
    assert digest(coll)==original and all(any(o.get('source_piece')==s.name for o in lab.objects) for s in coll.objects)
    assert any(o.get('collision_floor') for o in lab.objects)
    stones=[o for o in lab.objects if o.get('physical_role')=='stone'];before=sum(volume(o.data) for o in stones)
    lab.ruin_settings.fracture_strength=.001
    fragments=impact.fracture(lab,stones);assert len(fragments)==8
    assert abs(sum(volume(o.data) for o in fragments)-before)<before*.00001
    pair=fragments[2:4];start_distance=(pair[0].location-pair[1].location).length
    for frame in range(1,31):lab.frame_set(frame)
    deps=bpy.context.evaluated_depsgraph_get()
    stable_distance=(pair[0].evaluated_get(deps).matrix_world.translation-pair[1].evaluated_get(deps).matrix_world.translation).length
    assert abs(stable_distance-start_distance)<.0001
    lab.frame_set(1);p=lab.ruin_settings;p.impact_direction=(0,1,0);p.impact_speed=500;p.impact_radius=8;p.fracture_strength=.001
    impact.limit_to_selection(lab,fragments)
    assert all(o.rigid_body.type=='ACTIVE' for o in fragments)
    first=impact.launch(lab,fragments);second=impact.launch(lab,fragments)
    assert (Vector(first['launch_start'])-Vector(second['launch_start'])).length>.016
    assert first!=second and sum(bool(o.get('impactor')) for o in lab.objects)==2
    # Second stone offset avoids coincident projectile collision.
    for layer in second.animation_data.action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for curve in bag.fcurves:
                    if curve.data_path=='location' and curve.array_index==0:
                        for key in curve.keyframe_points:key.co.y+=.08
    initial=first.location.copy();positions=[]
    for frame in range(1,121):
        lab.frame_set(frame);deps=bpy.context.evaluated_depsgraph_get();positions.append(first.evaluated_get(deps).matrix_world.translation.copy())
    assert positions[first['release_frame']+2].y>positions[first['release_frame']].y,'No directed launch velocity'
    final_distance=(pair[0].evaluated_get(deps).matrix_world.translation-pair[1].evaluated_get(deps).matrix_world.translation).length
    print('FRAGMENT_SEPARATION',start_distance,final_distance,flush=True)
    assert final_distance>start_distance+.001,'Fragments did not break apart'
    assert digest(coll)==original
    for scene in (lab,source):
        bpy.context.window.scene=scene;frame_view(bpy.context)
        for area in bpy.context.screen.areas:
            if area.type=='VIEW_3D':
                sp=area.spaces.active;assert sp.clip_start>0 and sp.clip_end>sp.region_3d.view_distance
    from ruinas_panel.services import masonry_physics
    bpy.context.window.scene=source;source.ruin_settings.physics_brick_limit=16
    small=masonry_physics.prepare(source);bpy.context.window.scene=small
    bricks=[o for o in small.objects if o.get('masonry_brick')];initial={o:o.location.copy() for o in bricks}
    for frame in range(1,61):small.frame_set(frame)
    deps=bpy.context.evaluated_depsgraph_get()
    drift=max((o.evaluated_get(deps).matrix_world.translation-initial[o]).length for o in bricks)
    assert drift<.001,drift
    small.ruin_settings.impact_mode='PRESS';small.ruin_settings.impact_radius=8;small.ruin_settings.impact_speed=500
    press=impact.launch(small,bricks)
    for frame in range(1,121):small.frame_set(frame)
    assert press.rigid_body.kinematic
    print('IMPACT_REGRESSIONS_PASSED',{'intact_drift_mm':drift*1000,'split_distance_mm':final_distance*1000},flush=True)

if __name__=='__main__':run()
