"""Duración de proyectiles: colisión, reproducción y vuelta al inicio."""
import sys,time,json
from pathlib import Path
import bpy
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import ruinas_panel as addon
from ruinas_panel.services import masonry_physics,impact_physics,physics_jobs,physics_worker


def run():
    'IA: Exige vencimiento reversible, colisiones desactivadas y visibilidad persistente en reproducción reabierta.'
    with patch.object(Path,'replace',side_effect=[PermissionError('lector'),PermissionError('lector'),None]) as replace:
        physics_worker.progress(ROOT/'dist/progress_retry.json',stage='Prueba')
        assert replace.call_count==3
    bpy.ops.wm.read_factory_settings(use_empty=True);addon.register()
    source=bpy.context.scene;source.ruin_settings.live_preview=False;source.ruin_settings.physics_brick_limit=16;source.ruin_settings.physics_frames=24
    lab=masonry_physics.prepare(source);bpy.context.window.scene=lab;p=lab.ruin_settings
    p.impact_lifetime=3;p.impact_mode='PRESS';p.impact_speed=250
    ob=impact_physics.launch(lab,[]);assert ob['impact_expire_frame']==4
    lab.frame_set(1);assert not ob.hide_viewport and any(ob.rigid_body.collision_collections)
    lab.frame_set(4);assert ob.hide_viewport and ob.hide_render and not any(ob.rigid_body.collision_collections)
    lab.frame_set(1);assert not ob.hide_viewport and any(ob.rigid_body.collision_collections)
    physics_jobs.start(lab)
    while True:
        status=physics_jobs.poll()
        if 'finished' in status:break
        time.sleep(.2)
    replay=status['finished'];bpy.context.window.scene=replay;projectile=next(o for o in replay.objects if o.get('impactor'))
    replay.frame_set(1);assert not projectile.hide_viewport and not projectile.hide_render
    replay.frame_set(4);assert projectile.hide_viewport and projectile.hide_render
    replay.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'dist/ruinas_v03210_lifetime.blend'))
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'dist/ruinas_v03210_lifetime.blend'))
    replay=bpy.context.scene;replay.frame_set(4);projectile=next(o for o in replay.objects if o.get('impactor'));assert projectile.hide_viewport and projectile.hide_render
    (ROOT/'reports/impact_lifetime.json').write_text(json.dumps({'expires_at':4,'collision_disabled':True,'replay_reopened':True,'reset_restores':True}),encoding='utf8')
    print('IMPACT_LIFETIME_PASSED',flush=True)


if __name__=='__main__':run()
