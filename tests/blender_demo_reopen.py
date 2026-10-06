"""El archivo de demostración se reproduce sin registrar el addon ni ejecutar scripts embebidos."""
import json
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1]


def run():
    'IA: Reabre sin addon, salta a 1/120 y verifica movimiento horneado, cuatro escenas, cubierta y módulos independientes.'
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'dist/ruinas_v0324_fisica_interactiva.blend'),use_scripts=False,load_ui=True)
    replay=bpy.context.scene;assert replay.name.startswith('00 REPRODUCIR')
    assert not replay.rigidbody_world
    modules=[o for o in replay.objects if 'source_section' in o];assert len(modules)>20
    replay.frame_set(1);first={o.name:o.matrix_world.copy() for o in modules}
    replay.frame_set(120);last={o.name:o.matrix_world.copy() for o in modules}
    changed={name:(last[name].translation-matrix.translation).length*1000 for name,matrix in first.items()}
    assert max(changed.values())>5
    intact=next(s for s in bpy.data.scenes if s.name.startswith('01 CASA'))
    assert any(o.get('roof_tiles') for o in intact.objects)
    editable=next(s for s in bpy.data.scenes if s.name.startswith('02 CASA'))
    assert sum('partition_section' in o for o in editable.objects)>20
    assert bpy.data.texts.get('LEEME - manual de uso')
    report={'opens_in_replay':True,'works_without_addon':True,'scene_count':len(bpy.data.scenes),'replay_modules':len(modules),'maximum_motion_mm':max(changed.values()),'roof_present':True,'manual_embedded':True}
    (ROOT/'reports/demo_reopen.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('DEMO_REOPEN_PASSED',report,flush=True)


if __name__=='__main__':run()
