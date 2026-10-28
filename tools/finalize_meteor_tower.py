"""Entrega revisable de torre: métricas, materiales y cámaras sobre física ya calculada."""
import sys,json
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'tests'))
import ruinas_panel as addon
from ruinas_panel import runtime
from ruinas_panel.services import lab_cameras
from blender_v032 import render
addon.register();runtime.busy=True;runtime.preview=True
s=next(x for x in bpy.data.scenes if x.get('physics_result_scene'));lab=next(x for x in bpy.data.scenes if x.get('ruinas_physics_lab'))
bpy.context.window.scene=s;s.frame_set(1)
objects=[o for o in s.objects if o.type=='MESH' and not o.get('impactor') and o.get('physical_role')!='ground']
initial={o.name:o.matrix_world.copy() for o in objects}
s.frame_set(30);drift=[(o.matrix_world.translation-initial[o.name].translation).length*1000 for o in objects]
s.frame_set(241);moved=[(o.matrix_world.translation-initial[o.name].translation).length*1000 for o in objects]
report={'preimpact_max_mm':max(drift),'preimpact_over_2mm':sum(d>2 for d in drift),'final_over_10mm':sum(d>10 for d in moved),'final_scale_max_delta':max((o.matrix_world.to_scale()-initial[o.name].to_scale()).length for o in objects),'duration_seconds':(s.frame_end-1)/s.render.fps}
assert report['preimpact_over_2mm']==0,report
assert report['final_over_10mm']>300,report
assert report['final_scale_max_delta']<.00001,report
for f in (1,36,60,241):
    s.frame_set(f);s.render.image_settings.media_type='IMAGE';s.render.image_settings.file_format='PNG'
    render(s,ROOT/f'reports/meteor_entrega_{f:03d}.png',focus=(0,.055,.19),location=(.65,.90,.60),scale=.70)
# Las cámaras de control nunca forman parte de la entrega.
for ob in list(s.objects):
    if ob.type=='CAMERA' and not ob.get('lab_camera'):bpy.data.objects.remove(ob,do_unlink=True)
s.frame_set(1);s.camera=next(o for o in s.objects if o.get('lab_camera')=='STATIC')
s.camera.location=(.60,.80,.48);s.camera.data.lens=48
lab_cameras.prepare_render(s)
s.render.resolution_x=1280;s.render.resolution_y=1080;s.render.resolution_percentage=100;s.cycles.samples=64
s.render.filepath=str(ROOT/'dist/Videos Render/Torre_meteorito_20261028_')
# Acabado visual de roca, sin cambiar el colisionador esférico ni la masa.
mat=bpy.data.materials.new('Meteorito · roca oscura');mat.diffuse_color=(.12,.075,.045,1);mat.use_nodes=True
nodes=mat.node_tree.nodes;links=mat.node_tree.links;shader=nodes.get('Principled BSDF');shader.inputs['Base Color'].default_value=(.12,.075,.045,1);shader.inputs['Roughness'].default_value=.83
noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=8;noise.inputs['Detail'].default_value=3
coord=nodes.new('ShaderNodeTexCoord');links.new(coord.outputs['Generated'],noise.inputs['Vector'])
bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.45;bump.inputs['Distance'].default_value=.001;links.new(noise.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs['Normal'],shader.inputs['Normal'])
for sc in (s,lab):
    for ob in sc.objects:
        if ob.get('impactor'):ob.data.materials.clear();ob.data.materials.append(mat)
text=bpy.data.texts.new('LEEME · Torre y meteorito')
text.write('TORRE Y METEORITO — entrega 28-10-2026\n\nEscena 03: reproducción calculada, 241 fotogramas a 24 fps (10 segundos entre extremos). Espacio para reproducir. No necesita recalcular Bullet.\nEscena 02: laboratorio editable. Flecha = dirección inicial; la flecha no reprograma la trayectoria al rotarla.\nEscena 01: torre fuente editable, tres niveles, 12 ventanas y tres tramos de escalera hasta la terraza. Muros: 377 mm.\n\nImpacto dirigido: inicio f32; proyectil guiado hasta f35 para atravesar terraza y pared posterior; libre bajo gravedad desde f36. Se liberan 2061 uniones de 565 piezas en el corredor de impacto y la zona superior posterior. El resto conserva sus uniones. Es una puesta en escena física dirigida, no una predicción de resistencia real.\n\nCámaras: estática posterior, órbita e interior. Sol, área y spot. F12 para imagen (cambiar salida a imagen si Blender lo requiere), Ctrl+F12 para vídeo H264.\n\nFuente y laboratorio conservados. Los materiales visuales no cambian las masas ni la geometría de colisión.\n')
s['delivery_audit']=json.dumps(report);s['delivery_revision']='20261028-r2';s['directed_fracture']=lab['directed_fracture']
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.clip_start=.0001;area.spaces.active.clip_end=100
            area.spaces.active.region_3d.view_distance=.75;area.spaces.active.region_3d.view_location=(0,.055,.19)
s.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'dist/Torre_meteorito_entrega_20261028.blend'))
(ROOT/'reports/meteor_entrega_audit.json').write_text(json.dumps(report,indent=2),encoding='utf8')
# Imagen con materiales e iluminación, sin alterar la configuración de vídeo guardada.
s.frame_set(36);s.render.image_settings.media_type='IMAGE';s.render.image_settings.file_format='PNG';s.render.resolution_percentage=60;s.cycles.samples=24;s.render.filepath=str(ROOT/'reports/meteor_entrega_render.png')
bpy.ops.render.render(write_still=True)
print('DELIVERY_AUDIT',json.dumps(report),flush=True)
