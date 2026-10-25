"""Conservación geométrica al agrupar residuos de corte no resolubles."""
import sys
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import ruinas_panel as addon
from ruinas_panel import runtime
from ruinas_panel.services import structural_physics,physics


def points(objects):
    'IA: Compara vértices mundiales con precisión submicrométrica sin depender del orden de BMesh.'
    return sorted(tuple(round(v,9) for v in ob.matrix_world@vert.co) for ob in objects for vert in ob.data.vertices)


def run():
    'IA: Conserva vértices, caras y volumen del residuo; no agrega piezas ajenas y deja intacta una malla compartida por otro objeto.'
    addon.register();runtime.busy=True;scene=bpy.context.scene
    for ob in list(scene.objects):bpy.data.objects.remove(ob,do_unlink=True)
    parent=physics.body(scene,'Padre',(0,0,10),(5,5,15),True)
    thin=physics.body(scene,'Residuo',(5,0,10),(5.006,.3,10.2),True)
    other=physics.body(scene,'Ajeno',(5,1,10),(5.006,1.3,10.2),True)
    for ob in (parent,thin,other):ob['source_piece']='origen';ob['physical_role']='wood';ob['cut_component']=0
    other['source_piece']='otro origen'
    copy=parent.copy();copy.name='Referencia';scene.collection.objects.link(copy);copy['source_piece']='referencia'
    old_data=copy.data;before=points([parent,thin]);faces=len(parent.data.polygons)+len(thin.data.polygons)
    report=structural_physics.attach_collision_slivers(scene)
    assert report==[{'fragment':'Residuo','attached_to':'Padre'}],report
    assert points([parent])==before
    assert len(parent.data.polygons)==faces and copy.data==old_data and len(copy.data.polygons)==6
    assert 'Ajeno' in scene.objects and 'Residuo' not in scene.objects
    assert not structural_physics.attach_collision_slivers(scene)
    floor=physics.body(scene,'Seguridad',(-100,-100,-5),(100,100,0),False);floor['collision_floor']=True
    top=max((floor.matrix_world@v.co).z for v in floor.data.vertices)
    structural_physics.reinforce_safety_floor(scene)
    assert max((floor.matrix_world@v.co).z for v in floor.data.vertices)==top
    assert min((floor.matrix_world@v.co).z for v in floor.data.vertices)<=top-.5
    once=points([floor]);structural_physics.reinforce_safety_floor(scene);assert points([floor])==once
    print('COLLISION_SLIVERS_PASSED',flush=True)


if __name__=='__main__':run()
