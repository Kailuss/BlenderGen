"""Comprueba la entrega reabierta y sus dependencias locales."""
import sys,json,hashlib
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1]


def run():
    'IA: Verifica reproducción, luces, cámaras, GPU, vídeo, duración y cachés de humo presentes; no recalcula ni renderiza.'
    scene=bpy.context.scene
    assert scene.get('physics_result_scene'),scene.name
    assert scene.frame_end==241 and scene.render.fps==24
    assert scene.render.engine=='CYCLES' and scene.cycles.device=='GPU'
    assert scene.cycles.samples==1024 and scene.render.use_motion_blur
    assert scene.render.resolution_x==1920 and scene.render.resolution_y==1080
    assert scene.render.image_settings.file_format=='FFMPEG' and scene.render.ffmpeg.codec=='H264'
    cameras=[o for o in scene.objects if o.type=='CAMERA']
    lights=[o for o in scene.objects if o.type=='LIGHT']
    assert len(cameras)>=3 and scene.camera in cameras
    assert {'SUN','AREA','SPOT'}.issubset({o.data.type for o in lights})
    assert {'SUN','AREA','SPOT'}.issubset({o.data.type for o in lights if o.data.energy>0 and not o.hide_render})
    assert scene.camera.data.dof.use_dof and scene.camera.data.dof.focus_object
    assert any(o.get('lab_chandelier') for o in scene.objects)
    for ob in scene.objects:
        if ob.get('lab_chandelier'):
            assert ob.parent and (ob.matrix_world.translation-ob.parent.matrix_world@ob.location).length<1e-6,ob.name
    domains=[m.domain_settings for o in scene.objects for m in o.modifiers if m.type=='FLUID' and m.fluid_type=='DOMAIN']
    assert len(domains)==1
    domain=domains[0];assert domain.has_cache_baked_data and domain.has_cache_baked_noise
    cache=Path(bpy.path.abspath(domain.cache_directory))
    assert cache.exists() and any(cache.rglob('*.vdb')),str(cache)
    for frame in range(1,242):
        assert (cache/'data'/f'fluid_data_{frame:04d}.vdb').is_file(),('data',frame)
        assert (cache/'noise'/f'fluid_noise_{frame:04d}.vdb').is_file(),('noise',frame)
    report=dict(scene=scene.name,cameras=[o.name for o in cameras],lights=[dict(name=o.name,type=o.data.type,energy=o.data.energy) for o in lights],frames=241,fps=24,cache=str(cache),cache_files=sum(1 for p in cache.rglob('*') if p.is_file()),samples=scene.cycles.samples)
    with open(bpy.data.filepath,'rb') as stream:
        report['blend_sha256']=hashlib.file_digest(stream,'sha256').hexdigest()
    (ROOT/'reports/ejercicio02_delivery_verified.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print('DELIVERY_VERIFIED',report,flush=True)


if __name__=='__main__':run()
