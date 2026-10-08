"""Comparación de tabiques v0324 y actuales con los mismos parámetros."""
import sys,json,time,types,subprocess
from pathlib import Path
from types import SimpleNamespace
import bpy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from ruinas_panel import config,meta,runtime
from ruinas_panel.structure import interiors,floor_plan


def run():
    'IA: Compara caras, tiempo y número de piezas del mismo plano; la referencia se lee del commit publicado, sin sustituir la fuente editable.'
    runtime.preview=True;runtime.quality='WORK'
    p=SimpleNamespace(interior_layout='THREE',layout_mode='ROOM',height=112,ground_floor=True,wood_grain=.8,wood_damage=0,seed=47,collapse=0,lock_distribution=False,building_depth=190,thickness=9,length=220,projection=2,break_position=.5)
    plan=floor_plan.plan(p,(-100,100,5,185),{'left':-20,'right':20},{'y0':155});meta.put(bpy.context.scene,'plano_interior',plan)
    previous=types.ModuleType('ruinas_panel.structure.previous_interiors');previous.__package__='ruinas_panel.structure'
    text=subprocess.check_output(['git','show','4b90388:src/ruinas_panel/structure/interiors.py'],cwd=ROOT).decode('utf8')
    exec(compile(text,'v0324_interiors','exec'),previous.__dict__)
    original=(config.PARTITION_SECTION_WIDTH,config.PARTITION_SECTION_HEIGHT);results={}
    try:
        for name,module,width,height in [('v0324',previous,12,18),('v0325',interiors,*original)]:
            config.PARTITION_SECTION_WIDTH=width;config.PARTITION_SECTION_HEIGHT=height
            coll=bpy.data.collections.new(name);bpy.context.scene.collection.children.link(coll)
            start=time.perf_counter();module.build(coll,p,bpy.context.scene)
            results[name]={'seconds':time.perf_counter()-start,'objects':len(coll.objects),'faces':sum(len(o.data.polygons) for o in coll.objects)}
    finally:config.PARTITION_SECTION_WIDTH,config.PARTITION_SECTION_HEIGHT=original
    (ROOT/'reports/partition_comparison.json').write_text(json.dumps(results,indent=2),encoding='utf8')
    print('PARTITION_COMPARISON_PASSED',results,flush=True)


if __name__=='__main__':run()
