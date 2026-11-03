"""Integración del proyectil E-1 con el lanzador real."""
import json
import sys
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import ruinas_panel as addon
from ruinas_panel import runtime
from ruinas_panel.services import impact_physics, impact_spec


def run():
    """IA: La especificación gobierna masa/radio y rechaza PRESS sin mutación; mantiene la cesión dinámica anterior al blanco."""
    addon.register();runtime.busy=True
    scene=bpy.context.scene
    scene['structural_physics']=True
    scene.frame_end=241
    bpy.ops.mesh.primitive_cube_add(size=.02)
    target=bpy.context.object
    bpy.ops.rigidbody.object_add()
    p=scene.ruin_settings
    p.impact_direction=(1,0,0)
    p.impact_mode='THROW'
    spec=dict(radius_model_m=.01,density_kg_m3=2200,speed_model_m_s=.8,
              scale=60,mass_scale=10000,max_speed_model_m_s=1,event_energy_j=100000)
    expected=impact_spec.projectile(**spec)
    ob=impact_physics.launch(scene,[target],specification=spec)
    assert abs(ob.rigid_body.mass-expected['mass_solver'])<1e-4
    assert json.loads(ob['impact_specification'])==expected
    scene.frame_set(ob['release_frame'])
    assert not ob.rigid_body.kinematic
    scene.frame_set(1)
    count=len(scene.objects)
    p.impact_mode='PRESS'
    try:
        impact_physics.launch(scene,[target],specification=spec)
    except ValueError:
        pass
    else:
        raise AssertionError('Se aceptó empuje de energía ilimitada')
    assert len(scene.objects)==count
    print('IMPACT_SPEC_PASSED',flush=True)


if __name__=='__main__':
    run()
