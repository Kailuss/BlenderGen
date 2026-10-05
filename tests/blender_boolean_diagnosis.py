"""Diagnóstico localizado de caras degeneradas en mampostería."""
import sys,json
from pathlib import Path
import bpy,bmesh
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'tests'))
import ruinas_panel as addon
from ruinas_panel import runtime


def run():
    'IA: Reproduce la casa de dos plantas y registra coordenadas de caras casi nulas sin corregirlas.'
    bpy.ops.wm.read_factory_settings(use_empty=True);addon.register();runtime.busy=True
    p=bpy.context.scene.ruin_settings;p.live_preview=False;p.batch_preview=False;p.use_instances=True
    p.layout_mode='ROOM';p.length=180;p.building_depth=90;p.height_type='TWO';p.seed=47;p.lock_distribution=False
    p.damage_enabled=False;p.floor_beams=True;p.windows_enabled=True;p.door_enabled=True
    coll=addon.generate(bpy.context,p,'WORK');bad=[]
    from blender_probe import mesh_objects
    for ob in mesh_objects(coll):
        bm=bmesh.new();bm.from_mesh(ob.data)
        for f in bm.faces:
            if f.calc_area()<1e-8:
                bad.append({'object':ob.name,'area':f.calc_area(),'coords':[list(v.co) for v in f.verts]})
        bm.free()
    (ROOT/'reports/boolean_diagnosis.json').write_text(json.dumps(bad,indent=2),encoding='utf-8')
    print('DEGENERATE',len(bad),bad[:2],flush=True)


if __name__=='__main__':run()
