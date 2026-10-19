"""Reapertura de los dos laboratorios de entrega."""
import json
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1]


def run():
    'IA: Reabre cada archivo guardado y exige fuente activa y un laboratorio con los cuerpos del informe, sin regenerar ni simular.'
    for kind in ('WOOD','STONE'):
        bpy.ops.wm.open_mainfile(filepath=str(ROOT/('dist/ruinas_v03216_%s_0.blend'%kind)))
        assert not bpy.context.scene.get('structural_physics')
        labs=[s for s in bpy.data.scenes if s.get('structural_physics')]
        assert len(labs)==1
        report=json.loads(labs[0]['preparation_report'])
        assert sum(o.rigid_body is not None for o in labs[0].objects)>=report['bodies']
        assert not report['unconnected']
    print('V03216_REOPEN_PASSED',flush=True)


if __name__=='__main__':run()
