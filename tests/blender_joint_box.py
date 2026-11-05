"""Regresión del encaje imposible de la casa máxima: ménsula de tejadillo atravesada por un montante de mirador."""
import sys,json
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import ruinas_panel as addon
from ruinas_panel.services import structural_physics


def piece(name,data,role):
    'IA: Objeto de malla desde el volcado del diagnóstico de encaje, con su papel físico y nombre de origen.'
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(data['vertices'],[],data['faces']);mesh.update()
    ob=bpy.data.objects.new(name,mesh);bpy.context.scene.collection.objects.link(ob)
    ob['physical_role']=role;ob['source_piece']=data['name'];return ob


def run():
    'IA: El recorte ya no aborta: la ménsula sigue siendo un sólido cerrado con volumen, sin cruzarse con el montante.'
    bpy.ops.wm.read_factory_settings(use_empty=True);addon.register()
    data=json.loads((ROOT/'tests/fixtures/joint_tejadillo_mirador.json').read_text(encoding='utf8'))
    target=piece('ménsula',data['target'],'wood');cutter=piece('montante',data['cutter'],'wood')
    before=structural_physics.valid(target.data.copy())
    report={'covered_pieces_removed':0,'joints_cut':0}
    remaining=structural_physics.resolve([target,cutter],report)
    assert target in remaining and cutter in remaining,report
    after=structural_physics.valid(target.data)
    assert 0<after<before,(before,after,report)
    assert not structural_physics.tree(target).overlap(structural_physics.tree(cutter)),report
    print('JOINT_BOX_PASSED',json.dumps({'before_mm3':round(before,3),'after_mm3':round(after,3),'box_joints':report.get('box_joints'),'local_joints':report.get('local_joints'),'tolerant':report.get('tolerant_joints')}),flush=True)


if __name__=='__main__':run()
