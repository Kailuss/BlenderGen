"""Comparación controlada: fuente, desplazamiento de mortero y reparación local."""
import sys,json,time
from pathlib import Path
import bpy,bmesh
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'tests'))
import ruinas_panel as addon
from ruinas_panel import runtime
from ruinas_panel.geometry import primitives
from ruinas_panel.services import cache
from blender_probe import mesh_objects,digest


def count_bad(coll):
    'IA: Mide degeneración, cierre y cotas en piezas y variantes; no modifica la fuente.'
    bad={};opened={};bounds={}
    for ob in mesh_objects(coll):
        if ob.get('ruin_instances'):continue
        bm=bmesh.new();bm.from_mesh(ob.data)
        n=sum(f.calc_area()<1e-8 for f in bm.faces)
        if n:bad[ob.name]=n
        n=sum(not e.is_manifold for e in bm.edges)
        if n:opened[ob.name]=n
        bounds[ob.name]=[[fn(v.co[i] for v in bm.verts) for i in range(3)] for fn in (min,max)]
        bm.free()
    return {'degenerate':bad,'open':opened,'bounds':bounds}


def disabled_repair(ob):
    'IA: Referencia previa a la reparación; únicamente para comparación de esta prueba.'
    return False


def run():
    'IA: Compara igual semilla/calidad con desplazamiento del mortero de .01 mm frente a soldadura local; exige cierre y cotas conservadas.'
    bpy.ops.wm.read_factory_settings(use_empty=True);addon.register();runtime.busy=True;runtime.preview=False
    p=bpy.context.scene.ruin_settings;p.live_preview=False;p.batch_preview=False;p.use_instances=True
    p.layout_mode='ROOM';p.length=180;p.building_depth=90;p.height_type='TWO';p.seed=47;p.lock_distribution=False
    p.damage_enabled=False;p.floor_beams=True;p.windows_enabled=True;p.door_enabled=True
    repair=primitives.repair_precision;primitives.repair_precision=disabled_repair
    try:
        coll=addon.generate(bpy.context,p,'WORK');before=count_bad(coll)
        for ob in coll.objects:
            if ob.name.startswith(('Mortero','Núcleo')):
                for v in ob.data.vertices:v.co.x+=.01;v.co.y+=.01;v.co.z+=.01
        shifted=count_bad(coll)
    finally:primitives.repair_precision=repair
    cache.clear_cache();coll=addon.generate(bpy.context,p,'WORK');after=count_bad(coll)
    assert not after['open'] and not after['degenerate'],after
    delta=max(abs(v-after['bounds'][name][j][k]) for name,bound in before['bounds'].items() for j,row in enumerate(bound) for k,v in enumerate(row))
    assert delta<.00002,delta
    first=digest(coll);coll=addon.generate(bpy.context,p,'WORK');assert digest(coll)==first
    report={'baseline_degenerate':sum(before['degenerate'].values()),'mortar_shift_001_degenerate':sum(shifted['degenerate'].values()),'repaired_degenerate':sum(after['degenerate'].values()),'open_edges':after['open'],'max_bounds_delta_mm':delta,'baseline_objects':before['degenerate']}
    (ROOT/'reports/precision_comparison.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('PRECISION_COMPARISON_PASSED',report,flush=True)


if __name__=='__main__':run()
