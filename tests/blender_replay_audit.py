"""Valida dimensiones de reproducción y suelo con la casa integrada guardada."""
import sys,json
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import ruinas_panel as addon


def run():
    'IA: Compara cada pieza reproducida con su laboratorio al inicio y comprueba que no haya caídas al infinito al final; solo evalúa la reproducción sin cuerpos rígidos.'
    addon.register();scene=next(s for s in bpy.data.scenes if s.get('ruinas_replay'))
    lab=next((s for s in bpy.data.scenes if s.get('ruinas_physics_lab')),None);bpy.context.window.scene=scene
    scene.frame_set(1);bpy.context.view_layer.update();maximum=0;checked=0
    for ob in scene.objects:
        if ob.type!='MESH' or lab is None:continue
        original=lab.objects.get(ob.get('replay_source_object',''))
        if original is None:
            assert ob.get('physical_role')=='ground',ob.name
            continue
        assert len(ob.data.vertices)==len(original.data.vertices),ob.name
        assert original.parent is None,original.name
        # La escena inactiva no tiene matrix_world actualizada tras cargar el archivo.
        # matrix_basis lee sus transformaciones guardadas sin evaluar Bullet.
        error=max(((ob.matrix_world@a.co)-(original.matrix_basis@b.co)).length for a,b in zip(ob.data.vertices,original.data.vertices))
        assert error<1e-6,(ob.name,error)
        maximum=max(maximum,error);checked+=1
    floor=next(o for o in scene.objects if o.get('collision_floor'))
    floor_z=max((floor.matrix_world@v.co).z for v in floor.data.vertices)
    scene.frame_set(scene.frame_end);bpy.context.view_layer.update()
    below=[]
    for ob in scene.objects:
        if ob.type=='MESH' and ob.get('physical_role') in ('wood','stone','tile','metal'):
            center=ob.matrix_world.translation.z
            if center<floor_z-.005:below.append((ob.name,center))
    report={'pieces_compared':checked,'initial_max_error_m':maximum,'below_safety_floor':below,'floor_z_m':floor_z}
    if below:
        report['floor_bounds']=[list(floor.matrix_world@v.co) for v in floor.data.vertices]
        report['escaped']={}
        for name,_ in below:
            ob=scene.objects[name];track=[]
            for frame in range(1,scene.frame_end+1,4):
                scene.frame_set(frame);bpy.context.view_layer.update();track.append([frame,*ob.matrix_world.translation])
            report['escaped'][name]={'dimensions':list(ob.dimensions),'track':track}
    path=ROOT/('reports/replay_audit.json' if lab else 'reports/replay_floor_audit.json')
    path.write_text(json.dumps(report,indent=2),encoding='utf8')
    assert not below,below[:20]
    print('REPLAY_AUDIT_PASSED',report,flush=True)


if __name__=='__main__':run()
