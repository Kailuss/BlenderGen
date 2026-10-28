import bpy,json
from pathlib import Path
s=next(x for x in bpy.data.scenes if x.get('physics_result_scene'))
assert s.frame_end==241 and s.render.fps==24
assert not s.rigidbody_world
assert sum(o.type=='CAMERA' for o in s.objects)==3
assert {o.data.type for o in s.objects if o.type=='LIGHT'}=={'SUN','AREA','SPOT'}
assert s.render.image_settings.file_format=='FFMPEG'
assert not any(o.library for o in s.objects)
assert any(t.name.startswith('LEEME') for t in bpy.data.texts)
bpy.context.window.scene=s;s.frame_set(241)
assert json.loads(s['delivery_audit'])['final_over_10mm']>300
print('DELIVERY_REOPEN_PASSED',len(s.objects),bpy.data.filepath,flush=True)
