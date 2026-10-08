"""Demo legible y reproducible: retirada controlada de un apoyo y caída física."""
import sys,json
from pathlib import Path
import bpy,bmesh
from mathutils import Matrix,Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'tests'))
import ruinas_panel as addon
from ruinas_panel import runtime,meta,config
from ruinas_panel.services import physics
from blender_probe import digest,closure
from blender_v032 import render


def copy_scene(coll,name,unit=.001):
    'IA: Copia piezas sin fusionar a una escena estática con datos propios, conservando IDs de secciones.'
    scene=bpy.data.scenes.new(name);scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=unit
    for ob in coll.objects:
        clone=bpy.data.objects.new(ob.name,ob.data.copy());scene.collection.objects.link(clone);clone.matrix_world=ob.matrix_world.copy()
        for key in ob.keys():clone[key]=ob[key]
    return scene


def frame_views(scene):
    'IA: Presenta la reproducción con escala y orientación legibles al abrir el blend.'
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                space=area.spaces.active;space.shading.type='SOLID';space.shading.color_type='OBJECT';space.shading.show_cavity=True
                space.region_3d.view_location=Vector((0,.081,.026));space.region_3d.view_distance=.24
                space.region_3d.view_rotation=Vector((.15,-.25,.15)).to_track_quat('Z','Y');space.region_3d.view_perspective='ORTHO'
            elif area.type=='DOPESHEET_EDITOR' and screen==bpy.context.screen:
                region=next((r for r in area.regions if r.type=='WINDOW'),None)
                if region:
                    with bpy.context.temp_override(area=area,region=region):
                        if bpy.ops.action.view_all.poll():bpy.ops.action.view_all()


def run():
    'IA: Genera casa con tejado, daño y módulos; calcula caída, hornea transformaciones visibles sin addon y verifica desplazamiento real de descendientes.'
    if addon.bl_info['version']>=(0,32,5):
        # La demostración de bloques apilados solo describe la versión anterior.
        # La preparación nueva se valida en blender_structural_physics.py.
        from blender_structural_demo import build_demo
        return build_demo()
    bpy.ops.wm.read_factory_settings(use_empty=True);addon.register();runtime.busy=True;runtime.preview=True
    source=bpy.context.scene;source.name='02 CASA EDITABLE - piezas y daño';p=source.ruin_settings;p.live_preview=False
    p.layout_mode='ROOM';p.interior_layout='TWO';p.length=170;p.building_depth=155;p.height_type='ONE';p.seed=17;p.lock_distribution=False
    p.batch_preview=False;p.use_instances=False;p.door_enabled=True;p.door_width=40;p.door_leaf=False
    p.windows_enabled=True;p.ground_floor=True;p.roof_frame=True;p.roof_tiles=True;p.roof_gables=True
    p.wood_grain=1;p.damage_enabled=False;p.wear_level='CUSTOM';p.wear=.1;p.cracks=0;p.rubble_amount=0;p.ground_roughness=0
    p.collapse=.32;p.wood_damage=.5;p.floor_damage=0;p.roof_damage=0;p.hole_count=0;p.preview_quality='WORK';p.physics_target='ROOM1'
    coll=addon.generate(bpy.context,p,'WORK');intact=copy_scene(coll,'01 CASA CON TEJADO - detalle completo')
    assert any(o.get('roof_tiles') for o in intact.objects)
    p.damage_enabled=True;coll=addon.generate(bpy.context,p,'WORK');assert not closure(coll)['open_edges'];before=digest(coll)
    source_parts={o['partition_section']:o for o in coll.objects if 'partition_section' in o}
    lab=physics.prepare(source);lab.name='03 LABORATORIO - física recalculable';bpy.context.window.scene=lab
    bodies=[o for o in lab.objects if 'source_section' in o]
    roots=[o for o in bodies if o['source_support']=='ground']
    def descendants(root):
        'IA: Sigue referencias de apoyo para elegir una columna con caída medible.'
        found={root['source_section']}
        for _ in bodies:
            for ob in bodies:
                if ob['source_support'] in found:found.add(ob['source_section'])
        return found
    root=max(roots,key=lambda o:len(descendants(o)));fallers=descendants(root)-{root['source_section']}
    assert fallers
    lab.view_layers[0].objects.active=root;root.select_set(True)
    assert bpy.ops.ruin.physics_release()=={'FINISHED'}
    lab.rigidbody_world.time_scale=.2
    tracks={ob['source_section']:[] for ob in bodies}
    for frame in range(1,121):
        lab.frame_set(frame);dg=bpy.context.evaluated_depsgraph_get()
        for ob in bodies:tracks[ob['source_section']].append(ob.evaluated_get(dg).matrix_world.copy())
    drops={key:(tracks[key][0].translation.z-tracks[key][-1].translation.z)*1000 for key in fallers}
    assert max(drops.values())>5,drops
    assert digest(coll)==before
    lab['physics_simulated']=120
    replay=bpy.data.scenes.new('00 REPRODUCIR - Espacio para ver la caída');replay.unit_settings.system='METRIC';replay.unit_settings.scale_length=1;replay.frame_end=120
    replay['ruinas_replay']=True;replay['source_scene']=source.name;replay['lab_scene']=lab.name
    for index,ob in enumerate(bodies):
        key=ob['source_section'];origin=Matrix(json.loads(ob['initial_matrix']))
        original=source_parts[key];mesh=original.data.copy();mesh.transform(origin.inverted()@Matrix.Scale(.001,4)@original.matrix_world)
        clone=bpy.data.objects.new('Módulo '+key,mesh);replay.collection.objects.link(clone);clone.rotation_mode='QUATERNION'
        clone['source_section']=key;clone.color=(.72,.12,.06,1) if ob==root else ((.62,.39,.20,1) if index%2 else (.37,.21,.10,1))
        for frame,matrix in enumerate(tracks[key],1):
            clone.location=matrix.translation;clone.rotation_quaternion=matrix.to_quaternion()
            clone.keyframe_insert(data_path='location',frame=frame);clone.keyframe_insert(data_path='rotation_quaternion',frame=frame)
    floor=next(o for o in lab.objects if o.name.startswith('Ensayo · suelo'))
    ground=bpy.data.objects.new('Suelo de ensayo',floor.data.copy());ground.matrix_world=floor.matrix_world.copy();ground.color=(.22,.23,.25,1);replay.collection.objects.link(ground)
    for frame,label in ((1,'INICIO'),(12,'APOYO RETIRADO'),(24,'CAÍDA POR FÍSICA'),(120,'REPOSO')):replay.timeline_markers.new(label,frame=frame)
    bpy.context.window.scene=replay;replay.frame_set(1)
    render(replay,ROOT/'reports/demo_physics_before.png',focus=(0,.081,.025),location=(.15,-.20,.17),scale=.23)
    replay.frame_set(120)
    render(replay,ROOT/'reports/demo_physics_after.png',focus=(0,.081,.025),location=(.15,-.20,.17),scale=.23)
    replay.frame_set(1);frame_views(replay)
    manual=(ROOT/'docs/MANUAL_FISICA.md').read_text(encoding='utf-8')
    text=bpy.data.texts.new('LEEME - manual de uso');text.write(manual)
    report={'scenes':[s.name for s in bpy.data.scenes],'support_removed':root['source_section'],'descendant_drop_mm':drops,'frames':120,'animation_baked_to_keyframes':True,'source_unchanged':True,'replay_modules':len(bodies)}
    (ROOT/'reports/physics_demo.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'dist/ruinas_v0324_fisica_interactiva.blend'))
    print('PHYSICS_DEMO_PASSED',report,flush=True)


if __name__=='__main__':run()
