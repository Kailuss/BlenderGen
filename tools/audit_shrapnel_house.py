"""Aceptación visual y métrica del segundo ejercicio, sin recalcular Bullet."""
import sys,json,math
from pathlib import Path
import bpy
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]
import ruinas_panel as addon
from ruinas_panel import runtime
from blender_v032 import render
addon.register();runtime.busy=runtime.preview=True
s=next(s for s in bpy.data.scenes if s.get('physics_result_scene'));bpy.context.window.scene=s;s.frame_set(1)
objects=[o for o in s.objects if o.type=='MESH' and not o.get('lab_decor') and not o.get('impactor') and not o.get('lab_collision_proxy') and o.get('physical_role')!='ground']
initial={o.name:o.matrix_world.copy() for o in objects}
s.frame_set(30)
drift=max((o.matrix_world.translation-initial[o.name].translation).length*1000 for o in objects)
s.frame_set(241)
regions={key:dict(total=0,moved_over_5mm=0) for key in ('foundation','ground','middle','upper','roof')}
roof_total=roof_retained=0
foundation_blocks_moved=0
for ob in objects:
    origin=initial[ob.name].translation;z=origin.z
    zone='foundation' if z<.018 else 'ground' if z<.143 else 'middle' if z<.268 else 'upper' if z<.393 else 'roof'
    moved=(ob.matrix_world.translation-origin).length*1000
    regions[zone]['total']+=1;regions[zone]['moved_over_5mm']+=moved>5
    if 'cimiento' in ob.name.lower() and moved>5:foundation_blocks_moved+=1
    if z>.393 and ob.get('physical_role')=='tile':
        angle=initial[ob.name].to_quaternion().rotation_difference(ob.matrix_world.to_quaternion()).angle
        roof_total+=1;roof_retained+=moved<5 and angle<math.radians(15)
scale_error=max((o.matrix_world.to_scale()-initial[o.name].to_scale()).length for o in objects)
report=dict(preimpact_max_mm=drift,regions=regions,foundation_blocks_moved=foundation_blocks_moved,roof_retained=roof_retained,roof_total=roof_total,scale_error=scale_error)
(ROOT/'reports/ejercicio02_physics_audit.json').write_text(json.dumps(report,indent=2),encoding='utf8')
for frame in (1,50,90,135,241):
    s.frame_set(frame);s.render.image_settings.media_type='IMAGE';s.render.image_settings.file_format='PNG'
    render(s,ROOT/f'reports/ejercicio02_physics_{frame:03d}.png',focus=(0,.12,.23),location=(.60,-.70,.60),scale=.72)
assert drift<2,report
assert scale_error<1e-5,report
assert all(regions[key]['moved_over_5mm']>=5 for key in regions),report
assert foundation_blocks_moved>0,report
assert roof_total and roof_retained/roof_total>.5,report
print('EXERCISE02_ACCEPTED',report,flush=True)
