"""Solapes iniciales: detecta pares penetrados, ignora los que solo se tocan y desactiva su colisión."""
import sys
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import ruinas_panel as addon
from ruinas_panel.services import physics_worker


def box(name,x,kind='ACTIVE',size=.01,z=.05):
    'IA: Cubo de ensayo en metros con cuerpo rígido.'
    bpy.ops.mesh.primitive_cube_add(size=size,location=(x,0,z));ob=bpy.context.object;ob.name=name
    bpy.ops.rigidbody.object_add();ob.rigid_body.type=kind;return ob


def run():
    'IA: Un par solapado 0,1 mm se desactiva; contacto exacto, lejano y terreno no; profundidad medida dentro de tolerancia.'
    bpy.ops.wm.read_factory_settings(use_empty=True);addon.register();scene=bpy.context.scene
    # B, más pequeño, entra 0,1 mm en A; C y D solo se tocan; G es terreno solapado con F.
    a=box('A',0);b=box('B',.008-.0001,size=.006);c=box('C',.03);d=box('D',.04);e=box('E',.2,'PASSIVE')
    f=box('F',.3);g=box('G',.3,'PASSIVE',size=.02,z=.05-.0149);g['physical_role']='ground'
    pairs=physics_worker.overlapping_pairs(scene,2e-5)
    assert set(pairs)=={('A','B'),('F','G')},pairs
    assert abs(pairs[('A','B')]-.0001)<2e-5,pairs
    report=physics_worker.lab_experiments(scene)
    assert report['overlap_disabled']['pairs']==1 and report['overlap_disabled']['kept_colliding']==1,report
    joints=[o for o in scene.objects if o.rigid_body_constraint]
    assert len(joints)==1 and joints[0].rigid_body_constraint.disable_collisions and joints[0].rigid_body_constraint.type=='GENERIC'
    scene['lab_overlap_disable_m']=-1
    assert 'overlap_disabled' not in physics_worker.lab_experiments(scene)
    print('OVERLAP_PAIRS_PASSED',report,flush=True)


if __name__=='__main__':run()
