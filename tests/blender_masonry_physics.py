"""Ensayo reproducible de agujero e impacto en mampostería seca."""
import sys,json,time
from pathlib import Path
import bpy,bmesh
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import ruinas_panel as addon
from ruinas_panel.services import masonry_physics as masonry

def run():
    'IA: Verifica caída colectiva, suelo y mallas; guarda laboratorios editables y reproducciones independientes del addon.'
    bpy.ops.wm.read_factory_settings(use_empty=True);addon.register()
    source=bpy.context.scene;source.name='00 AJUSTES';source.ruin_settings.live_preview=False
    reports={};replays=[]
    for kind in ('HUECO','IMPACTO','TORRE'):
        source.ruin_settings.physics_masonry_shape='TOWER' if kind=='TORRE' else 'WALL'
        lab=masonry.prepare(source);lab.name=kind+' · EDITAR';bpy.context.window.scene=lab
        if kind=='HUECO':
            chosen=[o for o in lab.objects if o.get('masonry_brick') and o['course']<3 and abs(o.location.x)<.018]
            for ob in lab.objects:ob.select_set(False)
            for ob in chosen:ob.select_set(True)
            lab.view_layers[0].objects.active=chosen[0]
            before=len(lab.objects);assert bpy.ops.ruin.masonry_remove()=={'FINISHED'}
            assert before-len(lab.objects)>=6
        else:masonry.impactor(lab)
        objects=[o for o in lab.objects if o.type=='MESH'];bricks=[o for o in objects if o.get('masonry_brick')]
        assert len(bricks)<=96 and all(o.rigid_body.type=='ACTIVE' for o in bricks)
        assert any(o.rigid_body_constraint for o in lab.objects)
        poses=[];started=time.perf_counter()
        for frame in range(1,121):
            lab.frame_set(frame);deps=bpy.context.evaluated_depsgraph_get()
            poses.append({o.name:o.evaluated_get(deps).matrix_world.copy() for o in objects})
        moved=sum((poses[-1][o.name].translation-poses[0][o.name].translation).length>.006 for o in bricks)
        low=min((poses[-1][o.name]@v.co).z for o in objects if not o.get('collision_floor') for v in o.data.vertices)
        assert moved>=6,(kind,moved)
        assert low>-.001,(kind,low)
        for o in objects:
            bm=bmesh.new();bm.from_mesh(o.data);assert all(e.is_manifold for e in bm.edges);bm.free()
        reports[kind]={'bricks':len(bricks),'moved_over_6mm':moved,'lowest_mm':low*1000,'seconds':time.perf_counter()-started}
        print('MASONRY',kind,reports[kind],flush=True)
        replay=bpy.data.scenes.new(kind+' · REPRODUCIR');replay['ruinas_replay']=True;replay['lab_scene']=lab.name;replay['source_scene']=source.name
        replay['playback_instructions']='Pulsa Espacio · ladrillos bajo gravedad';replay.frame_end=120
        for original in objects:
            ob=bpy.data.objects.new(original.name+' · animado',original.data);replay.collection.objects.link(ob)
            for frame,pose in enumerate(poses,1):
                ob.matrix_world=pose[original.name];ob.keyframe_insert(data_path='location',frame=frame);ob.keyframe_insert(data_path='rotation_euler',frame=frame)
        lab.frame_set(1);replay.frame_set(1);replays.append(replay)
    source.ruin_settings.physics_masonry_shape='WALL'
    bpy.context.window.scene=replays[1]
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                area.spaces.active.region_3d.view_distance=.22;area.spaces.active.region_3d.view_location=(0,0,.045)
                area.spaces.active.clip_start=.0001;area.spaces.active.clip_end=10
    manual=bpy.data.texts.new('LEEME · física de ladrillos');manual.write('REPRODUCIR: Espacio muestra la simulación completa. EDITAR: todos los ladrillos son objetos activos. Instala addon v0326, fotograma 1, selecciona con Mayús o B. Ruinas > Abrir hueco retira varios ladrillos. Añadir piedra crea un impacto por gravedad. Simular derrumbe calcula 120 fotogramas. Suelo pasivo de 1 metro. No hay resortes. Los ladrillos se desplazan enteros: no se fracturan internamente. Usa 00 AJUSTES para crear un ensayo limpio. No exporta aún mortero ni modifica la casa.')
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'dist/ruinas_v0326_ladrillos.blend'))
    (ROOT/'reports/masonry_physics.json').write_text(json.dumps(reports,indent=2),encoding='utf8')
    print('MASONRY_PASSED',flush=True)

if __name__=='__main__':run()
