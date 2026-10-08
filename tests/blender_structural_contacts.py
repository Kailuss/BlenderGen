"""Encaje de viga y pérdida de unión sin desplazar manualmente cuerpos."""
import sys,json
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'tests'))
import ruinas_panel as addon
from ruinas_panel import config,runtime
from ruinas_panel.geometry import primitives,batching
from ruinas_panel.services import structural_physics as structural,physics
from blender_probe import digest


def run():
    'IA: Recorta una viga que cruza piedra, conserva el hueco, elimina mortero y prueba caída tras desconectar una tabla colgada; compara fuente agrupada e individual.'
    bpy.ops.wm.read_factory_settings(use_empty=True);addon.register();runtime.busy=True;runtime.preview=True;runtime.instance_build=True
    source=bpy.context.scene;p=source.ruin_settings;p.live_preview=False;p.physics_strength=1000
    for key,value in [('PARTITION',0),('ROOM1',1),('ROOM2',2),('ROOM3',3),('BUILDING',4)]:
        p.physics_target=key;assert p['physics_target']==value
    coll=bpy.data.collections.new(config.COLLECTION);source.collection.children.link(coll)
    stone=primitives.material('Piedra',(.5,.5,.5));wood=primitives.material('Madera',(.4,.2,.1))
    for name,box,mat in [('Tierra',(-10,35,-10,10,-2,0),stone),('Pie',(0,8,-3,3,0,3),stone),('Piedra soporte',(0,8,-3,3,3,15),stone),('Madera viga',(4,26,-2,2,12,15),wood),('Madera tabla colgada',(22,24,-1,1,7,12),wood),('Mortero',(1,7,-2,2,2,14),stone)]:
        primitives.block(name,*box,coll,mat)
    initial=digest(coll);lab=structural.prepare(source);assert digest(coll)==initial
    report=json.loads(lab['preparation_report']);assert report['binder_excluded']==1 and report['joints_cut']>=1
    support=next(o for o in lab.objects if o.get('source_piece')=='Piedra soporte')
    assert abs(support['physical_volume_mm3']-(8*6*12-4*4*3))<.01
    bpy.context.window.scene=lab
    plank=next(o for o in lab.objects if o.get('source_piece')=='Madera tabla colgada')
    beam=next(o for o in lab.objects if o.get('source_piece')=='Madera viga')
    structural.release(lab,[beam,plank]);assert not plank.animation_data
    animated=[o for o in lab.objects if o.animation_data]
    assert len(animated)==2 and animated[0].animation_data.action==animated[1].animation_data.action
    positions=[]
    for frame in range(1,121):
        lab.frame_set(frame);positions.append(plank.evaluated_get(bpy.context.evaluated_depsgraph_get()).matrix_world.translation.copy())
    assert (positions[11]-positions[0]).length<.0002,positions[:12]
    assert positions[0].z-positions[-1].z>.005,positions[-1]
    assert positions[-1].z>.002,'fell through ground'
    bpy.context.window.scene=source;batching.pack_preview(coll)
    grouped=structural.prepare(source);grouped_report=json.loads(grouped['preparation_report'])
    assert grouped_report['bodies']==report['bodies'] and grouped_report['constraints']==report['constraints']
    print('STRUCTURAL_CONTACTS_PASSED',report,'drop_mm',(positions[0].z-positions[-1].z)*1000,flush=True)


if __name__=='__main__':run()
