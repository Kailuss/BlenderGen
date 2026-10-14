"""Uniones de madera precortada: solo continuidad conocida, sin puentes arbitrarios."""
import sys,json
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import ruinas_panel as addon
from ruinas_panel import config,runtime
from ruinas_panel.geometry import primitives
from ruinas_panel.services import structural_physics,height_selection


def run():
    'IA: Une extremos astillados de etapa 1, rechaza etapas avanzadas y huecos grandes, evita duplicados y prueba filtros de selección.'
    bpy.ops.wm.read_factory_settings(use_empty=True);addon.register();runtime.busy=True
    source=bpy.context.scene;source.ruin_settings.live_preview=False
    coll=bpy.data.collections.new(config.COLLECTION);source.collection.children.link(coll)
    mat=primitives.material('Madera',(.3,.2,.1))
    for row,(stage,gap) in enumerate(((1,2),(2,2),(1,5))):
        for index in range(2):
            x=index*(10+gap)
            ob=primitives.block('Madera de prueba',x,x+10,row*15,row*15+3,10,13,coll,mat)
            ob['roof_fracture_parent']='viga %s'%row;ob['roof_member_segment']=index;ob['roof_damage_stage']=stage
    for row in range(2):primitives.block('Tierra de prueba',-1,23,row*15-1,row*15+4,8,10,coll,mat)
    lab=structural_physics.prepare(source);bpy.context.window.scene=lab
    joints=[o for o in lab.objects if o.get('timber_fracture_joint')]
    assert len(joints)==1,len(joints)
    c=joints[0].rigid_body_constraint
    assert c.use_breaking and c.object1['roof_fracture_parent']==c.object2['roof_fracture_parent']=='viga 0'
    assert structural_physics.connect_timber_fragments(lab)==0
    p=lab.ruin_settings;p.physics_selection_material='WOOD';p.physics_selection_percent=50
    chosen=height_selection.choose(lab);assert len(chosen)==3
    assert all(o.get('physical_role')=='wood' for o in chosen)
    p.physics_selection_material='STONE';assert not height_selection.choose(lab)
    ground=[o for o in lab.objects if o.get('physical_role')=='ground' and not o.get('collision_floor')]
    before=sorted(tuple(round(c,8) for c in o.matrix_world@v.co) for o in ground for v in o.data.vertices)
    assert structural_physics.merge_ground(lab)==2
    ground=[o for o in lab.objects if o.get('physical_role')=='ground' and not o.get('collision_floor')]
    after=sorted(tuple(round(c,8) for c in o.matrix_world@v.co) for o in ground for v in o.data.vertices)
    assert before==after and len(ground)==1
    assert sum(bool(o.get('collision_floor')) for o in lab.objects)==1
    assert all(o.rigid_body_constraint.object1 and o.rigid_body_constraint.object2 for o in lab.objects if o.rigid_body_constraint)
    assert structural_physics.prune_static_constraints(lab)==0
    for ob in lab.objects:
        if ob.rigid_body:ob.rigid_body.type='PASSIVE'
    assert structural_physics.prune_static_constraints(lab)==5
    assert structural_physics.prune_static_constraints(lab)==0
    print('TIMBER_JOINTS_PASSED',json.loads(lab['preparation_report'])['timber_fracture_joints'],flush=True)


if __name__=='__main__':run()
