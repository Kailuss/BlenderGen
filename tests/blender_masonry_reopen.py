import sys
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'tests'))
import ruinas_panel as addon
from ruinas_panel.services import masonry_physics as masonry
from blender_v032 import render
addon.register()
source=bpy.data.scenes['00 AJUSTES'];lab=masonry.prepare(source);bpy.context.window.scene=lab
bricks=[o for o in lab.objects if o.get('masonry_brick')];initial={o:o.location.copy() for o in bricks}
for frame in range(1,121):lab.frame_set(frame)
deps=bpy.context.evaluated_depsgraph_get();maximum=max((o.evaluated_get(deps).matrix_world.translation-initial[o]).length for o in bricks)
print('INTACT_MAX_MM',maximum*1000,flush=True);assert maximum<.001
for name in ('IMPACTO','HUECO'):
    scene=bpy.data.scenes[name+' · REPRODUCIR'];bpy.context.window.scene=scene
    for frame in (1,120):
        scene.frame_set(frame)
        render(scene,ROOT/('reports/masonry_'+name.lower()+'_'+str(frame)+'.png'),focus=(0,0,.035),location=(.14,-.23,.16),scale=.32)
print('MASONRY_REOPEN_PASSED',flush=True)
