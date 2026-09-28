"""Relieve físico de losas: estabilidad jugable, semillas, cierre y unión con el macizo."""
import json
from pathlib import Path
import sys
import time

import bpy
import bmesh
import numpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import ruinas_panel as addon
from ruinas_panel import runtime,config
from ruinas_panel.geometry import primitives
from ruinas_panel.services import export
from ruinas_panel.structure import stairs


def sealed(ob):
    'IA: Exige malla cerrada, caras con área y volumen positivo sin corregir la pieza.'
    bm=bmesh.new();bm.from_mesh(ob.data)
    assert all(e.is_manifold for e in bm.edges),ob.name
    assert all(f.calc_area()>1e-8 for f in bm.faces),ob.name
    assert bm.calc_volume()>0,ob.name
    bm.free()


def render(scene,target,center,location,scale):
    'IA: Renderiza geometría con material uniforme y luz rasante; no usa bump para aparentar relieve.'
    primitives.drop_stage();scene.view_layers[0].update()
    bpy.ops.object.camera_add(location=location)
    camera=bpy.context.object
    camera.rotation_euler=(Vector(center)-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.type='ORTHO';camera.data.ortho_scale=scale;scene.camera=camera
    scene.render.engine='BLENDER_WORKBENCH'
    scene.display.shading.light='STUDIO';scene.display.shading.studiolight_rotate_z=.65
    scene.display.shading.color_type='SINGLE';scene.display.shading.single_color=(.53,.49,.42)
    scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True
    scene.display.shading.cavity_type='BOTH'
    scene.display.shading.curvature_ridge_factor=1.5;scene.display.shading.curvature_valley_factor=1.5
    scene.render.resolution_x=1500;scene.render.resolution_y=850;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.filepath=str(target)
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(camera,do_unlink=True)


def run():
    'IA: Contrasta desgaste 0/0,55/1, ambos sentidos y fusión con macizo; registra tiempos, caras y vistas para QA.'
    bpy.ops.wm.read_factory_settings(use_empty=True)
    addon.register();runtime.busy=True;runtime.preview=False
    scene=bpy.context.scene;p=scene.ruin_settings;runtime.settings=p
    coll=bpy.data.collections.new('Escalera · prueba');scene.collection.children.link(coll)
    stone=primitives.material('Piedra · prueba',(.52,.52,.52))
    rows=[]
    for quality in ('DRAFT','WORK','DETAIL'):
        runtime.quality=quality
        for seed in (17,43,91):
            previous=None
            for amount in (0,.55,1):
                start=time.perf_counter()
                ob=stairs.stone_tread(coll,stone,'Escalera · losa prueba',0,22.4,0,22.8,10,amount,seed)
                elapsed=time.perf_counter()-start;sealed(ob)
                co=primitives.coords(ob);surface=co[co[:,2]>9.2]
                assert surface[:,2].min()>=9.47999, 'el macizo tapa el relieve'
                center=surface[(abs(surface[:,0]-11.2)<=10.00001)&(abs(surface[:,1]-11.4)<=10.00001)]
                variation=float(numpy.ptp(center[:,2]));assert variation<=.24001,(quality,amount,variation)
                assert numpy.ptp(center[:,0])>=19.999 and numpy.ptp(center[:,1])>=19.999
                assert len(co)<config.DETAIL_VERTEX_LIMIT
                volume=primitives.mesh_volume(ob.data)
                if previous is not None:
                    assert volume<previous if quality=='DETAIL' else abs(volume-previous)<1e-6
                previous=volume
                twin=stairs.stone_tread(coll,stone,'Escalera · losa gemela',0,22.4,0,22.8,10,amount,seed)
                assert numpy.array_equal(co,primitives.coords(twin))
                rows.append(dict(quality=quality,seed=seed,wear=amount,faces=len(ob.data.polygons),
                                 seconds=elapsed,volume=volume,center_variation_mm=variation,
                                 relief_mm=float(ob['stair_relief_mm'])))
                primitives.remove_objects((ob,twin))
    runtime.quality='DETAIL'
    # Igual encuadre y material: izquierda losa lisa original, derecha nueva al máximo.
    start=time.perf_counter()
    before=primitives.block('Antes · losa lisa',0,22.4,0,22.8,9.5,10.1,coll,stone)
    sealed(before)
    assert not before.hide_render and not before.hide_get()
    rows.append(dict(baseline='losa lisa original',faces=len(before.data.polygons),seconds=time.perf_counter()-start))
    stairs.stone_tread(coll,stone,'Después · losa tallada',29,51.4,0,22.8,10,1,43)
    render(scene,ROOT/'reports/stairs_surface_comparison.png',(26,11,10),(55,-75,76),64)
    primitives.remove_objects(list(coll.objects))
    p.stair_type='STONE';p.height_type='TWO';p.upper_floor=True;p.floor_beams=True;p.ground_floor=True
    p.wear=.7;p.stone_size=6.25;p.wood_damage=0
    for side in ('RIGHT','LEFT'):
        p.stair_side=side
        s=stairs.plan(p,(0,135,0,55));assert s and 'error' not in s
        assert s['approach_mm']==35 and s['usable_tread_mm']==20
        start=time.perf_counter();stairs.build(coll,p,scene,s)
        treads=[o for o in coll.objects if o.get('stair_surface')]
        assert len(treads)==s['steps']
        for ob in coll.objects:sealed(ob)
        core=next(o for o in coll.objects if primitives.piece_key(o)=='Escalera · macizo piedra')
        fused=core.copy();fused.data=core.data.copy();coll.objects.link(fused)
        for tread in treads:
            mod=fused.modifiers.new('Unión prueba','BOOLEAN');mod.operation='UNION'
            mod.solver='MANIFOLD';mod.object=tread
            primitives.apply_modifier(fused,mod,tread)
        sealed(fused)
        bm=bmesh.new();bm.from_mesh(fused.data);assert len(export.shells(bm))==1;bm.free()
        primitives.remove_objects((fused,))
        rows.append(dict(side=side,steps=len(treads),faces=sum(len(o.data.polygons) for o in coll.objects),
                         seconds=time.perf_counter()-start))
        if side=='RIGHT':
            render(scene,ROOT/'reports/stairs_surface_full.png',(82,40,29),(12,120,95),142)
        primitives.remove_objects(list(coll.objects))
    primitives.drop_stage();addon.unregister()
    (ROOT/'reports/stairs_surface.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')
    print('STAIRS_SURFACE_PASSED',flush=True)


if __name__=='__main__':run()
