"""Casa real y zona prefracturada, conservando laboratorio y reproducción."""
import sys,json,time
from pathlib import Path
import bpy,bmesh
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'tests'))
import ruinas_panel as addon
from ruinas_panel import runtime,config
from ruinas_panel.services import structural_physics as structural,impact_physics as impact
from ruinas_panel.ui.operators import frame_view
from blender_probe import digest,closure
from blender_v032 import render

def run():
    'IA: Traslada una casa generada, prepara 16 ladrillos para romper, conserva resto como soporte y hornea el impacto sin alterar la fuente.'
    bpy.ops.wm.read_factory_settings(use_empty=True);addon.register();runtime.busy=True;runtime.preview=True
    source=bpy.context.scene;source.name='01 CASA DISEÑADA';p=source.ruin_settings;p.live_preview=False
    p.layout_mode='ROOM';p.length=100;p.building_depth=90;p.height_type='ONE';p.seed=17;p.lock_distribution=False
    p.damage_enabled=False;p.roof_frame=True;p.roof_tiles=True;p.roof_gables=True
    p.ground_floor=True;p.ground_roughness=0;p.rubble_amount=0;p.windows_enabled=True;p.door_enabled=True;p.door_leaf=False
    p.use_instances=True;p.batch_preview=True;p.physics_strength=.2;p.physics_frames=120
    coll=addon.generate(bpy.context,p,'WORK');before=digest(coll);assert not closure(coll)['open_edges']
    lab=structural.prepare(source);lab.name='02 CASA · EDITAR IMPACTO';bpy.context.window.scene=lab
    assert digest(coll)==before
    stones=[o for o in lab.objects if o.get('physical_role')=='stone' and o.rigid_body.type=='ACTIVE']
    # Fachada posterior: mantiene intactos vanos y cubierta, limita el coste dinámico.
    target=Vector((.05,.09,.03));selected=sorted(stones,key=lambda o:(o.location-target).length)[:16]
    active=set(sorted(stones,key=lambda o:(o.location-target).length)[:64])
    for ob in lab.objects:
        if ob.rigid_body and ob not in active:ob.rigid_body.type='PASSIVE'
    lab.ruin_settings.fracture_strength=.01
    fragments=impact.fracture(lab,selected)
    lab.ruin_settings.impact_direction=(0,-1,0);lab.ruin_settings.impact_speed=600;lab.ruin_settings.impact_radius=12
    projectile=impact.launch(lab,fragments);objects=[o for o in lab.objects if o.type=='MESH']
    initial={o.name:o.matrix_world.copy() for o in objects};poses=[];started=time.perf_counter()
    print('HOUSE_SIM_START',len(objects),len(active),flush=True)
    for frame in range(1,121):
        lab.frame_set(frame);deps=bpy.context.evaluated_depsgraph_get()
        poses.append({o.name:o.evaluated_get(deps).matrix_world.copy() for o in objects})
        if frame%30==0:print('HOUSE_FRAME',frame,round(time.perf_counter()-started,1),flush=True)
    moved=sum((poses[-1][o.name].translation-initial[o.name].translation).length>.002 for o in fragments)
    print('HOUSE_FRAGMENT_MOVED',moved,flush=True);assert moved>0
    replay=bpy.data.scenes.new('00 CASA · REPRODUCIR');replay['ruinas_replay']=True;replay['source_scene']=source.name;replay['lab_scene']=lab.name
    replay['playback_instructions']='Impacto dirigido en la casa · Espacio';replay.frame_end=120
    for original in objects:
        ob=bpy.data.objects.new(original.name+' · reproducción',original.data);replay.collection.objects.link(ob)
        ob.matrix_world=initial[original.name]
        if original.get('collision_floor'):ob['collision_floor']=True
        if any((pose[original.name].translation-initial[original.name].translation).length>1e-6 for pose in poses):
            for frame,pose in enumerate(poses,1):
                ob.matrix_world=pose[original.name];ob.keyframe_insert(data_path='location',frame=frame);ob.keyframe_insert(data_path='rotation_euler',frame=frame)
    bpy.context.window.scene=replay;replay.frame_set(1)
    render(replay,ROOT/'reports/impact_house_before.png',focus=(.05,.045,.035),location=(.2,.25,.18),scale=.2)
    replay.frame_set(120)
    render(replay,ROOT/'reports/impact_house_after.png',focus=(.05,.045,.035),location=(.2,.25,.18),scale=.2)
    replay.frame_set(1);lab.frame_set(1);frame_view(bpy.context)
    bpy.data.texts.new('LEEME').write('Casa original en 01. Laboratorio en 02: zona de 64 ladrillos móviles, 16 prefracturados en 32 mitades. Resto pasivo para acotar coste. Impacto dirigido sin trayectoria impuesta después del lanzamiento. La reproducción 00 abre sin complemento. Para editar instala v0327. No se ha exportado mortero ni sólido de impresión.')
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'dist/ruinas_v0327_casa_impacto.blend'))
    report={'bodies':len(objects),'fractured_bricks':16,'moving_fragments':moved,'seconds':time.perf_counter()-started,'source_unchanged':digest(coll)==before}
    (ROOT/'reports/impact_house.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print('HOUSE_IMPACT_PASSED',report,flush=True)

if __name__=='__main__':run()
