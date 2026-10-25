"""Inventario de archivos fallidos sin regenerar ni ejecutar scripts embebidos."""
import json
import sys
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import ruinas_panel as addon
from ruinas_panel import runtime


def run():
    'IA: Lee una reproducción en proceso aislado y registra escenas, complejidad, ajustes y equipo de render sin modificar el archivo.'
    addon.register();runtime.busy=True
    path=Path(sys.argv[sys.argv.index('--')+1]);bpy.ops.wm.open_mainfile(filepath=str(path))
    report={'file':str(path),'bytes':path.stat().st_size,'scenes':[]}
    for scene in bpy.data.scenes:
        meshes={o.data for o in scene.objects if o.type=='MESH'}
        settings={}
        for key in ('quality','export_quality','physics_target','physics_frames','physics_memory_mb','physics_precision','physics_fragile_size','seed','height','length','depth','stairs_enabled','stairs_material','roof_enabled'):
            if hasattr(scene.ruin_settings,key):settings[key]=getattr(scene.ruin_settings,key)
        report['scenes'].append({'name':scene.name,'lab':bool(scene.get('ruinas_physics_lab')),'replay':bool(scene.get('ruinas_replay')),'objects':len(scene.objects),'unique_mesh_faces':sum(len(m.polygons) for m in meshes),'largest_mesh_faces':max((len(m.polygons) for m in meshes),default=0),'lights':[{'name':o.name,'kind':o.data.type,'energy':o.data.energy,'hidden':o.hide_render} for o in scene.objects if o.type=='LIGHT'],'cameras':[{'name':o.name,'dof':o.data.dof.use_dof} for o in scene.objects if o.type=='CAMERA'],'engine':scene.render.engine,'output':scene.render.image_settings.file_format,'settings':settings})
    target=ROOT/'reports'/('inventory_'+path.stem+'.json');target.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print('FAILURE_INVENTORY',json.dumps(report,ensure_ascii=False),flush=True)


if __name__=='__main__':run()
