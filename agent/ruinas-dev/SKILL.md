---
name: ruinas-dev
description: Editar, depurar y probar el generador procedural Ruinas para Blender, localizando sus módulos de mampostería, daño, terreno, carpintería e interfaz sin releer todo el proyecto.
---

# Desarrollo de Ruinas

Trabaja como mantenedor del generador de este proyecto. Esta habilidad aporta contexto y herramientas; no requiere un modelo entrenado ni un servicio externo.

1. Localiza la raíz que contiene `dev.py` y `src/ruinas_panel` (en este espacio: `ruinas/`). Lee su `AGENTS.md` y la fila pertinente de `docs/ARCHITECTURE.md`.
2. Ejecuta `python <raíz>/dev.py find <tema>`; lee el contrato `IA:` y el cuerpo del método afectado. Consulta `docs/STATUS.md` solo si necesitas conocer alcance o limitaciones.
3. Edita las fuentes modulares. Mantén unidades mm, semillas y campos RNA. Estado compartido en `runtime`, geometría fuera de la interfaz. No edites el monolito histórico ni los ZIP generados.
4. Elige comprobaciones proporcionales: `check` para sintaxis/documentación; `test` para generación, caché y registro. Usa `--baseline <script>` cuando necesites comprobar equivalencia durante un refactor. Los logs y JSON quedan en `reports/`.
5. Si cambias aspecto, revisa un render de la zona; si cambias sólido, comprueba cierre y componentes. Usa los comandos descritos en `README.md`. No atribuyas mejoras de velocidad a la modularización sin medirlas.
6. Recarga en Blender con `tools/load_in_blender.py` y empaqueta con `dev.py pack` cuando se solicite una entrega. Comunica archivos cambiados, validación y límites concretos.

Una petición puede invocarse así: «Usa ruinas-dev para mejorar las grietas manteniendo la densidad actual». Si la habilidad no aparece en el selector, lee este archivo por su ruta y sigue el mismo flujo en el chat actual.
