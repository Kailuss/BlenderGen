"""Reapertura y revisión visual de los diez segundos calculados."""
import json
import sys
from pathlib import Path
import bpy
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import ruinas_panel as addon
from ruinas_panel import runtime


def run():
    'IA: Reabre resultado, valida luces/objetivos/órbita, mide movimiento residual y límite inferior y renderiza inicio y final sin recalcular Bullet.'
    addon.register();runtime.busy=True
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'dist/repro_revoco_ciclo.blend'))
    scene=bpy.context.scene;assert scene.get('physics_result_scene') and scene.frame_end==241
    assert len([o for o in scene.objects if o.type=='LIGHT'])==3
    assert len([o for o in scene.objects if o.type=='CAMERA'])==3
    assert all(c.target in list(scene.objects) for o in scene.objects for c in o.constraints if hasattr(c,'target'))
    orbit=next(o for o in scene.objects if o.get('lab_camera')=='ORBIT')
    scene.frame_set(1);start=orbit.matrix_world.translation.copy()
    scene.frame_set(241);assert (orbit.matrix_world.translation-start).length<1e-5
    bodies=[o for o in scene.objects if o.type=='MESH' and not o.get('collision_floor')]
    scene.frame_set(217);previous={o.name:o.matrix_world.translation.copy() for o in bodies}
    scene.frame_set(241)
    residual=sorted([((o.matrix_world.translation-previous[o.name]).length*1000,o.name) for o in bodies],reverse=True)
    floor=next(o for o in scene.objects if o.get('collision_floor'))
    top=max((floor.matrix_world@Vector(v)).z for v in floor.bound_box)
    escaped=[o.name for o in bodies if max((o.matrix_world@Vector(v)).z for v in o.bound_box)<top-.001]
    scene.camera=next(o for o in scene.objects if o.get('lab_camera')=='STATIC')
    scene.render.resolution_percentage=50;scene.cycles.samples=16
    for frame,label in ((1,'initial'),(241,'final')):
        scene.frame_set(frame);scene.render.filepath=str(ROOT/('reports/reported_cycle_'+label+'.png'))
        bpy.ops.render.render(write_still=True)
    report={'frames':scene.frame_end,'lights':3,'floor_bounds':[[min((floor.matrix_world@Vector(v))[i] for v in floor.bound_box),max((floor.matrix_world@Vector(v))[i] for v in floor.bound_box)] for i in range(3)],'escaped_below_floor':{o.name:list(o.matrix_world.translation) for o in bodies if o.name in escaped},'largest_displacements_last_second_mm':residual[:10]}
    (ROOT/'reports/reported_cycle_reopen.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    assert not escaped,escaped
    print('CYCLE_REOPEN_PASSED',report,flush=True)


if __name__=='__main__':run()
