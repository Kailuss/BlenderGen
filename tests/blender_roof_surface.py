"""Mide curva, espesor, cierre y coste del tejado con render del hastial y los aleros."""
import importlib.util
import json
from pathlib import Path
import sys
import time
from types import SimpleNamespace

import bpy
import bmesh
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from ruinas_panel import runtime
from ruinas_panel.geometry import primitives
from ruinas_panel.structure import roof


def closure(coll):
    'IA: Exige caras no degeneradas, aristas manifold y volumen positivo en todos los componentes visibles del tejado.'
    for ob in coll.objects:
        bm=bmesh.new();bm.from_mesh(ob.data)
        assert all(e.is_manifold for e in bm.edges),ob.name
        assert all(f.calc_area()>1e-8 for f in bm.faces),ob.name
        assert bm.calc_volume()>0,ob.name
        bm.free()


def render(scene,path):
    'IA: Guarda una vista idéntica de cubierta, medias cañas y hastial en antes/después; el cierre se comprueba aparte.'
    bpy.ops.object.camera_add(location=(135,-180,133))
    camera=bpy.context.object
    camera.rotation_euler=(Vector((0,17,78))-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.type='ORTHO';camera.data.ortho_scale=151;scene.camera=camera
    scene.render.engine='BLENDER_WORKBENCH'
    scene.display.shading.light='STUDIO';scene.display.shading.studiolight_rotate_z=.5
    scene.display.shading.color_type='MATERIAL';scene.display.shading.show_shadows=True
    scene.display.shading.show_cavity=True;scene.display.shading.cavity_type='BOTH'
    scene.render.resolution_x=1400;scene.render.resolution_y=1100;scene.render.resolution_percentage=100
    scene.render.filepath=str(path)
    bpy.ops.render.render(write_still=True)


def run():
    'IA: Compara geometría con iguales dimensiones/semilla/calidad; valida también paños estrechos, daño, curva extrema y reserva de chimenea.'
    global roof
    label='after'
    if '--baseline' in sys.argv:
        label='before'
        source=sys.argv[sys.argv.index('--baseline')+1]
        spec=importlib.util.spec_from_file_location('ruinas_panel.structure.roof_baseline',source)
        roof=importlib.util.module_from_spec(spec);spec.loader.exec_module(roof)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    runtime.quality='WORK';runtime.preview=False
    p=SimpleNamespace(height=57,thickness=9,seed=17,roof_curve=.6,wood_damage=.35,wood_grain=.7,wear=.55)
    runtime.settings=p
    coll=bpy.data.collections.new('Tejado');scene=bpy.context.scene;scene.collection.children.link(coll)
    clay=primitives.material('Tejas · arcilla',(.40,.20,.115));wood=primitives.material('Madera · cubierta',(.31,.22,.13))
    started=time.perf_counter();tiles=0
    for edge in (-55,55):
        tiles+=roof.tile_bay(coll,clay,p,edge,0,-4,44,59.2,52,13,9301)
        roof.curved_rafter(coll,wood,p,edge,0,-4,59.2,52,8300)
        roof.curved_rafter(coll,wood,p,edge,0,0,59.2,52,8301)
        roof.curved_rafter(coll,wood,p,edge,0,44,59.2,52,8302)
    tiles+=roof.ridge_cap(coll,clay,0,-4,44,111.2)
    gable=roof.gable(coll,p,wood,-55,55,0,0,59.2,52,0)
    from ruinas_panel.geometry import timber
    timber.timber_beam(coll,wood,'Madera · cercha cubierta',(-51,0,57.4),(51,0,57.4),3.6,3.6,8150)
    timber.timber_beam(coll,wood,'Madera · cercha cubierta',(0,0,57.4),(0,0,111.2),2.8,2.8,8151)
    seconds=time.perf_counter()-started;closure(coll)
    rows=dict(label=label,seconds=seconds,faces=sum(len(o.data.polygons) for o in coll.objects),tiles=tiles,objects=len(coll.objects))
    if label=='after':
        assert gable['gable_depth_mm']>=3.2
        assert sum(bool(o.get('roof_gable_frame')) for o in coll.objects)>=4
        for ob in coll.objects:
            if ob.get('roof_tiles'):
                assert ob['tile_profile']=='half_round'
                # La sección inicial debe tener corona >1 mm sobre sus labios.
                zs=[v.co.z for v in ob.data.vertices[:9]]
                assert max(zs)-min(zs)>1,(ob.name,zs)
    out=ROOT/'reports';out.mkdir(exist_ok=True)
    render(scene,out/('roof_'+label+'.png'))
    bpy.ops.wm.save_as_mainfile(filepath=str(out/('roof_'+label+'.blend')))
    stress=bpy.data.collections.new('Casos límite');scene.collection.children.link(stress)
    for curve in (0,1):
        p.roof_curve=curve
        for edge in (-31,31):
            roof.tile_bay(stress,clay,p,edge,0,0,4,59.2,33,8,9011,
                          patches=[dict(x=edge*.4,y=1,rx=5,ry=3)],chimney=dict(x=edge*.6,y=2,radius=3))
    if label=='after':
        chimney=dict(x=18,y=1,radius=8)
        assert roof.roof_segments(-40,40,8,(),'x',chimney)==[(-40,8),(28,40)]
        for index in (0,4):
            ob=roof.gable(stress,p,wood,-55,55,0,0,59.2,52,index,chimney)
            for face in ob.data.polygons:
                xs=[ob.data.vertices[i].co.x for i in face.vertices]
                assert max(xs)<=9.651 or min(xs)>=26.349,(ob.name,xs)
    closure(stress)
    (out/('roof_'+label+'.json')).write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')
    print('ROOF_SURFACE_PASSED',json.dumps(rows),flush=True)


if __name__=='__main__':run()
