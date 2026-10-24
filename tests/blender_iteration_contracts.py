"""Mesures réelles de malla, réserves et capture de la famille en cours."""
import sys,json,math,statistics
from pathlib import Path
import bpy,bmesh
from mathutils import Matrix,Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import ruinas_panel as addon
from ruinas_panel import runtime,meta
from ruinas_panel.construction_core import adapter,materials
from ruinas_panel.structure import building_definition


def run():
    'IA: Genera casa, mide una viga en dos representaciones escaladas y verifica caché de reserva; no equivale a validación Bullet.'
    addon.register();runtime.busy=True
    p=bpy.context.scene.ruin_settings;p.layout_mode='ROOM';p.height_type='THREE'
    p.length=190;p.building_depth=100;p.floor_beams=True;p.upper_floor=True;p.stair_type='WOOD';p.damage_enabled=False
    coll=addon.generate(bpy.context,p,'DRAFT')
    reservation=meta.get(bpy.context.scene,'construction_reservations');assert reservation['stairs']['1'] and reservation['stairs']['2']
    beam=next(o for o in coll.objects if o.name.startswith('Madera · viga de planta'))
    results=[]
    for scale in (30,60):
        bm=bmesh.new();bm.from_mesh(beam.data);bm.transform(beam.matrix_world);bm.transform(Matrix.Scale(60/scale,4))
        volume=abs(bm.calc_volume(signed=True));area=sum(f.calc_area() for f in bm.faces);bm.free()
        definition=building_definition.define(p,scale)
        element=adapter.measured_element('measured.beam','BEAM','TIMBER_SOFT',volume,area,definition)
        results.append({'scale':scale,'mass_kg':element['mass_kg'],'area_mm2':element['exposed_area_mm2'],'weight_per_surface_MPa':element['mass_kg']*9.81/element['exposed_area_mm2']})
    for key in ('mass_kg','area_mm2','weight_per_surface_MPa'):assert math.isclose(results[0][key],results[1][key],rel_tol=1e-6)
    meta.put(bpy.context.scene,'construction_reservations',{})
    coll=addon.generate(bpy.context,p,'DRAFT');assert meta.get(bpy.context.scene,'construction_reservations')==reservation
    values=[materials.variability(seed,'beam.test',.25) for seed in range(1000)]
    report={'scale_mesh_test':results,'scale_scope':'same generated mesh represented at two scales; not independently resized procedural parameters','reservation_cache':True,'variability':{'count':len(values),'mean':statistics.mean(values),'stdev':statistics.pstdev(values),'min':min(values),'max':max(values)},'acceptance':materials.acceptance('TIMBER_SOFT',['density_kg_m3','compression','bearing']),'materials_signature':materials.signature(),'bullet_tested':False}
    (ROOT/'reports/iteration_contracts.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    scene=bpy.context.scene
    camera=bpy.data.objects.new('Revisión constructiva',bpy.data.cameras.new('Revisión constructiva'));scene.collection.objects.link(camera)
    camera.location=(350,-400,350);target=Vector((0,40,85));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.type='ORTHO';camera.data.ortho_scale=300;camera.data.clip_end=2000;scene.camera=camera
    scene.render.engine='BLENDER_WORKBENCH';scene.render.resolution_x=800;scene.render.resolution_y=800;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.filepath=str(ROOT/'reports/iteration_reservations.png')
    bpy.ops.render.render(write_still=True)
    print('ITERATION_CONTRACTS_PASSED',flush=True)


if __name__=='__main__':run()
