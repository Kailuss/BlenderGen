"""Lanzador de render de la entrega; se ejecuta solo por decisión del usuario."""
import bpy
from pathlib import Path


def run():
    'IA: Selecciona la escena entregada y OptiX localmente, exige caché de humo horneada y renderiza vídeo sin modificar preferencias globales.'
    scene=next(s for s in bpy.data.scenes if s.get('physics_result_scene'))
    bpy.context.window.scene=scene
    pref=bpy.context.preferences.addons['cycles'].preferences
    pref.compute_device_type='OPTIX';pref.get_devices()
    enabled=[]
    for device in pref.devices:
        device.use=device.type=='OPTIX' and '3090' in device.name
        if device.use:enabled.append(device.name)
    if not enabled:raise RuntimeError('No se encuentra la RTX 3090 Ti mediante OptiX.')
    domains=[m.domain_settings for o in scene.objects for m in o.modifiers if m.type=='FLUID' and m.fluid_type=='DOMAIN']
    if not domains or not all(d.has_cache_baked_data and d.has_cache_baked_noise for d in domains):
        raise RuntimeError('Falta la caché completa del humo; conserva la carpeta cache junto al blend.')
    for domain in domains:
        cache=Path(bpy.path.abspath(domain.cache_directory))
        for frame in range(scene.frame_start,scene.frame_end+1):
            for kind in ('data','noise'):
                path=cache/kind/f'fluid_{kind}_{frame:04d}.vdb'
                if not path.is_file() or path.stat().st_size==0:raise RuntimeError('Falta un archivo de humo: '+str(path))
    Path(bpy.path.abspath(scene.render.filepath)).parent.mkdir(parents=True,exist_ok=True)
    scene.cycles.device='GPU'
    print('RENDER_GPU',enabled,scene.render.filepath,flush=True)
    bpy.ops.render.render(animation=True)


if __name__=='__main__':run()
