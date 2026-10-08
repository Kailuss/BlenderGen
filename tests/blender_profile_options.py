"""Matriz real RNA: perfiles, planos, caché, agrupación y ensayo físico."""
import sys,json,math
from pathlib import Path
import bpy,bmesh
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'tests'))
import ruinas_panel as addon
from ruinas_panel import runtime,meta,config
from ruinas_panel.services import cache,physics
from ruinas_panel.geometry import batching,primitives
from ruinas_panel.structure import walls,layout
from ruinas_panel.ui.panel import enabled
from blender_probe import closure,digest
from blender_v032 import render


def run():
    'IA: Verifica grosor RNA efectivo, interiores en los tres perfiles, controles dependientes y caída de copias sin alterar fuente.'
    bpy.ops.wm.read_factory_settings(use_empty=True);addon.register();runtime.busy=True;runtime.preview=True
    source=bpy.context.scene;p=source.ruin_settings;p.live_preview=False;p.batch_preview=False;p.lock_distribution=False
    p.layout_mode='ROOM';p.length=220;p.building_depth=190;p.height_type='ONE';p.damage_enabled=False;p.interior_layout='THREE'
    p.physics_target='PARTITION';p.windows_enabled=True;p.door_enabled=True;p.door_width=40;p.roof_frame=False
    reports=[]
    for profile,thickness in (('PARTITION',6),('WALL',9),('FORTRESS',15)):
        p.build_type=profile;cache.clear_cache();coll=addon.generate(bpy.context,p,'WORK')
        assert abs(p.thickness-thickness)<1e-6,(profile,p.thickness)
        plan=meta.get(source,'plano_interior',{});assert len(plan.get('rooms',[]))==3,(profile,plan)
        count=len(physics.sections(coll));assert count>0
        closed=closure(coll);assert not closed['open_edges'],closed
        original=digest(coll);coll=addon.generate(bpy.context,p,'WORK');assert digest(coll)==original
        assert meta.get(source,'ventanas_generadas',[])
        print('PROFILE',profile,count,flush=True)
        reports.append({'profile':profile,'thickness':p.thickness,'sections':count,'closed':True,'cached':True})
    render(source,ROOT/'reports/profile_fortress.png',focus=(0,85,28),location=(250,-260,270),scale=320)
    saved_settings={k:getattr(p,k) for k in config.FIELDS}
    direct=physics.sections(coll)
    batching.pack_preview(coll);assert physics.sections(coll)==direct
    grouped=digest(coll);assert bpy.ops.ruin.physics_lab()=={'FINISHED'}
    scene=bpy.context.scene;assert not bpy.ops.ruin.generate.poll();assert digest(coll)==grouped
    assert source.rigidbody_world is None
    bpy.context.window.scene=scene
    initial={o.name:o.location.copy() for o in scene.objects if o.rigid_body.type=='ACTIVE'}
    for frame in range(1,121):scene.frame_set(frame)
    dg=bpy.context.evaluated_depsgraph_get();positions={o.name:o.evaluated_get(dg).matrix_world.translation.copy() for o in scene.objects if o.name in initial}
    assert all(all(math.isfinite(v) for v in co) for co in positions.values())
    assert any((positions[name]-co).length>0.00003 for name,co in initial.items()),'no movement'
    ground=next(o for o in scene.objects if o.name.startswith('Ensayo · suelo'))
    assert min(co.z for co in positions.values())>ground.location.z-.003,'fell through floor'
    scene.frame_set(1)
    render(scene,ROOT/'reports/physics_lab.png',focus=(0,.09,.025),location=(.24,-.22,.2),scale=.30)
    assert bpy.ops.ruin.physics_return()=={'FINISHED'};assert bpy.context.scene==source
    assert digest(coll)==grouped
    p.height_type='RUIN';assert not enabled(p,'interior_layout')
    p.height_type='ONE';p.stair_type='NONE';assert not enabled(p,'stair_side')
    p.ground_floor=False;p.upper_floor=True;assert not enabled(p,'floor_damage')
    p.height_type='TWO';p.damage_enabled=True;assert enabled(p,'floor_damage')
    p.damage_enabled=False;assert not enabled(p,'wood_damage')
    influences={}
    runtime.instance_build=False
    for field in ('stone_variation','randomness'):
        for wall in ('left','right','back'):
            results=[]
            for value in (0,1):
                setattr(p,field,value)
                probe=bpy.data.collections.new('probe');source.collection.children.link(probe)
                edges,_=layout.course_layout(p)
                walls.segment_wall(probe,p,wall,0,130,(0,0),(1,0),p.height,edges)
                results.append(digest(probe))
                assert not closure(probe)['open_edges']
                primitives.remove_objects(probe.objects);bpy.data.collections.remove(probe)
            assert results[0]!=results[1],(field,wall)
            influences[field+':'+wall]=True
    (ROOT/'reports/profile_options.json').write_text(json.dumps({'wall_controls':influences,'profiles':reports,'physics_bodies':len(initial),'source_unchanged':True,'grouping_preserves_sections':True,'simulation_frames':120},indent=2),encoding='utf-8')
    for key,value in saved_settings.items():setattr(p,key,value)
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'dist/ruinas_physics_lab.blend'))
    print('PROFILE_OPTIONS_PASSED',reports,flush=True)


if __name__=='__main__':run()
