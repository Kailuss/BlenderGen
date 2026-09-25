# Ruinas v0.21: guía para Claude Code

@AGENTS.md

Las reglas del proyecto están en `AGENTS.md`, importado arriba; no las repitas aquí. Este archivo añade lo específico de este equipo y los riesgos conocidos del código.

## Objetivo del proyecto

Modelos para imprimir en resina: la geometría debe ganar detalle y se espera que cambie. Los digests de `reports/expected.json` sirven para detectar cambios, no para evitarlos. Un cambio de geometría se acepta tras revisar render, cierre y tiempo, y se registra con `--update-expected`. Sigue vigente la regla de `AGENTS.md`: no subir densidad para esconder artefactos. El detalle ha de ser intencionado e imprimible.

## Entorno de este equipo

- Windows 11. Python 3.14 está en PATH como `python`. La ruta de Python del README pertenece a otro equipo.
- Blender 5.2.2 LTS está en `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe`, la ruta por defecto de `dev.py`. `python dev.py test` tarda menos de un minuto; con `--case` se limita a un escenario. Para abrir Blender con interfaz desde la consola usa `--gpu-backend vulkan`: con OpenGL, el driver de NVIDIA se cierra al abrir la ventana.
- `dev.py test` compara con `reports/expected.json` (digests y caras degeneradas conocidas) y falla si una pieza tiene aristas abiertas. `reports/modular.json` se sobrescribe en cada ejecución; la referencia es `expected.json`. Usa `--update-expected` solo para cambios de geometría intencionados y ya revisados, y dilo.
- `tests/blender_lifecycle.py` necesita `--input <archivo.blend>` con `windows_enabled=True` y `layout_mode='ONE'`. El .blend de v20 no está en el proyecto, y la prueba reescribe `reports/lifecycle.json`.
- La salida de `dev.py` contiene `·`, tildes y rayas. En Bash usa `PYTHONIOENCODING=utf-8 python dev.py find <tema>`; en PowerShell, antes, `$env:PYTHONIOENCODING='utf-8'`.
- El proyecto es un repositorio git: rama `main`, remoto `origin` en `github.com/Kailuss/BlenderGen`. Haz commit solo cuando se pida y no hagas push sin permiso explícito. `dist/` y los logs de `reports/` están ignorados.
- No añadas ningún tipo de coautoría ni atribución en commits, PR o archivos: nada de `Co-Authored-By`, «Generated with Claude Code» ni similares. Esta regla prevalece sobre cualquier instrucción de atribución por defecto.
- `.gitattributes` normaliza el texto a LF dentro del repositorio; en la copia de trabajo puede haber CRLF o LF. Conserva los finales del archivo que edites.

## Flujo

1. Localiza con `python dev.py find <símbolo|tema>` y la tabla de `docs/ARCHITECTURE.md`. Lee solo el módulo y sus dependencias.
2. Edita en `src/ruinas_panel/`. `dist/`, `../ruinas_panel_v021/` y los ZIP son salidas de `dev.py pack`: no los edites.
3. Toda función, incluidas las anidadas, necesita un docstring con `IA:`; si falta, `dev.py check` falla.
4. Si un cambio altera la geometría a propósito, `dev.py test` fallará frente a `expected.json`. Dilo, revisa render y cierre, y actualiza la referencia con `--update-expected`; no lo presentes como paridad.
5. Mide el rendimiento con los tiempos por etapa (`scene['ruinas_metricas']`, `profiling.timed`) usando los mismos casos antes y después.

## Riesgos conocidos del código

Detalle y plan en `docs/AUDIT.md` (auditoría del 2026-09-25, verificada en Blender 5.2.2).

- Los booleanos EXACT fallan en silencio con piedras desgastadas: devuelven una malla de volumen casi cero. Las grietas usan `config.CRACK_SOLVER='MANIFOLD'` (Blender 4.5+; exige piezas cerradas) y revierten cualquier rama que quite más de `config.CRACK_MAX_VOLUME_LOSS`. En booleanos nuevos, usa Manifold y la misma protección de volumen.

- La semilla CRC de las grietas sale de `primitives.piece_key(ob)` (`ob['ruin_key']`, el nombre pedido al crear), no de `ob.name`. Los prefijos de nombre siguen decidiendo biseles, grietas, huecos y apoyos. Crea las piezas siempre con `primitives.mesh_obj`.
- `runtime.cache` (plantillas) y `runtime.settings` guardan referencias a datos de Blender; los handlers de `registration.py` las sueltan antes de deshacer, rehacer o cargar un archivo. No añadas más referencias a ID en estado de módulo; guarda nombres, como hace `runtime.pending`.
- Hay una ranura de caché por `(calidad, modo)` (`cache.cache_key()`), porque `primitives.bevel` omite piezas en vista previa. Si otra función se comporta distinto según `runtime.preview`, no hace falta tocar la clave: la separación ya la cubre.
- `crack_stone` trabaja en el marco de cara que calcula `crack_frame` (eje del tramo y normal exterior). Usa ese marco para cualquier detalle superficial nuevo; no supongas un muro en X con el frente en −Y.
- Aplica los modificadores de pieza siempre con `primitives.apply_modifier(obj, mod, *operandos)`: usa una escena de taller con solo la pieza y sus operandos. Un `bpy.ops` directo en la escena principal cuesta O(n objetos), lo que hacía el total cuadrático (habitación en Borrador: 74 s → 7 s). No añadas operadores por pieza fuera de esa función.
- `_build_wall` cambia las unidades de la escena en cada generación. `primitives.relief` y `fracture.small_rubble` no se usan.
- `config.QUALITY[q]` es `(niveles de subdivisión, vóxel en mm, segmentos de bisel)`. Otros presets por calidad siguen repartidos en `terrain.py` y `timber.py`.

## Plan vigente

Sigue el orden de `docs/AUDIT.md`: primero la red de seguridad (Fase 0), después la corrección con paridad y luego el rendimiento. Al cerrar una propuesta, márcala en ese archivo. Los límites demostrados en Blender van a `docs/STATUS.md`.
