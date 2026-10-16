"""Cierre, caché y laboratorio de la terraza almenada."""
import sys,json
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'tests'))
import ruinas_panel as addon
from ruinas_panel import runtime,meta
from ruinas_panel.services import structural_physics
from blender_probe import digest,closure
from blender_v032 import render


def run():
    'IA: Genera torreón pequeño reproducible, comprueba cierre y caché, prepara laboratorio y entrega fuente editable junto a copias físicas.'
    bpy.ops.wm.read_factory_settings(use_empty=True);addon.register();runtime.busy=True;runtime.preview=True
    scene=bpy.context.scene;p=scene.ruin_settings;p.live_preview=False
    for key,value in dict(length=80,building_depth=80,height_type='TWO',layout_mode='ROOM',pillar_count=0,door_enabled=True,windows_enabled=False,roof_frame=True,roof_type='TOWER',ground_floor=True,upper_floor=True,stair_type='NONE',collapse=0,hole_count=0,cracks=0,rubble_amount=0,ground_roughness=0,batch_preview=True).items():setattr(p,key,value)
    coll=addon.generate(bpy.context,p,'WORK');assert not closure(coll)['open_edges']
    first=digest(coll);coll=addon.generate(bpy.context,p,'WORK');assert digest(coll)==first
    report=meta.get(scene,'cubierta_detalles');assert report['profile']=='tower' and report['parapet_blocks']>0
    render(scene,ROOT/'reports/tower_roof.png',focus=(0,35,70),location=(190,-210,210),scale=230)
    lab=structural_physics.prepare(scene);report['preparation']=json.loads(lab['preparation_report'])
    # Las piezas del laboratorio están en metros: validar con el umbral de volumen propio de la auditoría, no el umbral en mm³ de preparación.
    for ob in lab.objects:
        if ob.type=='MESH':
            import bmesh
            bm=bmesh.new();bm.from_mesh(ob.data)
            assert all(e.is_manifold for e in bm.edges) and bm.calc_volume()>0,ob.name
            bm.free()
    scene.name='01 · Torreón editable';lab.name='02 · Laboratorio torreón';bpy.context.window.scene=scene
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'dist/ruinas_v03212_torreon_prueba.blend'))
    (ROOT/'reports/tower_roof.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print('TOWER_ROOF_PASSED',report,flush=True)


if __name__=='__main__':run()
