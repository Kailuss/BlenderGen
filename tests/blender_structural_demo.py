"""Reproducción horneada del edificio completo, con una unión liberada."""
import sys,json,faulthandler
from pathlib import Path
import bpy
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'tests'))
import ruinas_panel as addon
from ruinas_panel.services import structural_physics as structural
from blender_v032 import render


def build_demo():
    'IA: Reabre el laboratorio validado, suelta un travesaño y hornea solo movimiento superior a 0,02 mm; conserva casa completa y vista interior separada.'
    faulthandler.dump_traceback_later(90,repeat=True)
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'dist/ruinas_estructura_preparada.blend'),use_scripts=False)
    addon.register()
    lab=next(s for s in bpy.data.scenes if s.get('structural_physics'));bpy.context.window.scene=lab;lab.frame_set(1)
    bpy.data.scenes[lab['source_scene']].ruin_settings.physics_target='BUILDING'
    bodies=[o for o in lab.objects if o.rigid_body]
    assert lab['mass_scale']==10000,'Regenera la preparación con masas normalizadas'
    prepared=json.loads((ROOT/'reports/structural_physics.json').read_text(encoding='utf8'))
    assert prepared['bodies']==len(bodies)
    checked=prepared['intact_motion_24_frames_mm']
    stability={'max_mm':checked['max'],'mean_mm':checked['mean'],'mass_scale':lab['mass_scale']}
    print('STRUCTURAL_STABILITY',stability,flush=True)
    assert stability['max_mm']<3 and stability['mean_mm']<.05,stability
    lab.frame_set(1)
    rails=[o for o in bodies if o.get('source_piece','').startswith('Madera · travesaño interior')]
    target=max(rails,key=lambda o:o.location.z)
    print('STRUCTURAL_RELEASE_REQUEST',target.name,flush=True)
    structural.release(lab,target)
    print('STRUCTURAL_RELEASE_READY',flush=True)
    tracks={o:[] for o in bodies}
    for frame in range(1,121):
        lab.frame_set(frame);dg=bpy.context.evaluated_depsgraph_get()
        for ob in bodies:tracks[ob].append(ob.evaluated_get(dg).matrix_world.copy())
        if frame%24==0:print('STRUCTURAL_DEMO_FRAME',frame,flush=True)
    drop=(tracks[target][0].translation.z-tracks[target][-1].translation.z)*1000
    assert drop>5,('la tabla no se desprende',drop)
    replay=bpy.data.scenes.new('00 REPRODUCIR - edificio completo');replay.frame_end=120
    interior=bpy.data.scenes.new('03 INTERIOR - misma simulación');interior.frame_end=120
    for scene in (replay,interior):
        scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1;scene.unit_settings.length_unit='MILLIMETERS'
        scene['ruinas_replay']=True;scene['source_scene']=lab['source_scene'];scene['lab_scene']=lab.name
        scene['playback_instructions']='Espacio: física guardada · unión roja se suelta en 13'
        scene.timeline_markers.new('Uniones conservadas',frame=1);scene.timeline_markers.new('Se suelta el travesaño rojo',frame=13)
    animated=0
    for ob in bodies:
        clone=bpy.data.objects.new(ob['source_piece'],ob.data.copy());replay.collection.objects.link(clone)
        clone['source_piece']=ob['source_piece'];clone['physical_role']=ob['physical_role'];clone.matrix_world=tracks[ob][0]
        if ob==target:
            red=bpy.data.materials.new('Unión liberada · rojo');red.diffuse_color=(.7,.08,.025,1);clone.data.materials.clear();clone.data.materials.append(red)
            clone['released_piece']=True
        # Una vista adicional, nunca una sustitución de la casa con cubierta.
        initial=tracks[ob][0].translation
        if ob['physical_role']=='ground' or (ob['physical_role']=='wood' and initial.z<.055 and any(word in ob['source_piece'].lower() for word in ('interior','suelo','planta baja'))):interior.collection.objects.link(clone)
        moving=max((m.translation-tracks[ob][0].translation).length for m in tracks[ob])>.00002 or max(m.to_quaternion().rotation_difference(tracks[ob][0].to_quaternion()).angle for m in tracks[ob])>.002
        if moving:
            animated+=1;clone.rotation_mode='QUATERNION'
            for frame,matrix in enumerate(tracks[ob],1):
                clone.location=matrix.translation;clone.rotation_quaternion=matrix.to_quaternion()
                clone.keyframe_insert(data_path='location',frame=frame);clone.keyframe_insert(data_path='rotation_quaternion',frame=frame)
    manual=bpy.data.texts.new('LEEME - estructura sin mortero');manual.write((ROOT/'docs/MANUAL_ESTRUCTURA.md').read_text(encoding='utf8'))
    bpy.context.window.scene=replay;replay.frame_set(1)
    render(replay,ROOT/'reports/structure_complete.png',focus=(0,.08,.047),location=(.24,-.28,.22),scale=.29)
    bpy.context.window.scene=interior;interior.frame_set(1)
    render(interior,ROOT/'reports/structure_interior_before.png',focus=(0,.08,.03),location=(.18,-.18,.19),scale=.24)
    interior.frame_set(120)
    render(interior,ROOT/'reports/structure_interior_after.png',focus=(0,.08,.03),location=(.18,-.18,.19),scale=.24)
    lab.frame_set(1);interior.frame_set(1);bpy.context.window.scene=replay;replay.frame_set(1)
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                space=area.spaces.active;space.shading.type='SOLID';space.shading.color_type='MATERIAL';space.shading.show_cavity=True;space.overlay.show_extras=False
                space.region_3d.view_location=Vector((0,.08,.045));space.region_3d.view_distance=.36
                space.region_3d.view_rotation=Vector((.24,-.36,.22)).to_track_quat('Z','Y');space.region_3d.view_perspective='ORTHO'
    report={'bodies':len(bodies),'animated_bodies':animated,'released_piece':target['source_piece'],'drop_mm':drop,'frames':120,'scenes':[s.name for s in bpy.data.scenes],'full_roof':True,'baked_without_addon':True,'calibrated_initial_stability':stability}
    (ROOT/'reports/structural_demo.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf8')
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'dist/ruinas_v0325_estructura_interactiva.blend'),compress=True)
    print('STRUCTURAL_DEMO_PASSED',report,flush=True)
    faulthandler.cancel_dump_traceback_later()


if __name__=='__main__':build_demo()
