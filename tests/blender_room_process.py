"""Reproducción completa: daño, física por estancia, aceptación y STL."""
import sys,json,time
from pathlib import Path
import bpy,bmesh
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'tests'))
import ruinas_panel as addon
from ruinas_panel import runtime,meta,config
from ruinas_panel.services import physics,export
from blender_probe import closure,digest
from blender_v032 import render


def snapshot(source,coll,name):
    'IA: Conserva una etapa visible con mallas propias, sin compartir modificaciones posteriores.'
    dg=bpy.context.evaluated_depsgraph_get()
    matrices={ob.name:ob.evaluated_get(dg).matrix_world.copy() for ob in coll.objects}
    scene=bpy.data.scenes.new(name);scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=source.unit_settings.scale_length
    for ob in coll.objects:
        copy=bpy.data.objects.new(ob.name,ob.data.copy());scene.collection.objects.link(copy)
        copy.matrix_world=matrices[ob.name]
        for key in ob.keys():copy[key]=ob[key]
    return scene


def run():
    'IA: Genera daño real, simula una estancia, acepta poses, comprueba caché/exportación y guarda escenas y STL verificables.'
    bpy.ops.wm.read_factory_settings(use_empty=True);addon.register();runtime.busy=True;runtime.preview=True
    source=bpy.context.scene;source.name='04 · Casa con física aceptada';p=source.ruin_settings;p.live_preview=False
    p.layout_mode='ROOM';p.interior_layout='TWO';p.length=170;p.building_depth=155;p.height_type='ONE';p.seed=17;p.lock_distribution=False
    p.batch_preview=False;p.use_instances=False;p.door_enabled=True;p.door_width=40;p.door_leaf=False
    p.windows_enabled=True;p.ground_floor=True;p.roof_frame=True;p.roof_tiles=False;p.roof_gables=True
    p.wood_grain=1;p.damage_enabled=False;p.wear_level='CUSTOM';p.wear=.1;p.cracks=0;p.rubble_amount=0;p.ground_roughness=0
    p.collapse=.32;p.wood_damage=.5;p.floor_damage=0;p.roof_damage=0;p.hole_count=0;p.preview_quality='WORK';p.export_quality='WORK';p.export_density=1
    coll=addon.generate(bpy.context,p,'WORK');assert not closure(coll)['open_edges']
    intact=snapshot(source,coll,'01 · Detalle madera y cal')
    gables=[o for o in coll.objects if o.get('roof_gable')];assert gables
    for ob in gables:
        bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.triangulate(bm,faces=list(bm.faces))
        assert all(e.is_manifold for e in bm.edges);assert min(f.calc_area() for f in bm.faces)>1e-8;assert bm.calc_volume()>0;bm.free()
    # Vista de detalle interior: ocultación solo para la imagen, sin quitar piezas.
    for ob in coll.objects:ob.hide_render=not (ob.get('interior_partition') or ob.get('roof_gable') or ob.get('roof_gable_frame'))
    render(source,ROOT/'reports/material_relief.png',focus=(0,65,55),location=(170,-180,160),scale=245)
    for ob in coll.objects:ob.hide_render=False
    p.damage_enabled=True;p.roof_frame=False
    coll=addon.generate(bpy.context,p,'WORK');assert not closure(coll)['open_edges']
    before=digest(coll);snapshot(source,coll,'02 · Daño antes de física')
    p.physics_target='ROOM1';p.physics_frames=120
    assert bpy.ops.ruin.physics_lab()=={'FINISHED'};lab=bpy.context.scene;lab.name='03 · Física estancia 1'
    assert lab['physics_room']=='front'
    active=[o for o in lab.objects if o.rigid_body.type=='ACTIVE'];assert active
    assert bpy.ops.ruin.physics_simulate()=={'FINISHED'}
    assert digest(coll)==before
    snapshot(lab,lab.collection,'03b · Resultado físico fijado')
    assert bpy.ops.ruin.physics_accept()=={'FINISHED'};assert bpy.context.scene==source
    coll=bpy.data.collections[config.COLLECTION];accepted=digest(coll);assert accepted!=before
    poses=meta.get(source,'physics_result');assert poses['poses']
    runtime.preview=True
    coll=addon.generate(bpy.context,p,'WORK');assert digest(coll)==accepted
    p.seed+=1
    try:addon.generate(bpy.context,p,'WORK');raise AssertionError('stale physics accepted')
    except ValueError as exc:assert 'obsoleto' in str(exc)
    p.seed-=1
    assert digest(coll)==accepted
    render(source,ROOT/'reports/room_physics_result.png',focus=(0,65,20),location=(190,-220,260),scale=260)
    runtime.preview=False
    coll=addon.generate(bpy.context,p,'WORK');assert meta.get(source,'physics_result')==poses
    print('PROCESS_EXPORT_START',flush=True);start=time.perf_counter()
    solid=export.make_solid(bpy.context,method='MANIFOLD')
    bm=bmesh.new();bm.from_mesh(solid.data);assert all(e.is_manifold for e in bm.edges);assert bm.calc_volume()>0;bm.free()
    out=ROOT/'dist/ruinas_v0324_proceso_completo.stl'
    bpy.ops.object.select_all(action='DESELECT');solid.select_set(True);bpy.context.view_layer.objects.active=solid
    bpy.ops.wm.stl_export(filepath=str(out),export_selected_objects=True,apply_modifiers=True)
    assert out.stat().st_size>84
    report={'rooms':meta.get(source,'plano_interior')['rooms'],'active_bodies':len(active),'poses':len(poses['poses']),'frames':120,'source_unchanged_until_accept':True,'cache_preserves_poses':True,'stale_settings_rejected':True,'solid_faces':len(solid.data.polygons),'export_seconds':time.perf_counter()-start,'solid_closed':True,'stl_bytes':out.stat().st_size}
    (ROOT/'reports/room_process.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    notes=bpy.data.texts.new('LEEME · proceso reproducido')
    notes.write('Ruinas 0.32.4. Escenas: 01 detalle intacto; 02 daño previo; 03 ensayo de estancia; 04 casa con poses aceptadas y sólido exportado. Física solo de tabiques, con suelo plano y dinteles fijos. Fuente oculta por exportación, conservada. STL en mm, sin aplicar Scene Unit. Ver docs/V0324.md.\n'+json.dumps(report,indent=2))
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'dist/ruinas_v0324_proceso_completo.blend'))
    print('ROOM_PROCESS_PASSED',report,flush=True)


if __name__=='__main__':run()
