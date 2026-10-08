"""Ensayo de edificio completo: fuente intacta, sólidos recortados y uniones."""
import sys,json,time
from pathlib import Path
import bpy
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'tests'))
import ruinas_panel as addon
from ruinas_panel import runtime,config
from ruinas_panel.services import physics,structural_physics as structural
from blender_probe import digest,closure
from blender_v032 import render


def run():
    'IA: Casa con cubierta completa; valida preparación sin mortero, no mutación de fuente y estabilidad inicial antes de soltar uniones.'
    bpy.ops.wm.read_factory_settings(use_empty=True);addon.register();runtime.busy=True;runtime.preview=True
    source=bpy.context.scene;source.name='01 CASA EDITABLE';p=source.ruin_settings;p.live_preview=False
    p.layout_mode='ROOM';p.interior_layout='TWO';p.length=170;p.building_depth=155;p.height_type='ONE';p.seed=17;p.lock_distribution=False
    p.batch_preview=False;p.use_instances=False;p.door_enabled=True;p.door_width=40;p.door_leaf=False
    p.windows_enabled=True;p.ground_floor=True;p.roof_frame=True;p.roof_tiles=True;p.roof_gables=True
    p.wood_grain=1;p.damage_enabled=False;p.wear_level='CUSTOM';p.wear=.1;p.cracks=0;p.rubble_amount=0;p.ground_roughness=0
    p.collapse=0;p.wood_damage=0;p.floor_damage=0;p.roof_damage=0;p.hole_count=0;p.preview_quality='WORK';p.physics_target='BUILDING'
    coll=addon.generate(bpy.context,p,'WORK');before=digest(coll);assert not closure(coll)['open_edges']
    lab=physics.prepare(source);lab.name='02 LABORATORIO ESTRUCTURAL';bpy.context.window.scene=lab
    assert digest(coll)==before;report=json.loads(lab['preparation_report'])
    assert report['binder_excluded'] and report['roles']['tile'] and report['roles']['wood'] and report['roles']['stone']
    bodies=[o for o in lab.objects if o.rigid_body and not o.get('collision_floor')];assert all(o.rigid_body.collision_shape=='MESH' for o in bodies)
    assert all(o.rigid_body_constraint.type=='FIXED' for o in lab.objects if o.rigid_body_constraint)
    report['source_unchanged']=True
    (ROOT/'reports/structural_physics.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf8')
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'dist/ruinas_estructura_preparada.blend'))
    for frame in range(1,25):lab.frame_set(frame)
    dg=bpy.context.evaluated_depsgraph_get()
    from mathutils import Matrix
    motions=[(o.evaluated_get(dg).matrix_world.translation-Matrix(json.loads(o['initial_matrix'])).translation).length*1000 for o in bodies]
    report['intact_motion_24_frames_mm']={'max':max(motions),'mean':sum(motions)/len(motions)}
    report['largest_initial_movements']=[{'piece':o['source_piece'],'motion_mm':m,'volume_mm3':o['physical_volume_mm3']} for o,m in sorted(zip(bodies,motions),key=lambda pair:pair[1],reverse=True)[:10]]
    assert max(motions)<3 and sum(motions)/len(motions)<.05,'El edificio intacto se mueve demasiado antes del ensayo'
    (ROOT/'reports/structural_physics.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf8')
    print('STRUCTURAL_PHYSICS_PASSED',report,flush=True)


if __name__=='__main__':run()
