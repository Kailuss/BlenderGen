"""Puesta en escena dirigida de tres impactos; preserva apoyos fuera de corredores."""
import sys,json,math,time,tempfile,subprocess,faulthandler
from pathlib import Path
import bpy
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import ruinas_panel as addon
from ruinas_panel import runtime
from ruinas_panel.services import impact_physics,lab_chandelier,lab_cameras,physics_jobs
OUT=ROOT/'dist/Ejercicio02_metralla_20261028'
PATHS=[
    dict(name='01 · Cubierta y planta alta',start=(-.08,-.15,.52),end=(.04,.29,.265),frame=40,radius=.022),
    dict(name='02 · Cruce de plantas',start=(.27,-.09,.32),end=(-.18,.22,.13),frame=78,radius=.024),
    dict(name='03 · Planta baja y cimientos',start=(-.18,-.12,.17),end=(.08,.28,.012),frame=116,radius=.021),
]


def contact(ob,path,padding=0):
    'IA: Entrada del segmento en la caja mundial expandida; no usa el centro de una unión como blanco.'
    start=Vector(path['start']);delta=Vector(path['end'])-start
    length=delta.length;direction=delta.normalized();radius=path['radius']+padding
    pts=[ob.matrix_world@Vector(v) for v in ob.bound_box]
    near,far=0.,length
    for axis in range(3):
        lo=min(v[axis] for v in pts)-radius;hi=max(v[axis] for v in pts)+radius
        if abs(direction[axis])<1e-10:
            if not lo<=start[axis]<=hi:return None
        else:
            a,b=sorted(((lo-start[axis])/direction[axis],(hi-start[axis])/direction[axis]))
            near=max(near,a);far=min(far,b)
            if near>far:return None
    return near


def run():
    'IA: Prefractura localizada, tres proyectiles guiados hasta salida, liberaciones al contacto, lámparas y cámaras; cálculo opcional aislado.'
    addon.register();runtime.busy=runtime.preview=True
    faulthandler.enable();faulthandler.dump_traceback_later(120,repeat=True)
    lab=next(s for s in bpy.data.scenes if s.get('ruinas_physics_lab'))
    bpy.context.window.scene=lab;lab.frame_set(1)
    p=lab.ruin_settings;p.physics_frames=241;p.physics_memory_mb=10240;p.physics_timeout_seconds=7200
    lab.render.fps=24;lab.render.fps_base=1;lab.frame_end=241;lab.rigidbody_world.point_cache.frame_end=241
    p.physics_sparse_constraints=False;p.fracture_strength=.15
    p.impact_render_visible=True;p.impact_lifetime=0;p.impact_mode='THROW';p.impact_speed=2000;p.impact_mass=20
    # Acotar por distancia a trayectorias, nunca por una muestra aleatoria de piezas.
    eligible=[o for o in lab.objects if o.rigid_body and not o.get('impactor') and not o.get('collision_floor') and o.get('physical_role')!='ground']
    padding=None
    for candidate in (.016,.014,.012,.010,.008,0.):
        count=sum(any(contact(o,path,candidate) is not None for path in PATHS) for o in eligible)
        print('ZONE_PREFLIGHT',candidate,count,flush=True)
        if count<=2016:padding=candidate;break
    if padding is None:raise ValueError('Las trayectorias directas superan el presupuesto; hay que replantearlas.')
    prefractured=json.loads(lab.get('shrapnel_prefractured','[]'))
    for path in ([] if lab.get('shrapnel_prefractured') else PATHS):
        print('FRACTURE_SELECT',path['name'],flush=True)
        stones=[o for o in lab.objects if o.rigid_body and o.rigid_body.type=='ACTIVE'
                and o.get('physical_role')=='stone' and not o.get('fracture_fragment') and contact(o,path) is not None]
        stones.sort(key=lambda o:(contact(o,path),o.name))
        chosen=stones[::max(1,len(stones)//10)][:10]
        if chosen:
            print('FRACTURE_BEGIN',len(chosen),[o.name for o in chosen],flush=True)
            prefractured.extend(o.name for o in chosen)
            impact_physics.fracture(lab,chosen)
            print('FRACTURE_END',path['name'],flush=True)
    lab['shrapnel_prefractured']=json.dumps(prefractured)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'02b_prefractura.blend'))
    hit={};report_paths=[]
    for path in PATHS:
        print('PROJECTILE_BEGIN',path['name'],flush=True)
        start=Vector(path['start']);delta=Vector(path['end'])-start;direction=delta.normalized()
        p.impact_direction=direction;p.impact_radius=path['radius']*1000
        projectile=impact_physics.launch(lab,[]);projectile.name='Metralla · '+path['name'];projectile.animation_data_clear()
        first=path['frame'];steps=math.ceil(delta.length/(2/24));last=first+steps
        for frame in (1,first-1,*range(first,last+2)):
            projectile.location=start+direction*(max(0,frame-first+1)*2/24)
            projectile.keyframe_insert(data_path='location',frame=frame)
        for frame,value in ((1,True),(last,True),(last+1,False)):
            projectile.rigid_body.kinematic=value;projectile.rigid_body.keyframe_insert(data_path='kinematic',frame=frame)
        for layer in projectile.animation_data.action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for curve in bag.fcurves:
                        for key in curve.keyframe_points:key.interpolation='LINEAR' if curve.data_path=='location' else 'CONSTANT'
        projectile['release_frame']=last+1;projectile['launch_start']=list(start)
        impact_physics.direction_guide(lab,projectile,direction)
        lab.frame_set(1);bpy.context.view_layer.update()
        affected=0
        for ob in lab.objects:
            if not ob.rigid_body or ob.get('impactor') or ob.get('collision_floor') or ob.get('physical_role')=='ground':continue
            distance=contact(ob,path,padding)
            if distance is None:continue
            frame=max(first,first-1+math.floor(distance/(2/24)))
            hit[ob.name]=min(frame,hit.get(ob.name,frame));affected+=1
            ob['shrapnel_zone']=path['name']
            if ob.rigid_body.type=='PASSIVE':ob.rigid_body.type='ACTIVE'
        report_paths.append(dict(path,release_frame=last+1,affected=affected))
    p.physics_brick_limit=2048
    print('ZONE_READY',len(hit),flush=True)
    impact_physics.limit_to_selection(lab,[lab.objects[name] for name in hit])
    released=0;retained=0
    for ob in lab.objects:
        c=ob.rigid_body_constraint
        if not c:continue
        frames=[hit[o.name] for o in (c.object1,c.object2) if o and o.name in hit]
        if not frames:
            c.use_breaking=False;c.enabled=False;c.disable_collisions=False;retained+=1
            continue
        frame=min(frames)
        c.use_breaking=False
        for field in ('enabled','disable_collisions'):
            for f,value in ((1,True),(frame-1,True),(frame,False)):
                setattr(c,field,value);c.keyframe_insert(data_path=field,frame=f)
        ob['shrapnel_release_frame']=frame;released+=1
    lab.frame_set(1);bpy.context.view_layer.update()
    p.chandelier_drop_mm=35;p.chandelier_sway_deg=6
    ceilings=[o for o in lab.objects if o.type=='MESH' and o.rigid_body and 'viga' in o.name.lower() and o.name not in hit]
    lamps=[]
    for z in (.139,.264,.389):
        choices=[o for o in ceilings if abs(o.location.z-z)<.025]
        if choices:
            ceiling=min(choices,key=lambda o:(o.location-Vector((.04,.12,z))).length)
            lamps.append(lab_chandelier.create(lab,ceiling).name)
    if not lamps:raise ValueError('No se ha encontrado apoyo para la lámpara.')
    for kind in ('STATIC','ORBIT','INTERIOR'):lab_cameras.create(lab,kind=kind)
    lab.camera=next(o for o in lab.objects if o.get('lab_camera')=='STATIC')
    lab_cameras.prepare_render(lab)
    report=dict(paths=report_paths,corridor_padding_m=padding,prefractured=prefractured,released_bodies=hit,released_joints=released,
                retained_joints=retained,chandeliers=lamps,
                limits='Puesta en escena dirigida: cuerpos fuera de corredores pasivos, proyectiles guiados hasta salida. No predicción de resistencia real.')
    lab['directed_fracture']=report['limits'];lab.frame_set(1)
    (OUT/'impactos.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'03_laboratorio_impactos.blend'))
    print('IMPACTS_READY',len(hit),released,retained,lamps,flush=True)
    if '--simulate' not in sys.argv:return
    simulate(lab,report)


def simulate(lab,report):
    'IA: Ejecuta el laboratorio preparado en un trabajador aislado con límites, diagnóstico de poses y reproducción separada.'
    folder=Path(tempfile.mkdtemp(prefix='ruinas_shrapnel_'));output=folder/'result.blend';progress=folder/'progress.json'
    source=folder/'input.blend';bpy.data.libraries.write(str(source),{lab},fake_user=True)
    cmd=[bpy.app.binary_path,'--factory-startup','-t','2','-b',str(source),'--python-exit-code','1','--python',str(ROOT/'tools/shrapnel_worker.py'),'--',str(output),str(progress),lab.name]
    with (folder/'worker.log').open('w',encoding='utf8') as log:
        proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    runtime.physics_job=dict(process=proc,folder=folder,output=output,progress=progress,started=time.monotonic(),scene=lab.name,mode='SIMULATE',memory_limit_mb=10240,time_limit_seconds=21600)
    print('SHRAPNEL_JOB',str(folder),flush=True)
    peak=0;last=0
    while True:
        peak=max(peak,physics_jobs.memory_mb(proc.pid));status=physics_jobs.poll()
        if 'finished' in status:result=status['finished'];break
        if time.monotonic()-last>30:print('SIM_PROGRESS',status,peak,flush=True);last=time.monotonic()
        time.sleep(1)
    result.name='04 · Tres impactos calculados';bpy.context.window.scene=result;result.frame_set(1)
    report['simulation']=json.loads(result['simulation_report']);report['peak_mb']=peak
    (OUT/'impactos.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'04_fisicas_calculadas.blend'))


if __name__=='__main__':run()
