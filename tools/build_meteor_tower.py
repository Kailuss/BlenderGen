"""Entrega dirigida: torre máxima con trayectoria de meteorito y rotura localizada."""
import sys,time,json
from pathlib import Path
import bpy
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import ruinas_panel as addon
from ruinas_panel import runtime,meta
from ruinas_panel.services import physics_jobs,impact_physics,lab_cameras


def wait_job(scene,mode):
    'IA: Ejecuta trabajador aislado y vigila recursos, conserva diagnóstico y registra pico sin simular en la fuente.'
    job=physics_jobs.start(scene,mode);peak=0;last=0
    print('JOB_FOLDER',mode,str(job['folder']),flush=True)
    while True:
        peak=max(peak,physics_jobs.memory_mb(job['process'].pid));status=physics_jobs.poll()
        if 'finished' in status:return status['finished'],peak
        if time.monotonic()-last>15:
            print('JOB_PROGRESS',mode,status,round(peak),flush=True);last=time.monotonic()
        time.sleep(1)


def run():
    'IA: Genera tres niveles máximos y escalera, prepara el laboratorio revisable; la revisión dirigida y su cálculo se ejecutan por separado.'
    addon.register();runtime.busy=True;runtime.preview=True
    scene=bpy.context.scene;scene.name='01 · Torre editable';p=scene.ruin_settings;p.live_preview=False
    values=dict(length=220,building_depth=110,height_type='THREE',ground_storey_height=125,upper_storey_height=125,layout_mode='ROOM',thickness=10,stone_size=10,pillar_count=0,door_enabled=True,door_width=28,door_height=48,windows_enabled=True,windows_per_wall=3,window_width=18,window_height=32,window_projection=0,window_canopies=False,window_leaves=True,window_open_angle=20,balconies=False,roof_frame=True,roof_type='TOWER',roof_tiles=False,roof_gables=False,chimneys=False,ground_floor=True,upper_floor=True,floor_beams=True,stair_type='WOOD',stair_tread=7,stair_riser=8,collapse=0,roof_damage=0,hole_count=0,cracks=0,rubble_amount=0,ground_roughness=0,damage_enabled=False,batch_preview=False,seed=73,physics_strength=150,physics_fragile_size=25,physics_frames=241,physics_memory_mb=8192,physics_timeout_seconds=7200,physics_precision='HIGH',physics_sparse_constraints=False)
    for key,value in values.items():setattr(p,key,value)
    coll=addon.generate(bpy.context,p,'WORK')
    steps=meta.get(scene,'escaleras_generadas',[]);windows=meta.get(scene,'ventanas_generadas',[])
    if len(steps)!=3 or any('error' in s for s in steps):raise ValueError('No hay tres tramos transitables: '+str(steps))
    print('GENERATED',len(coll.objects),'stairs',len(steps),'windows',len(windows),'height',p.height,flush=True)
    scene.render.fps=24
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'dist/torre_meteorito_fuente.blend'))
    lab,prepare_peak=wait_job(scene,'PREPARE');lab.name='02 · Laboratorio meteorito';bpy.context.window.scene=lab
    lp=lab.ruin_settings;lp.physics_memory_mb=8192;lp.physics_timeout_seconds=7200;lp.physics_precision='HIGH';lp.physics_sparse_constraints=False
    for key in ('physics_stone_strength','physics_wood_strength','physics_floor_strength'):setattr(lp,key,1)
    lp.impact_mode='THROW';lp.impact_radius=14;lp.impact_mass=30;lp.impact_speed=2000;lp.impact_direction=(.55,.7,-.45);lp.impact_lifetime=0;lp.impact_render_visible=True
    entry=Vector((-.025,.025,.389));direction=Vector(lp.impact_direction).normalized()
    targets=sorted([o for o in lab.objects if o.rigid_body and o.rigid_body.type=='ACTIVE'],key=lambda o:(o.location-entry).length)[:3]
    meteor=impact_physics.launch(lab,targets);meteor.name='Meteorito · entrada azotea y salida trasera'
    meteor.animation_data_clear();meteor.location=entry-direction*.12
    for frame,position in ((1,entry-direction*.12),(31,entry-direction*.12),(32,entry-direction*(.12-2/24)),(33,entry-direction*(.12-4/24))):
        meteor.location=position;meteor.keyframe_insert(data_path='location',frame=frame)
    meteor.rigid_body.kinematic=True;meteor.rigid_body.keyframe_insert(data_path='kinematic',frame=1);meteor.rigid_body.keyframe_insert(data_path='kinematic',frame=32)
    meteor.rigid_body.kinematic=False;meteor.rigid_body.keyframe_insert(data_path='kinematic',frame=33)
    for layer in meteor.animation_data.action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for curve in bag.fcurves:
                    for key in curve.keyframe_points:key.interpolation='LINEAR' if curve.data_path=='location' else 'CONSTANT'
    meteor['release_frame']=33;meteor['launch_start']=list(entry-direction*.12)
    release_count=0
    for ob in lab.objects:
        c=ob.rigid_body_constraint
        if not c or not c.object1 or not c.object2:continue
        offset=ob.location-entry;t=offset.dot(direction);distance=(offset-direction*t).length
        if -.025<t<.22 and distance<.025 and ob.location.z>.27:
            frame=33+max(0,round(t/(2/24)))
            for field,before,after in (('enabled',True,False),('disable_collisions',True,False)):
                setattr(c,field,before);c.keyframe_insert(data_path=field,frame=1);c.keyframe_insert(data_path=field,frame=frame-1)
                setattr(c,field,after);c.keyframe_insert(data_path=field,frame=frame)
            ob['meteor_release_frame']=frame;release_count+=1
    lab['meteor_direction']=list(direction);lab['meteor_entry_m']=list(entry);lab['directed_fracture']='Joints along 25 mm corridor release on contact frames; remaining structure uses rigid breakable constraints'
    lab.frame_set(1);lab_cameras.create(lab,kind='STATIC');lab_cameras.create(lab,kind='ORBIT');lab_cameras.create(lab,kind='INTERIOR')
    lab.camera=next(o for o in lab.objects if o.get('lab_camera')=='STATIC');lab_cameras.prepare_render(lab)
    report={'parameters':values,'effective_profile':{k:getattr(p,k) for k in ('build_type','stone_size','thickness','height','length','building_depth')},'stairs':steps,'windows':windows,'preparation':json.loads(lab['preparation_report']),'prepare_peak_mb':prepare_peak,'directed_release_joints':release_count}
    (ROOT/'reports/torre_meteorito_preparation.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'dist/torre_meteorito_laboratorio.blend'))
    print('LAB_READY',report['preparation']['bodies'],release_count,flush=True)


if __name__=='__main__':run()

