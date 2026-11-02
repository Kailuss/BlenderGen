# Ejercicio 02 — entrega de render, 2026-11-02

Archivo: `dist/Ejercicio02_metralla_20261028/05_render_listo.blend`.
Lanzador: `Render_GPU.cmd`, en esa misma carpeta. Selecciona OptiX en la RTX 3090 Ti y genera `render/Ejercicio02.mp4`. Comprueba la presencia de las cachés y crea la carpeta de salida. No cambia preferencias globales.
Paquete: `dist/Ejercicio02_metralla_entrega_20261102.zip`, con cachés relativas, instrucciones, vista previa y manifiesto SHA-256.

## Validación realizada

- Física completa: 241 poses a 24 fps, diez segundos físicos. 1.952 piezas liberables, 1.896 objetos con movimiento en el informe del trabajador. Cálculo de 15.260 s y pico de 3.993 MiB.
- Sin movimiento antes de los impactos por retención cinemática programada. No representa una prueba de estabilidad estructural libre.
- Daño en todas las regiones de altura, incluidos 46 bloques identificados como cimientos. Se conserva el 88,9 % de las tejas principales dentro de 5 mm y 15 grados de su pose inicial. Error máximo de escala 0,000001354.
- Mantaflow GAS: resolución 128, ruido ×2, nueve fuentes temporizadas, 32 obstáculos de caja. Horneado completo de datos y ruido: 723 archivos, unos 7,06 GB. Duración del horneado: 6.581 s.
- Reapertura del archivo final: tres cámaras, nueve luces (sol, área, spot y seis luces de vela), DOF, motion blur, Cycles GPU y H.264. Se comprueban todos los fotogramas de las cachés y el hash del blend antes de empaquetar.
- Render visual del fotograma 135 con humo y materiales. Corregido en la entrega el doble desplazamiento de las lámparas, reanclándolas en coordenadas locales de sus vigas. Ajustada la densidad óptica del humo y el encuadre de la cámara a 38 mm; no se recalcularon ni alteraron las físicas o el campo de gas.
- Lanzador real probado en OptiX: vídeo de dos fotogramas, decodificado a 960 × 540. La reducción fue solo en memoria; el archivo final conserva 1920 × 1080 y hasta 1.024 muestras adaptativas.

## Límites

Es una puesta en escena dirigida, con cuerpos externos a los corredores pasivos y proyectiles guiados. No acredita calibración mecánica del catálogo ni cierre del plan constructivo B1. Las lámparas tienen balanceo decorativo, no cadenas físicas. El gas sigue obstáculos animados pero no aplica presión a los cuerpos. El microrelieve de materiales es visual, no imprimible.

La corrección general del traslado del anclaje de lámparas al duplicar escenas queda pendiente en el complemento; esta entrega contiene el anclaje corregido y verificado. El suelo finito sí quedó corregido de forma general en 0.32.26.

El supervisor de este ejercicio admite seis horas de física y mantiene el máximo de 10 GiB. El intento anterior fue interrumpido a las dos horas, no por memoria. `tools/run_shrapnel_delivery.ps1` reproduce la secuencia desde el laboratorio preparado, incluida la corrección final de presentación. No se ha ejecutado el vídeo completo: queda listo para el usuario.
