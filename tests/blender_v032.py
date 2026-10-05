"""Validación integrada de cubierta, accesorios y planos de la v0.32."""
import json,sys
from pathlib import Path
import bpy,bmesh
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'tests'))
import ruinas_panel as addon
from ruinas_panel import runtime,meta
from ruinas_panel.services import cache
from blender_probe import closure,digest


def render(scene,path,focus=(0,55,60),location=(230,-260,250),scale=270):
    'IA: Vista de inspección reproducible, independiente de la comprobación de mallas.'
    bpy.ops.object.camera_add(location=location);cam=bpy.context.object
    cam.rotation_euler=(Vector(focus)-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.type='ORTHO';cam.data.ortho_scale=scale;scene.camera=cam
    scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL';scene.display.shading.show_cavity=True
    scene.render.resolution_x=1200;scene.render.resolution_y=1000;scene.render.resolution_percentage=100;scene.render.filepath=str(path)
    bpy.ops.render.render(write_still=True)


def run():
    'IA: Prueba tres planos, pasos libres, cache, tubos huecos cerrados y chimenea integrada; guarda caso editable y dos vistas.'
    bpy.ops.wm.read_factory_settings(use_empty=True)
    addon.register();runtime.busy=True;runtime.preview=True
    p=bpy.context.scene.ruin_settings;p.live_preview=False;p.batch_preview=False;p.lock_distribution=False
    p.layout_mode='ROOM';p.length=220;p.building_depth=190;p.height_type='TWO';p.seed=47
    p.damage_enabled=False;p.roof_frame=True;p.roof_tiles=True;p.chimneys=True;p.brass_pipes=True
    p.ground_floor=True;p.upper_floor=True;p.floor_beams=True;p.stair_type='STONE';p.windows_enabled=True;p.door_enabled=True;p.door_width=40
    reports=[]
    for mode in ('OPEN','TWO','THREE'):
        p.interior_layout=mode;cache.clear_cache();coll=addon.generate(bpy.context,p,'WORK')
        plan=meta.get(bpy.context.scene,'plano_interior',{})
        assert 'error' not in plan,plan
        sealed=closure(coll);assert not sealed['open_edges'],sealed
        for ob in coll.objects:
            if ob.get('interior_partition') or ob.get('pipe_section') or ob.get('chimney') or ob.get('roof_tiles'):
                bm=bmesh.new();bm.from_mesh(ob.data)
                assert all(f.calc_area()>1e-8 for f in bm.faces),ob.name
                assert bm.calc_volume()>0,ob.name
                bm.free()
        assert meta.get(bpy.context.scene,'bajantes_generadas',[])
        assert meta.get(bpy.context.scene,'chimeneas_generadas',[]),'chimenea sin sitio'
        if mode!='OPEN':
            assert len(plan['rooms'])==(2 if mode=='TWO' else 3)
            entry=meta.get(bpy.context.scene,'puerta_generada',{})
            assert entry['clear_right']-entry['clear_left']>=34.999,entry
            for room in plan['rooms']:
                x0,x1,y0,y1=room['bounds'];minimum=60 if room['kind']=='room' else 35
                assert min(x1-x0,y1-y0)>=minimum,room
            for part in plan['partitions']:
                for door in part['doors']:
                    point=Vector((door,part['fixed'],20))
                    for ob in coll.objects:
                        if not ob.get('interior_partition'):continue
                        coords=[v.co for v in ob.data.vertices]
                        assert not all(min(v[i] for v in coords)<point[i]<max(v[i] for v in coords) for i in range(3)),ob.name
        first=digest(coll);metrics=meta.get(bpy.context.scene,'ruinas_metricas')
        coll=addon.generate(bpy.context,p,'WORK');assert digest(coll)==first
        assert meta.get(bpy.context.scene,'ruinas_metricas')['cached']
        reports.append({'mode':mode,'plan':plan,'metrics':metrics,'closure':sealed})
        print('V032_CASE',mode,flush=True)
    scene=bpy.context.scene
    from ruinas_panel.services import geometry_audit
    audit=geometry_audit.inspect(coll)
    assert not audit['open_edges'] and not audit['degenerate_faces'] and not audit['nonpositive_volume'],audit
    (ROOT/'reports/physics_readiness.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
    render(scene,ROOT/'reports/v032_exterior.png',focus=(0,90,60),location=(300,-320,300),scale=340)
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'dist/ruina_v032.blend'))
    p.use_instances=False
    coll=addon.generate(bpy.context,p,'WORK')
    for ob in coll.objects:
        top=max((v.co.z for v in ob.data.vertices),default=0)
        ob.hide_render=not (ob.get('interior_partition') or ob.get('stair') or (ob.get('wood_floor') and top<10) or (ob.get('chimney') and top<55))
    render(scene,ROOT/'reports/v032_interior.png',focus=(0,90,15),location=(130,-130,350),scale=310)
    p.use_instances=True;p.damage_enabled=True;p.wear_level='CUSTOM';p.wear=1
    p.collapse=0;p.hole_count=0;p.floor_damage=0;p.roof_damage=0;p.cracks=0
    coll=addon.generate(bpy.context,p,'WORK')
    drains=meta.get(scene,'bajantes_generadas',[])
    assert any(len(d['surviving'])<d['sections'] for d in drains),drains
    assert not closure(coll)['open_edges']
    for ob in coll.objects:
        if ob.get('drain'):
            bm=bmesh.new();bm.from_mesh(ob.data)
            assert all(f.calc_area()>1e-8 for f in bm.faces),ob.name
            assert bm.calc_volume()>0,ob.name
            bm.free()
    render(scene,ROOT/'reports/v032_worn.png',focus=(0,90,60),location=(300,-320,300),scale=340)
    (ROOT/'reports/v032.json').write_text(json.dumps(reports,indent=2),encoding='utf-8')
    print('V032_PASSED',flush=True)


if __name__=='__main__':run()
