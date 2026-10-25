"""Prepara el ensayo ya calculado para render, sin repetir física."""
import json
import sys
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import ruinas_panel as addon
from ruinas_panel import runtime
from ruinas_panel.services import lab_cameras


def run():
    'IA: Aplica perfil al laboratorio y replay existentes, comprueba poses y caras, renderiza un fotograma y guarda vídeo Full HD en carpeta común.'
    addon.register();runtime.busy=True
    path=ROOT/'dist/repro_revoco_ciclo.blend'
    bpy.ops.wm.open_mainfile(filepath=str(path))
    replay=bpy.context.scene;assert replay.get('physics_result_scene')
    for scene in bpy.data.scenes:
        if not (scene.get('physics_result_scene') or scene.get('structural_physics')):continue
        bpy.context.window.scene=scene
        scene.frame_set(1)
        before={o.name:(o.data.as_pointer(),len(o.data.polygons),tuple(v for row in o.matrix_world for v in row)) for o in scene.objects if o.type=='MESH'}
        lab_cameras.prepare_render(scene)
        after={o.name:(o.data.as_pointer(),len(o.data.polygons),tuple(v for row in o.matrix_world for v in row)) for o in scene.objects if o.type=='MESH'}
        assert before==after
        scene.render.filepath=str(ROOT/'dist'/'Videos Render'/('repro_revoco_ciclo_'+bpy.path.clean_name(scene.name)+'_'))
    bpy.context.window.scene=replay
    replay.frame_set(241)
    replay.render.image_settings.media_type='IMAGE';replay.render.image_settings.file_format='PNG'
    replay.render.filepath=str(ROOT/'reports/reported_cycle_render_detail.png')
    replay.render.resolution_percentage=40;replay.cycles.samples=16
    bpy.ops.render.render(write_still=True)
    replay.render.image_settings.media_type='VIDEO';replay.render.image_settings.file_format='FFMPEG'
    replay.render.resolution_percentage=100;replay.cycles.samples=128
    replay.render.filepath=str(ROOT/'dist'/'Videos Render'/'repro_revoco_ciclo_')
    replay.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=str(path))
    report={'lights':len([o for o in replay.objects if o.type=='LIGHT']),'cameras':len([o for o in replay.objects if o.type=='CAMERA']),'video':replay.render.filepath,'resolution':[1920,1080],'engine':replay.render.engine,'dof':replay.camera.data.dof.use_dof,'physics_recalculated':False}
    (ROOT/'reports/render_delivery.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print('RENDER_DELIVERY_PASSED',report,flush=True)


if __name__=='__main__':run()
