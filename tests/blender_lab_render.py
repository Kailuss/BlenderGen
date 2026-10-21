"""Regresión de corte comunicado y equipo de render."""
import sys,json
from pathlib import Path
import bpy,bmesh
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from ruinas_panel.services import fragile_physics,lab_cameras


def run():
    'IA: Reintenta el corte real capturado y comprueba luces, objetivos y copia independiente; renderiza una casa existente convertida de mm a metros.'
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'dist/repro_revoco.blend'))
    ob=sorted((o for o in bpy.data.objects if o.name.startswith('FALLO_REVOCO')),key=lambda o:o.name)[-1]
    bm=bmesh.new();bm.from_mesh(ob.data)
    print('INPUT_SOLID',len(bm.faces),sum(not e.is_manifold for e in bm.edges),bm.calc_volume(),flush=True)
    bmesh.ops.triangulate(bm,faces=list(bm.faces))
    print('TRIANGULATED',sum(not e.is_manifold for e in bm.edges),flush=True);bm.free()
    bm=bmesh.new();bm.from_mesh(ob.data);fragile_physics.triangulate_closed(bm)
    print('SAFE_TRIANGULATED',sum(not e.is_manifold for e in bm.edges),flush=True);bm.free()
    parts=fragile_physics.split(ob.data,int(ob['axis']),int(ob['seed']))
    assert len(parts)==2
    print('REPORTED_SPLIT_PASSED',flush=True)
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'dist/ruinas_escalera_piedra_revision.blend'))
    scene=bpy.context.scene
    for ob in list(scene.objects):
        if ob.type!='MESH':bpy.data.objects.remove(ob,do_unlink=True)
        else:
            ob.scale*=.001;ob.location*=.001
    bpy.context.view_layer.update()
    lab_cameras.create(scene)
    assert {o.data.type for o in scene.objects if o.type=='LIGHT'}=={'SUN','AREA','SPOT'}
    assert all(o.constraints[0].target for o in scene.objects if o.type=='CAMERA')
    copy=bpy.data.scenes.new('Comprobación reproducción')
    lab_cameras.copy_to_replay(scene,copy)
    assert all(c.target in list(copy.objects) for o in copy.objects if o.type=='CAMERA' for c in o.constraints)
    scene.cycles.samples=16;scene.render.resolution_percentage=50
    scene.render.filepath=str(ROOT/'reports/lab_render.png')
    bpy.ops.render.render(write_still=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'dist/ruinas_render_revision.blend'))
    print('LAB_RENDER_PASSED',flush=True)


if __name__=='__main__':run()
