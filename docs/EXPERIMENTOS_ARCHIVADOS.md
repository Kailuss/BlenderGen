# Experimentos archivados del laboratorio de física

Decisión del usuario (5-11-2026): «prepara archivos, absorbe conocimientos y al cajón». Las ramas se conservan en
`origin` sin integrar. Lo útil ya está en `claude/api-panel` (0.32.29–0.32.30). Aquí queda lo aprendido para no
repetir ensayos.

## `claude/reposo` (fa048bc)
- **Qué era:** umbrales de sueño de Bullet (lineal y angular) configurables y sustituibles por escena para ensayos.
- **Integrado:** `PHYSICS_SLEEP_LINEAR_M_S=.002`, `PHYSICS_SLEEP_ANGULAR_RAD_S=.1` en `config.py`, con lectura por
  escena en el trabajador.
- **Aprendido:** el reposo no corrige la deriva lenta (creep) si hay solapes iniciales. La deriva venía de la
  corrección de penetración, no de piezas que no se duermen. Subir los umbrales solo esconde movimiento real.

## `claude/regimen-energia` (7b61b04)
- **Qué era:** la sonda `tests/blender_panel_regime.py` sobre el banco de panel, con la matriz subpasos 40/400 ×
  impulso dividido sí/no × solape inicial 0 / 0,1 / 0,3 mm, uniones FIXED y umbral escalado 40/subpasos. También el
  ensayo de forma de colisión de activos (`lab_active_shape`) y la colisión desactivada entre pares solapados.
- **Integrado:**
  - Umbral de rotura escalado por 40/subpasos (0.32.29).
  - Colisión desactivada entre pares que empiezan solapados entre 0,02 y 1 mm, nunca con el terreno (0.32.30).
  - Descarte de astillas recortadas por debajo de un píxel de impresión (0,025 mm) (0.32.30).
- **Aprendido:**
  1. **El escalado es lineal:** Bullet corrige la penetración con velocidad ∝ penetración / paso. Con 10 veces más
     subpasos, un solape inicial expulsa 10 veces más fuerte, y los hierros «bailarines» de la zona 32.28 eran
     justo eso. Arreglo: no dejar colisionar pares que nacen solapados.
  2. **Impulso dividido (`use_split_impulse`):** inútil aquí. Con él, un fragmento de tabla atravesaba el suelo de
     seguridad en Equilibrada (fotograma 18). Revertido (a4dc088).
  3. **Régimen (400 subpasos):** caótico en la casa entera aun con las correcciones. Se recomienda Equilibrada
     (40 subpasos, 8 s); Régimen queda marcado como experimental en el panel.
  4. **`lab_active_shape`** (forma de colisión de activos): sin mejora clara; se queda como clave de ensayo.
  5. **Coste de detectar solapes:** 40 s en la casa entera (7192 piezas activas) y 6 s en una zona. La casa tiene
     571 pares solapados de diseño, hasta 12 mm (piedra/tierra, latón, hierro…). Por eso hay un tope de 1 mm.

## Si se retoma
- Volver a Régimen solo con solapes iniciales resueltos en la geometría, no en el laboratorio.
- Medir siempre en Equilibrada 8 s: η, lanzamiento p99 y máximo frente a v, piezas por encima de 1,5·v, fugas
  y deriva final (herramientas en `reports/claude_queue/measure_zone2.py`).
