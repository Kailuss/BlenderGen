"""Genera instrucciones a partir de las comprobaciones terminadas."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'dist/Ejercicio02_metralla_20261028'


def run():
    'IA: Escribe instrucciones de render y alcance tras existir los informes de auditoría física y reapertura.'
    audit=json.loads((ROOT/'reports/ejercicio02_physics_audit.json').read_text(encoding='utf8'))
    verified=json.loads((ROOT/'reports/ejercicio02_delivery_verified.json').read_text(encoding='utf8'))
    impact=json.loads((OUT/'impactos.json').read_text(encoding='utf8'))
    retained=100*audit['roof_retained']/audit['roof_total']
    text=f'''# Ejercicio 02 · Tres impactos

Abre **05_render_listo.blend** en Blender 5.2 LTS. La escena activa contiene la reproducción calculada, materiales, luces y humo horneado. No necesita el complemento para reproducirla.

## Renderizar

- **Render_GPU.cmd** renderiza el vídeo con OptiX en la RTX 3090 Ti, sin modificar las preferencias globales de Blender.
- Salida: **render/Ejercicio02.mp4**. Blender puede añadir el intervalo de fotogramas al nombre.
- Desde Blender: F12 para una imagen; Ctrl+F12 para la animación. El lanzador configura automáticamente el dispositivo GPU.
- 1920 × 1080, 24 fps, fotogramas 1–241 (aproximadamente diez segundos), Cycles GPU, 1024 muestras adaptativas como máximo, denoising, motion blur y profundidad de campo. Cáusticas desactivadas.
- Hay cámaras estática, orbital e interior. Puedes cambiar la cámara activa y guardar antes de ejecutar el lanzador.

**Conserva la carpeta cache junto al blend.** El humo está en archivos OpenVDB externos. Para trasladar la entrega, copia el blend, cache, Render_GPU.cmd y Render_GPU.py juntos. Los archivos 01–04 son etapas de trabajo.

## Comprobaciones

- {len(impact['released_bodies'])} piezas liberables alrededor de tres trayectorias.
- Movimiento previo al impacto: {audit['preimpact_max_mm']:.4f} mm. Las piezas se retienen cinemáticamente hasta el contacto; no es una prueba de estabilidad libre.
- {retained:.1f} % de las tejas de la cubierta principal conserva su posición dentro de 5 mm y su orientación dentro de 15° al finalizar.
- {len(verified['cameras'])} cámaras, {len(verified['lights'])} luces y {verified['cache_files']} archivos de caché verificados al reabrir.

## Alcance

{impact['limits']} Las mallas visibles se conservan. Las lámparas tienen balanceo decorativo, no cadenas físicas. El polvo Mantaflow usa emisores temporizados y obstáculos aproximados; no ejerce presión sobre la estructura ni procede aún de eventos causales JOINT_BREAK. El microrelieve de materiales es visual y no se imprime.

La hoja de ruta recibida el 30 de octubre de 2026 guía el desarrollo posterior; este ejercicio no acredita el cierre de B1 ni la calibración mecánica del catálogo.
'''
    (OUT/'LEEME.md').write_text(text,encoding='utf8')
    print('DELIVERY_README_WRITTEN',flush=True)


if __name__=='__main__':run()
