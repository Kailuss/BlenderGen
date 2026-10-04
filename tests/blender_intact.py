"""Regresión del interruptor de daño y diez edificios intactos."""
import json
from pathlib import Path
import sys
import bpy
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
sys.path.insert(0,str(ROOT/'tests'))
from blender_probe import closure,digest
import ruinas_panel as addon
from ruinas_panel import runtime,meta
from ruinas_panel.services import cache
from ruinas_panel.structure.damage import DISABLED_VALUES


def run():
    """IA: diez semillas/calidades, conservación RNA, caché y reactivación reversible del daño."""
    addon.register();runtime.busy=True;runtime.preview=True
    results=[]
    for i in range(10):
        cache.clear_cache()
        p=bpy.context.scene.ruin_settings
        p.live_preview=False;p.batch_preview=False;p.use_instances=True
        p.layout_mode='ROOM';p.height_type='ONE';p.length=80;p.building_depth=70
        p.lock_distribution=False;p.seed=101+i;p.roof_frame=True;p.roof_tiles=True;p.windows_enabled=True
        p.chimneys=i%2==0;p.brass_pipes=True;p.damage_enabled=False
        p.collapse=.8;p.roof_damage=.6;p.floor_damage=.7;p.wood_damage=.8
        p.hole_count=3;p.wear_level='CUSTOM';p.wear=.8;p.cracks=.8
        quality=('DRAFT','WORK','DETAIL')[i%3]
        saved={k:getattr(p,k) for k in DISABLED_VALUES}
        coll=addon.generate(bpy.context,p,quality)
        first=digest(coll);sealed=closure(coll)
        assert not sealed['open_edges'],sealed
        assert all(getattr(p,k)==v for k,v in saved.items()),'ajustes borrados'
        assert not meta.get(bpy.context.scene,'huecos_generados',[])
        metrics=meta.get(bpy.context.scene,'ruinas_metricas')
        coll=addon.generate(bpy.context,p,quality)
        assert meta.get(bpy.context.scene,'ruinas_metricas')['cached']
        assert digest(coll)==first
        results.append({'seed':p.seed,'quality':quality,'closure':sealed,'metrics':metrics})
        print('INTACT_CASE',i,flush=True)
    p.damage_enabled=True
    coll=addon.generate(bpy.context,p,quality)
    assert not meta.get(bpy.context.scene,'ruinas_metricas')['cached']
    assert digest(coll)!=first,'reactivar no cambia geometría'
    p.damage_enabled=False
    coll=addon.generate(bpy.context,p,quality)
    assert digest(coll)==first,'apagar otra vez debe restaurar geometría'
    scene=bpy.context.scene
    bpy.ops.object.camera_add(location=(170,-220,180))
    camera=bpy.context.object;camera.rotation_euler=(Vector((0,30,30))-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.type='ORTHO';camera.data.ortho_scale=180;scene.camera=camera
    scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL'
    scene.display.shading.show_cavity=True;scene.render.resolution_x=1000;scene.render.resolution_y=850;scene.render.resolution_percentage=100
    scene.render.filepath=str(ROOT/'reports/intact_buildings.png');bpy.ops.render.render(write_still=True)
    (ROOT/'reports/intact_buildings.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    print('INTACT_PASSED',flush=True)


if __name__=='__main__':run()
