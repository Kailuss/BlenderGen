"""Ensayo aislado del botón de zarandeo sobre selección explícita."""
import sys,json,time
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import ruinas_panel as addon
from ruinas_panel.services import physics,physics_jobs,structural_physics


def run():
    'IA: Calcula diez fotogramas en otro Blender, exige expiración de cuatro impactos y demuestra que cuerpos, selección y fotogramas originales no cambian.'
    bpy.ops.wm.read_factory_settings(use_empty=True);addon.register();scene=bpy.context.scene
    scene['structural_physics']=True;scene['ruinas_physics_lab']=True;scene.frame_end=72
    floor=physics.body(scene,'Suelo',(-60,-60,-5),(60,60,0),False);floor['physical_role']='ground';floor['collision_floor']=True
    bodies=[]
    for x,y in ((-15,-15),(15,-15),(15,15),(-15,15)):
        ob=physics.body(scene,'Bloque',(x-4,y-4,2),(x+4,y+4,10),True);ob['physical_role']='stone';bodies.append(ob)
        structural_physics.joint(scene,ob,floor,ob.location*1000,20)
    original=[(o.name,tuple(o.location),o.rigid_body.type) for o in bodies]
    from ruinas_panel.services import material_strength
    joints=[o for o in scene.objects if o.rigid_body_constraint]
    thresholds=[o.rigid_body_constraint.breaking_threshold for o in joints]
    scene.ruin_settings.physics_stone_strength=.25
    material_strength.apply(scene);material_strength.apply(scene)
    assert all(abs(o.rigid_body_constraint.breaking_threshold-v*.25)<1e-6 for o,v in zip(joints,thresholds))
    scene.ruin_settings.physics_stone_strength=1;material_strength.apply(scene)
    from ruinas_panel.services import lab_cameras
    lab_cameras.create(scene);assert len([o for o in scene.objects if o.type=='CAMERA'])==3
    orbit=next(o for o in scene.objects if o.get('lab_camera')=='ORBIT')
    scene.frame_set(1);start=orbit.location.copy();scene.frame_set(60);assert (orbit.location-start).length>.1
    scene.frame_set(120);assert (orbit.location-start).length<1e-6;scene.frame_set(1)
    try:physics_jobs.start(scene,'SHAKE',selection=[])
    except ValueError:pass
    else:raise AssertionError('Se aceptó selección vacía')
    job=physics_jobs.start(scene,'SHAKE',selection=[o.name for o in bodies[:2]]);peak=0
    while True:
        peak=max(peak,physics_jobs.memory_mb(job['process'].pid));state=physics_jobs.poll()
        if 'finished' in state:break
        time.sleep(.25)
    result=state['finished'];bpy.context.window.scene=result
    assert result.frame_end==10 and scene.frame_end==72
    assert [(o.name,tuple(o.location),o.rigid_body.type) for o in bodies]==original
    assert not any(o.get('impactor') for o in scene.objects)
    projectiles=[o for o in result.objects if o.get('shake_impactor')];assert len(projectiles)==4
    result.frame_set(1);assert all(o.hide_render and not o.hide_viewport for o in projectiles)
    assert len([o for o in result.objects if o.type=='CAMERA'])==3 and result.camera
    result.frame_set(5);assert all(o.hide_render for o in projectiles)
    report=json.loads(result['shake_report']);report['peak_mb']=peak;report['simulation']=json.loads(result['simulation_report'])
    assert report['selected']==2 and report['simulation']['moving']>=4
    (ROOT/'reports/shake_v03212.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'dist/ruinas_v03212_zarandeo_prueba.blend'))
    print('SHAKE_PASSED',report,flush=True)


if __name__=='__main__':run()
