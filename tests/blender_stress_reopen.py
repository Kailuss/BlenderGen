"""Verificación de la entrega máxima: reproducción, STL y vistas antes/después."""
import json,sys
from pathlib import Path
import bpy,bmesh,numpy as np
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'tests'))
from blender_v032 import render


def audit_stl(path):
    'IA: Relee los float32 reales del STL y exige dos caras por arista, triángulos no nulos, orientación coherente y volumen positivo.'
    dtype=np.dtype([('normal','<f4',(3,)),('vertices','<f4',(3,3)),('attribute','<u2')])
    with path.open('rb') as stream:
        stream.seek(80);count=int(np.fromfile(stream,dtype='<u4',count=1)[0]);data=np.fromfile(stream,dtype=dtype)
    assert len(data)==count and path.stat().st_size==84+50*count
    points,indices=np.unique(data['vertices'].reshape(-1,3),axis=0,return_inverse=True)
    faces=indices.reshape(-1,3)
    directed=np.concatenate((faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]))
    edges=np.sort(directed,axis=1);unique,inverse,counts=np.unique(edges,axis=0,return_inverse=True,return_counts=True)
    assert np.all(counts==2),'STL con aristas abiertas o no manifold'
    directions=np.where(directed[:,0]<directed[:,1],1,-1)
    assert np.all(np.bincount(inverse,weights=directions)==0),'Orientación inconsistente'
    triangles=data['vertices'].astype(np.float64)
    area=np.linalg.norm(np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0]),axis=1)/2
    volume=np.einsum('ij,ij->i',triangles[:,0],np.cross(triangles[:,1],triangles[:,2])).sum()/6
    assert np.all(area>1e-12) and volume>0
    return {'triangles':count,'closed':True,'consistent_orientation':True,'volume_mm3':float(volume),'bounds_mm':[points.min(axis=0).tolist(),points.max(axis=0).tolist()]}


def run():
    'IA: Reabre sin autorun, comprueba todas las mallas físicas, movimiento y STL; guarda casa, laboratorio, reproducción y sólido con manual y encuadre.'
    replay=next(s for s in bpy.data.scenes if s.get('physics_result_scene'))
    lab=next(s for s in bpy.data.scenes if s.get('ruinas_physics_lab'))
    source=bpy.data.scenes[lab['source_scene']]
    exported=next(s for s in bpy.data.scenes if s.get('physical_export_report'))
    assert not any(o.rigid_body for o in replay.objects)
    for ob in lab.objects:
        if ob.type!='MESH':continue
        bm=bmesh.new();bm.from_mesh(ob.data)
        try:assert all(e.is_manifold for e in bm.edges) and bm.calc_volume()>0,ob.name
        finally:bm.free()
    moving=[o for o in replay.objects if o.animation_data and not o.get('impactor')]
    assert len(moving)>100,'No se reproduce un derrumbe de alcance amplio'
    bpy.context.window.scene=replay;replay.frame_set(1)
    positions={o:o.matrix_world.translation.copy() for o in moving}
    replay.frame_set(replay.frame_end)
    displacements=[(o.matrix_world.translation-start).length*1000 for o,start in positions.items()]
    assert max(displacements)>1,'No hay movimiento visible'
    report=audit_stl(ROOT/'dist/ruinas_v0328_maxima.stl')
    report.update(animated_pieces=len(moving),moved_over_1mm=sum(d>1 for d in displacements),max_displacement_mm=max(displacements))
    source.name='01 CASA MAXIMA · EDITAR';lab.name='02 LABORATORIO · ZONA MOVIL';replay.name='00 REPRODUCCION · ESPACIO';exported.name='03 SOLIDO · STL'
    for scene in (lab,replay,exported):scene['source_scene']=source.name
    for scene in (replay,exported):scene['lab_scene']=lab.name
    replay['structural_physics']=True
    for ob in replay.objects:
        if ob.get('collision_floor'):ob.hide_render=True;ob.hide_set(True)
    replay.frame_set(1)
    points=[o.matrix_world@Vector(v) for o in replay.objects if o.type=='MESH' and not o.get('collision_floor') and not o.get('impactor') for v in o.bound_box]
    lo=Vector([min(v[k] for v in points) for k in range(3)]);hi=Vector([max(v[k] for v in points) for k in range(3)]);center=(lo+hi)*.5;span=max(hi-lo)
    for frame,label in ((1,'before'),(replay.frame_end,'after')):
        replay.frame_set(frame)
        render(replay,ROOT/('reports/stress_max_'+label+'.png'),focus=center,location=center+Vector((.34,-.4,.3)),scale=span*1.7)
    bpy.context.window.scene=exported
    render(exported,ROOT/'reports/stress_max_solid.png',focus=center*1000,location=center*1000+Vector((340,-400,300)),scale=span*1700)
    bpy.context.window.scene=replay
    import ruinas_panel as addon
    addon.register()
    from ruinas_panel.ui.operators import frame_view
    replay.frame_set(1);frame_view(bpy.context)
    text=bpy.data.texts.get('LEEME') or bpy.data.texts.new('LEEME');text.clear();text.write((ROOT/'docs/MANUAL_CARGA_MAXIMA.md').read_text(encoding='utf8'))
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'dist/ruinas_v0328_maxima.blend'))
    (ROOT/'reports/stress_max_reopen.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print('STRESS_REOPEN_PASSED',report,flush=True)


if __name__=='__main__':run()
