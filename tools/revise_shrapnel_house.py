"""Revisa el ensayo guardado sin repetir generación, contactos ni prefractura."""
import sys,json,math
from pathlib import Path
import bpy
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from stage_shrapnel_house import addon,runtime,OUT,PATHS,contact,simulate


def run():
    'IA: Reduce velocidad a 0,8 m/s, retiene cuerpos hasta el paso del impacto y programa conjuntamente colisiones y uniones; conserva geometría y límites.'
    addon.register();runtime.busy=runtime.preview=True
    lab=next(s for s in bpy.data.scenes if s.get('ruinas_physics_lab'));bpy.context.window.scene=lab;lab.frame_set(1)
    report=json.loads((OUT/'impactos.json').read_text(encoding='utf8'));hit={}
    step=.8/24;padding=report['corridor_padding_m']
    for path in PATHS:
        projectile=next(o for o in lab.objects if o.get('impactor') and o.name=='Metralla · '+path['name'])
        projectile.animation_data_clear();start=Vector(path['start']);delta=Vector(path['end'])-start
        direction=delta.normalized();first=path['frame'];last=first+math.ceil(delta.length/step)
        for frame in (1,first-1,first,last,last+1):
            projectile.location=start+direction*max(0,frame-first+1)*step
            projectile.keyframe_insert(data_path='location',frame=frame)
        for frame,value in ((1,True),(last,True),(last+1,False)):
            projectile.rigid_body.kinematic=value;projectile.rigid_body.keyframe_insert(data_path='kinematic',frame=frame)
        for layer in projectile.animation_data.action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for curve in bag.fcurves:
                        for key in curve.keyframe_points:key.interpolation='LINEAR' if curve.data_path=='location' else 'CONSTANT'
        projectile['release_frame']=last+1
        for name in report['released_bodies']:
            ob=lab.objects[name];distance=contact(ob,path,padding)
            if distance is not None:
                frame=max(first,first-1+math.floor(distance/step));hit[name]=min(frame,hit.get(name,frame))
    assert set(hit)==set(report['released_bodies'])
    for name,frame in hit.items():
        ob=lab.objects[name];ob.animation_data_clear()
        for f,value in ((1,True),(frame-1,True),(frame,False)):
            ob.rigid_body.kinematic=value;ob.rigid_body.keyframe_insert(data_path='kinematic',frame=f)
    for ob in lab.objects:
        c=ob.rigid_body_constraint
        if not c:continue
        frames=[hit[o.name] for o in (c.object1,c.object2) if o and o.name in hit]
        if not frames:continue
        frame=min(frames);ob.animation_data_clear();c.use_breaking=False
        for field in ('enabled','disable_collisions'):
            for f,value in ((1,True),(frame-1,True),(frame,False)):
                setattr(c,field,value);c.keyframe_insert(data_path=field,frame=f)
        ob['shrapnel_release_frame']=frame
    lab.frame_set(1)
    report.update(speed_m_s=.8,released_bodies=hit,hold_until_impact=True)
    report['limits']+=' Cuerpos afectados retenidos cinemáticamente hasta su impacto; reposo anterior impuesto, no ensayo de estabilidad libre.'
    lab['directed_fracture']=report['limits']
    (OUT/'impactos.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'03b_impactos_retenidos.blend'))
    print('REVISED_READY',len(hit),flush=True)
    simulate(lab,report)


if __name__=='__main__':run()
