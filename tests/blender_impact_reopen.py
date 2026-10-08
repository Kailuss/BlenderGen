"""Reapertura, mallas y vista de la entrega sin depender de scripts automáticos."""
import sys,json
from pathlib import Path
import bpy,bmesh
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'tests'))
from blender_v032 import render

def run():
    'IA: Comprueba reproducción sin addon, mallas cerradas y retorno entre escalas; incorpora manual completo y encuadre de la casa.'
    replay=bpy.data.scenes['00 CASA · REPRODUCIR'];lab=bpy.data.scenes['02 CASA · EDITAR IMPACTO'];source=bpy.data.scenes['01 CASA DISEÑADA']
    assert not any(o.rigid_body for o in replay.objects)
    assert sum(bool(o.get('fracture_fragment')) for o in lab.objects)==32
    for ob in lab.objects:
        if ob.type!='MESH':continue
        bm=bmesh.new();bm.from_mesh(ob.data);assert all(e.is_manifold for e in bm.edges),ob.name;assert bm.calc_volume()>0,ob.name;bm.free()
    moving=next(o for o in replay.objects if o.animation_data and 'rotura' in o.name)
    replay.frame_set(1);start=moving.matrix_world.copy();replay.frame_set(120)
    assert (moving.matrix_world.translation-start.translation).length>.00001
    import ruinas_panel as addon
    addon.register()
    from ruinas_panel.ui.operators import frame_view
    measurements={}
    for scene in (source,lab):
        bpy.context.window.scene=scene;scene.frame_set(1);frame_view(bpy.context)
        for area in bpy.context.screen.areas:
            if area.type=='VIEW_3D':
                sp=area.spaces.active;measurements[scene.name]={'near':sp.clip_start,'far':sp.clip_end,'distance':sp.region_3d.view_distance}
                assert sp.clip_end>sp.region_3d.view_distance and sp.clip_end/sp.clip_start<1e7
    bpy.context.window.scene=replay;replay.frame_set(1)
    replay.unit_settings.system='METRIC';replay.unit_settings.length_unit='MILLIMETERS'
    points=[o.matrix_world@Vector(v) for o in replay.objects if o.type=='MESH' and not o.get('collision_floor') for v in o.bound_box]
    lo=Vector([min(v[k] for v in points) for k in range(3)]);hi=Vector([max(v[k] for v in points) for k in range(3)])
    center=(lo+hi)*.5;span=max(hi-lo)
    for frame,label in ((1,'before'),(120,'after')):
        replay.frame_set(frame);render(replay,ROOT/('reports/impact_house_'+label+'.png'),focus=center,location=center+Vector((.25,.35,.23)),scale=span*1.6)
    replay.frame_set(1);frame_view(bpy.context)
    text=bpy.data.texts.get('LEEME');text.clear();text.write((ROOT/'docs/MANUAL_IMPACTOS.md').read_text(encoding='utf8'))
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'dist/ruinas_v0327_casa_impacto.blend'))
    (ROOT/'reports/impact_reopen.json').write_text(json.dumps(measurements,indent=2),encoding='utf8')
    print('IMPACT_REOPEN_PASSED',measurements,flush=True)

if __name__=='__main__':run()
