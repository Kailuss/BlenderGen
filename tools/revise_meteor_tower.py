"""Revisión dirigida: atravesar la terraza y liberar los cuerpos alcanzados."""
import sys,time,json,math,tempfile,subprocess
from pathlib import Path
import bpy
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import ruinas_panel as addon
from ruinas_panel import runtime
from ruinas_panel.services import physics_jobs,impact_physics
addon.register();runtime.busy=True;runtime.preview=True
lab=next(s for s in bpy.data.scenes if s.get('ruinas_physics_lab'));bpy.context.window.scene=lab
lab.frame_set(1);lab.ruin_settings.physics_timeout_seconds=7200
lab.frame_end=241;lab.ruin_settings.physics_frames=241;lab.render.fps=24;lab.render.fps_base=1
lab.rigidbody_world.point_cache.frame_end=241
meteor=next(o for o in lab.objects if o.get('impactor'))
entry=Vector(lab['meteor_entry_m']);direction=Vector(lab['meteor_direction']);start=entry-direction*.12
meteor.animation_data_clear()
for f in (1,31,32,33,34,35,36):
    meteor.location=start+direction*(max(0,f-31)*2/24)
    meteor.keyframe_insert(data_path='location',frame=f)
meteor.rigid_body.kinematic=True
meteor.rigid_body.keyframe_insert(data_path='kinematic',frame=1);meteor.rigid_body.keyframe_insert(data_path='kinematic',frame=35)
meteor.rigid_body.kinematic=False;meteor.rigid_body.keyframe_insert(data_path='kinematic',frame=36)
for layer in meteor.animation_data.action.layers:
    for strip in layer.strips:
        for bag in strip.channelbags:
            for curve in bag.fcurves:
                for k in curve.keyframe_points:k.interpolation='LINEAR' if curve.data_path=='location' else 'CONSTANT'
meteor['release_frame']=36

def entry_distance(ob,radius=.018):
    'IA: Interseca la trayectoria con AABB expandida por radio; devuelve distancia de contacto y no decide por el centro de la unión.'
    points=[ob.matrix_world@Vector(v) for v in ob.bound_box]
    lo=[min(v[k] for v in points)-radius for k in range(3)];hi=[max(v[k] for v in points)+radius for k in range(3)]
    near,far=0.,.36
    for k in range(3):
        if abs(direction[k])<1e-9:
            if not lo[k]<=start[k]<=hi[k]:return None
        else:
            a,b=sorted(((lo[k]-start[k])/direction[k],(hi[k]-start[k])/direction[k]))
            near=max(near,a);far=min(far,b)
            if near>far:return None
    return near
lab.frame_set(1);bpy.context.view_layer.update()
hit={}
for ob in lab.objects:
    if not ob.rigid_body or ob==meteor or ob.rigid_body.type!='ACTIVE':continue
    d=entry_distance(ob)
    if d is not None:hit[ob.name]=max(32,math.floor(31+d/(2/24)))
    x,y,z=ob.location
    if ob.name not in hit and -.09<x<.10 and ((z>.375 and y>.018) or (z>.26 and y>.055)):
        hit[ob.name]=36 if z>.375 else 38+int(max(0,.375-z)*30)
        ob['meteor_damage_zone']='COLLAPSE'
    elif ob.name in hit:ob['meteor_damage_zone']='DIRECT'
impact_physics.direction_guide(lab,meteor,direction)
released=0
for ob in lab.objects:
    c=ob.rigid_body_constraint
    if not c:continue
    if ob.get('meteor_release_frame'):
        ob.animation_data_clear();c.enabled=True;c.disable_collisions=True;del ob['meteor_release_frame']
    frames=[hit[o.name] for o in (c.object1,c.object2) if o and o.name in hit]
    if not frames:continue
    f=min(frames)
    for field in ('enabled','disable_collisions'):
        setattr(c,field,True);c.keyframe_insert(data_path=field,frame=1);c.keyframe_insert(data_path=field,frame=f-1)
        setattr(c,field,False);c.keyframe_insert(data_path=field,frame=f)
    ob['meteor_release_frame']=f;released+=1
lab['directed_fracture']='Meteorito cinemático hasta salir del muro; libera todas las uniones de cuerpos intersectados por su volumen. Libre bajo gravedad desde f36.'
lab.frame_set(1)
report={'revision':2,'contacted_bodies':hit,'released_joints':released,'kinematic_until':35,'reason':'Revision 1 rebounded on roof; no penetration.'}
(ROOT/'reports/meteor_v2_setup.json').write_text(json.dumps(report,indent=2),encoding='utf8')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'dist/torre_meteorito_laboratorio_v2.blend'))
folder=Path(tempfile.mkdtemp(prefix='ruinas_meteor_v2_'));output=folder/'result.blend';progress=folder/'progress.json'
source_file=folder/'input.blend'
bpy.data.libraries.write(str(source_file),{lab},fake_user=True)
command=[bpy.app.binary_path,'--factory-startup','-t','2','-b',str(source_file),'--python-exit-code','1','--python',str(ROOT/'tools/meteor_worker.py'),'--',str(output),str(progress),lab.name]
with (folder/'worker.log').open('w',encoding='utf8') as log:
    process=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
runtime.physics_job={'process':process,'folder':folder,'output':output,'progress':progress,'started':time.monotonic(),'scene':lab.name,'mode':'SIMULATE','memory_limit_mb':8192,'time_limit_seconds':7200}
print('REVISION2_JOB',str(folder),len(hit),released,flush=True)
peak=0;last=0
while True:
    peak=max(peak,physics_jobs.memory_mb(process.pid));status=physics_jobs.poll()
    if 'finished' in status:result=status['finished'];break
    if time.monotonic()-last>30:print('V2_PROGRESS',status,peak,flush=True);last=time.monotonic()
    time.sleep(1)
result.name='03 · Meteorito calculado';bpy.context.window.scene=result;result.frame_set(1)
report.update(simulation=json.loads(result['simulation_report']),peak_mb=peak)
(ROOT/'reports/meteor_v2_result.json').write_text(json.dumps(report,indent=2),encoding='utf8')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'dist/Torre_meteorito_v03221_revision2.blend'))
print('REVISION2_SAVED',flush=True)


