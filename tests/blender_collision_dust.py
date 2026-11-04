"""Residuos booleanos submilimétricos: descarte acotado sin uniones colgantes."""
import sys
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import ruinas_panel as addon
from ruinas_panel.services import physics,structural_physics


def run():
    'IA: Elimina piedra recortada diminuta y astillas recortadas más finas que un píxel de impresión, con sus uniones; conserva metal fino, piedra diseñada, fragmentos largos y la repetición sin efectos.'
    bpy.ops.wm.read_factory_settings(use_empty=True);addon.register();scene=bpy.context.scene
    pieces=[]
    for index,(role,cut,size,thick) in enumerate((('stone',True,.1,.1),('metal',True,.1,.1),('stone',False,.1,.1),('stone',True,.3,.1),('wood',True,.3,.002))):
        ob=physics.body(scene,'Prueba %s'%index,(index,0,0),(index+size,.1,thick),True)
        ob['physical_role']=role
        if cut:ob['cut_component']=0
        pieces.append(ob)
    joint=bpy.data.objects.new('Unión de residuo',None);scene.collection.objects.link(joint)
    with bpy.context.temp_override(object=joint,active_object=joint,selected_objects=[joint],selected_editable_objects=[joint]):
        bpy.ops.rigidbody.constraint_add()
    joint.rigid_body_constraint.object1=pieces[0];joint.rigid_body_constraint.object2=pieces[3]
    names=sorted([pieces[0].name,pieces[4].name])
    assert sorted(structural_physics.discard_collision_dust(scene))==names
    assert len(scene.objects)==3 and all(o.rigid_body for o in scene.objects)
    assert structural_physics.discard_collision_dust(scene)==[]
    print('COLLISION_DUST_PASSED',flush=True)


if __name__=='__main__':run()
