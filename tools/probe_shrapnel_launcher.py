"""Prueba de vídeo del lanzador real, sin cambiar el archivo entregado."""
import sys,json
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import render_shrapnel_gpu


def run():
    'IA: Renderiza dos fotogramas de humo por el lanzador OptiX real, con muestreo reducido solo en memoria; verifica el vídeo decodificado sin guardar ajustes sobre la entrega.'
    scene=bpy.context.scene;scene.frame_start=135;scene.frame_end=136
    scene.cycles.samples=16;scene.cycles.adaptive_min_samples=8
    scene.render.resolution_percentage=50
    scene.render.filepath=str(ROOT/'reports/ejercicio02_launcher_probe.mp4')
    render_shrapnel_gpu.run()
    paths=list((ROOT/'reports').glob('ejercicio02_launcher_probe*.mp4'))
    assert paths
    video=max(paths,key=lambda p:p.stat().st_mtime)
    clip=bpy.data.movieclips.load(str(video))
    assert clip.frame_duration==2 and tuple(clip.size)==(960,540),(clip.frame_duration,tuple(clip.size))
    report=dict(video=str(video),frames=clip.frame_duration,size=list(clip.size),bytes=video.stat().st_size)
    (ROOT/'reports/ejercicio02_launcher_verified.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print('LAUNCHER_VIDEO_VERIFIED',report,flush=True)


if __name__=='__main__':run()
