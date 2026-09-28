"""Integra y representa la casa aportada, sin ejecutar código embebido en el blend."""
import json
from pathlib import Path
import sys
import time
import bpy
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
sys.path.insert(0,str(ROOT/'tests'))


def render(scene,name):
    """IA: misma cámara de la entrega para exterior; guarda PNG de inspección sin cambiar materiales ni geometría."""
    scene.render.engine='BLENDER_WORKBENCH'
    scene.display.shading.light='STUDIO'
    scene.display.shading.color_type='MATERIAL'
    scene.display.shading.show_shadows=True
    scene.display.shading.show_cavity=True
    scene.display.shading.cavity_type='BOTH'
    scene.render.resolution_x=1400;scene.render.resolution_y=1100;scene.render.resolution_percentage=100
    scene.render.filepath=str(ROOT/'reports'/name)
    bpy.ops.render.render(write_still=True)


def run():
    """IA: reproduce ajustes del usuario; exige hogar bajo, hueco frontal y conducto libre, cierre, caché y conserva blend original."""
    from ruinas_panel import config,meta,runtime
    import ruinas_panel as addon
    from ruinas_panel.geometry import primitives
    from blender_probe import closure,digest
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'dist/reference_v031/ruina_v031.blend'),use_scripts=False)
    addon.register();runtime.busy=True;runtime.preview=True
    p=bpy.context.scene.ruin_settings
    p.batch_preview=False
    scene=bpy.context.scene
    started=time.perf_counter();coll=addon.generate(bpy.context,p,'DETAIL')
    plan=meta.get(scene,'chimeneas_generadas',[])
    assert plan, 'No se encontró emplazamiento de chimenea'
    plan=plan[0]
    assert plan['bottom']<plan['floor'] and plan['hood_top']<config.UPPER_FLOOR
    objects=[ob for ob in coll.objects if ob.get('chimney')]
    verts=[];faces=[]
    for ob in objects:
        offset=len(verts);verts.extend(tuple(v.co) for v in ob.data.vertices)
        ob.data.calc_loop_triangles();faces.extend(tuple(i+offset for i in t.vertices) for t in ob.data.loop_triangles)
        bm=bmesh.new();bm.from_mesh(ob.data)
        assert all(e.is_manifold for e in bm.edges),ob.name
        assert not any(f.calc_area()<1e-8 for f in bm.faces),ob.name
        assert bm.calc_volume()>0,ob.name
        bm.free()
    tree=BVHTree.FromPolygons(verts,faces,all_triangles=True)
    x,y=plan['x'],plan['y'];nx,ny=plan['normal']
    # La boca no tiene una placa tapándola y el eje vertical deja pasar humo hasta el cielo.
    opening=Vector((x+nx*(plan['half_depth']+3),y+ny*(plan['half_depth']+3),(plan['floor']+plan['mouth_top'])/2))
    hit=tree.ray_cast(opening,Vector((-nx,-ny,0)),plan['half_depth']*2+6)
    assert hit[0] and hit[3]>plan['half_depth']+3,('boca_obstruida',hit)
    assert tree.ray_cast(Vector((x,y,plan['mouth_top'])),Vector((0,0,1)),plan['top']+10)[0] is None,'conducto_obstruido'
    bpy.context.view_layer.update()
    for ob in coll.objects:
        if ob.get('chimney') or not (ob.get('madera') or ob.get('wood_floor') or ob.get('roof_tiles')):continue
        hit=ob.ray_cast(Vector((x,y,plan['mouth_top'])),Vector((0,0,1)),distance=plan['top']+10)
        assert not hit[0],('estructura_cruza_conducto',ob.name)
    sealed=closure(coll)
    assert not sealed['open_edges'],sealed['open_edges']
    first=digest(coll)
    addon.generate(bpy.context,p,'DETAIL')
    assert meta.get(scene,'ruinas_metricas')['cached'] and digest(bpy.data.collections[config.COLLECTION])==first
    coll=bpy.data.collections[config.COLLECTION]
    camera=scene.camera;old_matrix=camera.matrix_world.copy();old_scale=camera.data.ortho_scale
    hidden={ob:ob.hide_render for ob in coll.objects}
    for ob in coll.objects:ob.hide_render=not ob.get('chimney')
    focus=Vector((x,y,plan['mouth_top']*.65))
    camera.location=focus+Vector((nx*55+ny*32,ny*55-nx*32,32))
    camera.rotation_euler=(focus-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=65
    # Ocultar la parte alta para inspeccionar el hogar y su campana.
    for ob in coll.objects:
        if ob.get('chimney') and min(v.co.z for v in ob.data.vertices)>plan['hood_top']+5:ob.hide_render=True
    render(scene,'house_fireplace.png')
    for ob,value in hidden.items():ob.hide_render=value
    camera.matrix_world=old_matrix;camera.data.ortho_scale=old_scale
    p.batch_preview=True
    coll=addon.generate(bpy.context,p,'DETAIL')
    metrics=meta.get(scene,'ruinas_metricas')
    render(scene,'house_after.png')
    # La copia revisada usa el addon instalado, nunca el activador de la versión adjunta.
    for block in list(bpy.data.texts):
        if block.name.endswith('.py'):bpy.data.texts.remove(block)
    text=bpy.data.texts.new('LEEME_RUINAS')
    text.write('Casa 0.31 revisada. Instala ruinas_panel_v031.zip para regenerar. Fuente única: src/ruinas_panel/.')
    p.live_preview=False
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'dist/ruina_v031_revisada.blend'))
    result={'settings':{k:getattr(p,k) for k in config.FIELDS},'chimney':plan,'closure':sealed,
            'metrics':metrics,'elapsed_seconds':time.perf_counter()-started,'cache_identical':True,'wood_passage_clear':True}
    (ROOT/'reports/house_revision.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('HOUSE_REVISION_PASSED',flush=True)


if __name__=='__main__':run()
