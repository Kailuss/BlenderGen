"""Duración real, órbita y luces sin duplicados a distintas tasas de fotogramas."""
import sys
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import ruinas_panel as addon
from ruinas_panel import runtime
from ruinas_panel.services import masonry_physics,lab_cameras


def run():
    'IA: Comprueba diez segundos con FPS enteros/fraccionales, caché, órbita cerrada, luces idempotentes y preservación al copiar a reproducción.'
    addon.register();runtime.busy=True
    source=bpy.context.scene;source.ruin_settings.physics_brick_limit=16
    lab=masonry_physics.prepare(source);bpy.context.window.scene=lab
    lab_cameras.setup(lab)
    for kind in ('STATIC','ORBIT','INTERIOR'):lab_cameras.create(lab,kind=kind)
    orbit=next(o for o in lab.objects if o.get('lab_camera')=='ORBIT')
    lights={o.name:o.data.energy for o in lab.objects if o.type=='LIGHT'}
    for fps,base in ((24,1),(30,1),(30,1.001),(60,1)):
        lab.render.fps=fps;lab.render.fps_base=base
        lab_cameras.ten_seconds(lab)
        assert abs((lab.frame_end-1)*base/fps-10)<=base/fps/2
        assert lab.rigidbody_world.time_scale==1 and lab.rigidbody_world.point_cache.frame_end==lab.frame_end
        curves=[c for layer in orbit.animation_data.action.layers for strip in layer.strips for bag in strip.channelbags for c in bag.fcurves if c.data_path=='location']
        assert len(curves)==3
        assert all(abs(c.keyframe_points[-1].co.x-lab.frame_end)<1e-4 for c in curves)
        assert all(abs(c.evaluate(1)-c.evaluate(lab.frame_end))<1e-6 for c in curves)
        assert sum(abs(c.evaluate(1)-c.evaluate((lab.frame_end+1)/2)) for c in curves)>.05
        assert {o.name:o.data.energy for o in lab.objects if o.type=='LIGHT'}==lights
    replay=bpy.data.scenes.new('Reproducción de prueba');lab_cameras.copy_to_replay(lab,replay)
    assert len([o for o in replay.objects if o.type=='LIGHT'])==3
    assert len([o for o in replay.objects if o.type=='CAMERA'])==3
    assert all(c.target in list(replay.objects) for o in replay.objects for c in o.constraints if hasattr(c,'target'))
    print('TEN_SECONDS_PASSED',flush=True)


if __name__=='__main__':run()
