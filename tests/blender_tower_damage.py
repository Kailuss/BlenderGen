"""Comprueba daño propio de torreón y retirada de losas sin vigas."""
import sys,json
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'tests'))
import ruinas_panel as addon
from ruinas_panel import runtime,meta
from blender_probe import closure
from blender_v032 import render


def run():
    'IA: Reabre fuente intacta de la prueba, aplica daño general y de cubierta por separado y exige reducción cerrada de piezas.'
    addon.register();runtime.busy=True;runtime.preview=True;scene=bpy.context.scene;p=scene.ruin_settings
    baseline=meta.get(scene,'cubierta_detalles');reports=[]
    for other in list(bpy.data.scenes):
        if other.get('structural_physics'):bpy.data.scenes.remove(other)
    scene['example_note']='Fuente dañada: preparar un laboratorio nuevo antes de simular.'
    for collapse,roof_damage in ((.55,0),(0,.7)):
        p.collapse=collapse;p.roof_damage=roof_damage;coll=addon.generate(bpy.context,p,'WORK')
        sealed=closure(coll);assert not sealed['open_edges'],sealed
        current=meta.get(scene,'cubierta_detalles');assert current['parapet_blocks']<baseline['parapet_blocks']
        assert current['deck_slabs']<baseline['deck_slabs']
        reports.append({'collapse':collapse,'roof_damage':roof_damage,'roof':current,'closure':sealed})
        render(scene,ROOT/('reports/v03216_tower_damage_%s.png'%len(reports)),focus=(0,35,75),location=(280,-320,260),scale=350)
        bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/('dist/ruinas_v03216_torre_dano_%s.blend'%len(reports))))
    (ROOT/'reports/v03216_tower_damage.json').write_text(json.dumps(reports,indent=2),encoding='utf8')
    print('TOWER_DAMAGE_PASSED',flush=True)


if __name__=='__main__':run()
