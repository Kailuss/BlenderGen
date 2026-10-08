"""Reapertura independiente de la entrega, sin addon ni autorun."""
import json,sys
from pathlib import Path
import bpy,bmesh
ROOT=Path(__file__).resolve().parents[1]


def run():
    'IA: Reabre la animación entregada sin registrar Ruinas; verifica techo, piezas cerradas, cuatro escenas, manual y caída guardada en fotogramas clave.'
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'dist/ruinas_v0325_estructura_interactiva.blend'),use_scripts=False)
    scene=bpy.context.scene;assert scene.name.startswith('00 REPRODUCIR')
    assert len([s for s in bpy.data.scenes if s.name[:2] in ('00','01','02','03')])==4
    pieces=[o for o in scene.objects if 'source_piece' in o];assert len(pieces)>1000
    assert any(o.get('physical_role')=='tile' for o in pieces)
    assert all(o.rigid_body is None for o in pieces)
    assert any('LEEME' in t.name for t in bpy.data.texts)
    released=next(o for o in pieces if o.get('released_piece'))
    scene.frame_set(1);initial=released.matrix_world.translation.copy()
    scene.frame_set(120);drop=(initial.z-released.matrix_world.translation.z)*1000
    assert drop>5 and released.animation_data
    for ob in pieces:
        bm=bmesh.new();bm.from_mesh(ob.data);assert all(e.is_manifold for e in bm.edges),ob.name;bm.free()
    lab=next(s for s in bpy.data.scenes if s.get('structural_physics'));assert lab['mass_scale']==10000
    report={'opens_at_scene':scene.name,'bodies':len(pieces),'roof_present':True,'all_pieces_closed':True,'drop_mm':drop,'addon_registered':hasattr(bpy.types.Scene,'ruin_settings'),'mass_scale':lab['mass_scale'],'manual_embedded':True}
    assert not report['addon_registered']
    sys.path.insert(0,str(ROOT/'src'))
    import ruinas_panel as addon
    addon.register()
    p=bpy.data.scenes[lab['source_scene']].ruin_settings
    assert p.physics_target=='BUILDING' and p.length==170 and p.building_depth==155 and p.interior_layout=='TWO'
    report['editable_parameters_preserved']=True
    (ROOT/'reports/structural_reopen.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf8')
    print('STRUCTURAL_REOPEN_PASSED',report,flush=True)


if __name__=='__main__':run()
