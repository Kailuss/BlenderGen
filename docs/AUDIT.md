# Auditoría de Ruinas v0.21 y plan de propuestas

Fecha: 2026-09-25. Alcance: `src/ruinas_panel/` (25 módulos, unas 2 500 líneas), `dev.py`, `tests/`, `tools/`, `docs/`, `reports/`, `agent/`.

## Método y límites

- Lectura completa de fuentes, pruebas, herramientas y documentación.
- `python dev.py check` pasa: 30 archivos, 91 funciones con contrato `IA:`, 3 pruebas puras.
- Análisis de `reports/modular.json` y `reports/validation.json`. Los hashes de `validation.json` coinciden con las fuentes actuales. `dist/ruinas_panel_v021.zip` y `../../ruinas_panel_v021/` son idénticos a `src/`. Por tanto, las métricas de los informes corresponden al código auditado.
- Verificación posterior con Blender 5.2.2 LTS (la misma versión de `validation.json`):
  - `dev.py test` pasa y los digests de los tres casos son idénticos a los de referencia.
  - `blender_lifecycle.py` pasa con un .blend de prueba creado en v0.21, porque el de v20 no está disponible.
  - Scripts específicos para C1, C2, C3, C9/T4 y R1 (ver «Resultados de la verificación»).
- Cada hallazgo indica su evidencia:
  - **Blender**: reproducido ejecutando Blender.
  - **Datos**: comprobado con los informes existentes.
  - **Código**: deducido de la lectura, sin ejecutar Blender.
  - **Hipótesis**: plausible; hay que probarlo en Blender antes de actuar.

## Resumen

El paquete está bien organizado. Los módulos tienen responsabilidades claras, `dev.py check` comprueba los contratos `IA:`, hay paridad exacta con v20 en tres escenarios y la regeneración desde caché está verificada. Es una buena base.

Problemas principales:

1. **Rendimiento.** El coste crece de forma aproximadamente cuadrática con el número de piezas. Una habitación de dos plantas en Borrador tarda 42,9 s, y el 99 % del tiempo se va en `bpy.ops.object.modifier_apply` aplicado pieza a pieza.
2. **Corrección.** Las grietas de las paredes de retorno (L, U, habitación) se tallan en la cara de junta oculta. La caché puede entregar geometría de vista previa al exportar. `runtime` guarda referencias a datos de Blender que el propio Blender considera inseguras tras deshacer o cargar un archivo.
3. **Red de pruebas.** La paridad solo cubre el modo vista previa en tres casos, y la referencia v20 no está en esta copia. La prueba de ciclo de vida no está conectada a `dev.py`. Nada comprueba el cierre de las piezas fuente.

## Puntos fuertes

- Separación geometría/estructura/servicios/UI respetada casi siempre. `config`, `runtime` y `layout` se importan sin Blender.
- Aleatoriedad local con `random.Random(seed)`, con resultados reproducibles.
- `blender_probe.py` compara digests y exige que la regeneración desde caché sea idéntica.
- Recarga en caliente con limpieza de temporizadores y caché, cubierta por una prueba.
- Tiempos por etapa (`profiling.timed`) guardados con cada generación.
- `STATUS.md` y README documentan los límites con honestidad.

## Hallazgos

Severidad: **Alta** significa resultado incorrecto, riesgo de cierre de Blender o bloqueo del uso normal. **Media** significa incoherencia o coste relevante. **Baja** significa mantenimiento.

| ID | Sev. | Área | Hallazgo | Evidencia |
|---|---|---|---|---|
| C10 | Alta | Grietas | ✅ Resuelto: una grieta podía dejar la piedra reducida a una esquirla | Blender |
| C1 | Alta | Grietas | ✅ Resuelto: en paredes de retorno, las grietas se tallaban en la cara de junta | Blender |
| C2 | Alta | Estado | ✅ Resuelto: referencias a ID en `runtime`, sin handlers de deshacer ni de carga | Blender (carga) + doc. Blender (deshacer) |
| C3 | Media | Caché | ✅ Resuelto: la exportación reutilizaba geometría de vista previa | Blender |
| C4 | Media | UI | ✅ Resuelto: operadores sin `poll` ni gestión de errores | Código |
| C5 | Media | Deshacer | ✅ Mitigado: la geometría queda desfasada tras Ctrl+Z | Hipótesis |
| C6 | Baja | Semillas | ✅ Semillas resueltas: clasificación y semillas dependen del nombre de objeto | Código |
| C7 | Baja | Exportación | ✅ Resuelto: «Reducir caras coplanares» es un Decimate COLLAPSE | Código |
| C8 | Baja | Efectos | Parcial: unidades según preferencia y metadatos en un grupo; materiales y perfiles se siguen reescribiendo | Código |
| C9 | Baja | Geometría | Recorte de X de todos los vértices a ±L/2 | No confirmado en Blender |
| R1 | Alta | Rendimiento | ✅ Resuelto: escalado cuadrático por `bpy.ops` en bucle | Blender |
| R2 | Media | Rendimiento | ✅ Mejorado: hasta ~9 booleanos EXACT por piedra en grietas; ahora Manifold y como mucho una rama por grieta | Código + datos |
| R3 | Media | Densidad | Parcial: en Detalle la densidad va por mm en caras visibles; Trabajo sigue con ~1 000 caras por piedra | Datos |
| R4 | Baja | Rendimiento | ✅ Casi resuelto: bucles Python por vértice (quedan `settle_rubble`, `hole_fragment` y el ruido del desgaste) | Código |
| R5 | Media | UX | ✅ Resuelto: vista previa bloqueante, sin progreso ni pausa automática | Datos |
| T1 | Alta | Pruebas | Parcial: la exportación Manifold y el modo exportación se prueban; falta un caso en Detalle, ahora la calidad por defecto | Código |
| T2 | Media | Pruebas | ✅ Resuelto: sin referencia v20 ni digests guardados que actúen como referencia | Código |
| T3 | Media | Pruebas | Ciclo de vida desconectado y dependiente de un .blend externo | Código |
| T4 | Media | Pruebas | ✅ Resuelto: la prueba no comprobaba el cierre de las piezas fuente | Blender |
| T5 | Media | Pruebas | Planificación de `_build_wall` sin pruebas puras | Código |
| T6 | Baja | Herramientas | Salida no UTF-8; versión repetida en tres sitios | Datos |
| M1–M9 | Baja | Mantenimiento | Ver detalle | Código |

### Corrección

**C10: una grieta puede dejar la piedra reducida a una esquirla.** En el caso de referencia `door_windows_work`, `Piedra entera · hilada 06.05` mide 10,7 × 13,4 × 5,7 mm antes de las grietas y 2,6 × 0,7 × 0,8 mm después: el muro pierde la piedra y en su lugar queda un fragmento. La limpieza de islas de `crack_stone` ([fracture.py:123-143](../src/ruinas_panel/geometry/fracture.py#L123-L143)) conserva el componente con más vértices, no el de más volumen, y el caso de «booleano vacío» solo se detecta cuando no queda ningún vértice ([fracture.py:111](../src/ruinas_panel/geometry/fracture.py#L111)). Las pruebas de paridad no lo detectaban, porque v20 produce el mismo resultado.
**Causa (diagnóstico en Blender):** no es la limpieza de islas. El quinto booleano EXACT (raíz 2 de la grieta) devolvió un fragmento de 16 vértices y 0,38 mm³ en lugar de la piedra de 755 mm³. La protección solo actuaba si la malla quedaba vacía.
**Resuelto:** `crack_stone` mide el volumen tras cada rama y restaura la copia de respaldo si se pierde más de `config.CRACK_MAX_VOLUME_LOSS` (25 %). Una rama sana retira menos del 5 %. Las ramas descartadas se cuentan en `ob['ramas_revertidas']`. `blender_probe` falla si una pieza agrietada queda por debajo del 50 % de su caja previa. Solo cambió `door_windows_work` (141 116 → 142 069 caras); `basic_draft` y `room_beams_draft` conservan su digest. Render revisado: la piedra vuelve a su sitio con sus grietas.

**C1: grietas de paredes de retorno en la cara de junta.** [fracture.py:23-31](../src/ruinas_panel/geometry/fracture.py#L23-L31) toma X como anchura de la piedra y Z como altura, y talla desde `lo[1]`, el mínimo de Y ([fracture.py:89](../src/ruinas_panel/geometry/fracture.py#L89)). Eso es correcto en la fachada, que corre en X con el frente en −Y. Las paredes `left`/`right` ([walls.py:84](../src/ruinas_panel/structure/walls.py#L84)) corren en Y, así que el mínimo de Y de cada piedra es la cara que queda a 0,36 mm de la piedra contigua.
Evidencia: en `door_windows_work`, `Piedra · right.0.0` mide 13,39 × 12,03 × 5,67 mm (X es el grosor, Y la longitud). Aplicando la regla de `apply_damage` con semilla 17 salen exactamente las seis piedras de retorno que tienen caras extra (924–1 015, frente a 864). Se pagan booleanos sin efecto visible y las paredes de retorno no muestran grietas. En la pared `back`, las grietas caen en la cara interior. El fallo viene de v20 (los digests son idénticos).

**C2: referencias a datos de Blender en `runtime`.** [runtime.py](../src/ruinas_panel/runtime.py) mantiene `cache` (objetos plantilla sin usuarios, [cache.py:42-52](../src/ruinas_panel/services/cache.py#L42-L52)), `pending` (una `Scene`) y `settings` (un `PropertyGroup`). El proyecto no usa `bpy.app.handlers` en ningún sitio. La API de Blender advierte: *"you should assume that undo and redo always invalidates all bpy.types.ID instances […] simply not holding references to data when Blender is used interactively by the user is the only way to make sure that the script doesn't become unstable"* ([Troubleshooting Errors & Crashes](https://docs.blender.org/api/current/info_gotchas_crashes.html#undo-redo)).
Caminos de riesgo:
- Abrir otro .blend y editar: `save_cache` llama a `clear_cache`, que accede a `ob.data` de objetos liberados.
- Pulsar Ctrl+Z y volver a unos parámetros ya en caché: `restore_cache` copia plantillas obsoletas.

`blender_probe.py` llama a `clear_cache()` antes de `read_factory_settings` ([blender_probe.py:60-61](../tests/blender_probe.py#L60-L61)), así que la prueba esquiva justo este camino.

**C3: la caché mezcla vista previa y exportación.** `bevel()` omite el mortero y otras piezas cuando `runtime.preview` es verdadero ([primitives.py:32](../src/ruinas_panel/geometry/primitives.py#L32)), pero `cache_signature` no incluye `runtime.preview` ([cache.py:36-39](../src/ruinas_panel/services/cache.py#L36-L39)). Con los valores por defecto (edición y exportación en Trabajo), la vista previa guarda la plantilla `WORK` sin biseles de mortero y «Preparar sólido» la reutiliza. Si no hubo vista previa antes, el mortero sí se bisela, así que el STL depende del historial de la sesión. Las pruebas fijan `preview=True` ([blender_probe.py:48-49](../tests/blender_probe.py#L48-L49)) y no pueden detectarlo.

**C4: operadores sin `poll` ni gestión de errores.** [operators.py](../src/ruinas_panel/ui/operators.py) no define `poll`, y `select_all`, `join` y `modifier_apply` fallan fuera de Modo Objeto. Solo `refresh_timer` captura excepciones. `plan_door` lanza `ValueError` si la puerta no cabe. `make_solid` lanza «Fragmento desconectado» después de unir y remallar ([export.py:73-76](../src/ruinas_panel/services/export.py#L73-L76)). En ese caso el usuario ve una traza de Python, el sólido a medio procesar queda en la escena y la fuente sigue visible.

**C5: deshacer y vista previa (hipótesis).** La regeneración se ejecuta en un temporizador sin paso de deshacer. El paso que Blender guarda al mover un deslizador contiene los parámetros nuevos con la geometría anterior. Tras Ctrl+Z, la geometría puede corresponder a un paso más antiguo que los parámetros, y ningún callback la regenera. Hay que comprobarlo a mano. `scene['parametros_muro']` ya permite detectar el desfase.

**C6: nombres como clave.** La semilla de las grietas usa `crc32(ob.name)` ([fracture.py:368](../src/ruinas_panel/geometry/fracture.py#L368)). La clasificación usa prefijos y subcadenas del nombre (`'Piedra'`, `'Pilar'`, `'· sillar'`, `'pie'`, `'núcleo'`, `'Esquirla'`). Si el archivo ya contiene un objeto con ese nombre (por ejemplo, porque el usuario duplicó la colección para guardar una variante), Blender añade `.001` y las grietas cambian. Los informes contienen entre 18 y 337 nombres con sufijo automático, aunque hoy ninguno entra en la selección de grietas. Además, `'Núcleo'` en [openings.py:40](../src/ruinas_panel/structure/openings.py#L40) no coincide con ningún objeto.

**C7: Decimate mal nombrado.** El modificador «Reducir caras coplanares» ([export.py:46-48](../src/ruinas_panel/services/export.py#L46-L48)) usa el modo por defecto `COLLAPSE` con `ratio=.28`. Elimina el 72 % de las caras de forma uniforme; no disuelve caras coplanares. Hay que decidir cuál era la intención y medir el efecto en el STL.

**C8: efectos secundarios en cada generación.**
- `_build_wall` fija las unidades de la escena (métrico, escala 0,001, mm) ([walls.py:110-112](../src/ruinas_panel/structure/walls.py#L110-L112)).
- `material()` sobrescribe `diffuse_color` de materiales existentes con el mismo nombre ([primitives.py:13-14](../src/ruinas_panel/geometry/primitives.py#L13-L14)).
- `apply_profiles` escribe propiedades RNA.
- Se guardan 12 JSON de auditoría como propiedades de escena, que acaban en el .blend.

**C9: recorte global de X (hipótesis).** [walls.py:351-353](../src/ruinas_panel/structure/walls.py#L351-L353) limita la X de todos los vértices de la colección a ±L/2, incluidos escombros, grava y tierra. Una pieza que sobresale queda aplanada contra el plano extremo y puede generar caras degeneradas. La propuesta 0.3 lo detectaría.

### Rendimiento

**R1: coste cuadrático por operadores en bucle.** Cada piedra pasa por tres `modifier_apply` (bisel, subdivisión y suavizado). Cada hueco y cada rama de grieta pasa además por un booleano EXACT. Datos de `reports/modular.json`:

| Caso | Objetos | Total | Biseles | Desgaste | Aberturas | ms por bisel (aprox.) |
|---|---|---|---|---|---|---|
| basic_draft | 209 | 1,50 s | 0,43 s | 0,91 s | 0,00 s | ~4 |
| door_windows_work | 277 | 7,47 s | 0,70 s | 1,95 s | 0,85 s | — |
| room_beams_draft | 974 | 42,90 s | 11,64 s | 20,84 s | 10,02 s | ~24 |

Con 4,7 veces más objetos, el tiempo se multiplica por 28,6 y cada llamada cuesta unas seis veces más. El mecanismo probable, pendiente de medir, es que cada objeto nuevo obliga a reconstruir las relaciones del depsgraph antes del siguiente operador, de modo que cada llamada cuesta O(n).

**R2: grietas caras.** `crack_stone` crea un cortador y aplica un booleano EXACT por rama (de 1 a 3 raíces, con 0 a 2 ramas cada una). En cada rama copia además la malla completa como respaldo ([fracture.py:81-120](../src/ruinas_panel/geometry/fracture.py#L81-L120)). En `door_windows_work` son 2,9 s de 7,5 s.

**R3: densidad poco «lowpoly».** En Trabajo, las piedras suman 120 565 de las 141 116 caras (unas 1 000 por piedra). [weather.py:20](../src/ruinas_panel/geometry/weather.py#L20) dice que la densidad depende de milímetros, pero el código usa un nivel fijo por calidad ([weather.py:24](../src/ruinas_panel/geometry/weather.py#L24)). Una piedra de 3 mm y una de 20 mm reciben la misma subdivisión.

**R4: bucles Python por vértice.** Aparecen en las transformaciones de tramo ([walls.py:62-65](../src/ruinas_panel/structure/walls.py#L62-L65)), en el recorte de X y en `carve_rectangle`, que convierte todos los vértices de todos los objetos del muro para cada hueco ([openings.py:37-47](../src/ruinas_panel/structure/openings.py#L37-L47)). También se asigna `use_smooth` cara a cara. Numpy (incluido en Blender) con `foreach_get`/`foreach_set`, `Mesh.transform` o `Mesh.shade_smooth()` reduce este coste. En particular, el filtro por caja envolvente de `carve_rectangle` con numpy da resultados idénticos.

**R5: vista previa bloqueante.** El temporizador genera en el hilo principal. Con «Habitación», cada ajuste congela Blender unos 43 s en Borrador y después vuelve a generar en Trabajo. No hay barra de progreso, cancelación ni pausa automática de la vista previa.

### Pruebas y herramientas

**T1: cobertura de paridad.** Hay tres casos y todos usan `runtime.preview=True`. Ninguno usa Detalle. `make_solid` no forma parte de `dev.py test`. La combinación de agujeros y grietas en Trabajo nunca se ejecuta: los casos en Trabajo usan `hole_count=0` y Borrador no genera grietas. El digest tampoco incluye materiales, propiedades personalizadas ni normales.

**T2: referencia de paridad ausente.** `--baseline ../outputs/muro_20/generador_muro.py` no existe en esta copia. Sin `--baseline`, `dev.py test` no compara con nada guardado: solo comprueba que la regeneración desde caché se repite. Una regresión de geometría pasaría desapercibida.

**T3: ciclo de vida.** [blender_lifecycle.py](../tests/blender_lifecycle.py) exige `--input` con un .blend de v20 que no está en el proyecto. `dev.py` no lo invoca y no prueba deshacer ni abrir otro archivo (C2, C5).

**T4: cierre de malla.** Solo se comprueba que el sólido fusionado sea variedad (manifold), y solo en un caso Borrador sin grietas, puerta ni ventanas ([blender_lifecycle.py:51](../tests/blender_lifecycle.py#L51)). Las piezas fuente no se validan: pueden tener caras degeneradas o bordes abiertos tras booleanos o `clip_closed`.

**T5: planificación sin pruebas puras.** `_build_wall` contiene unas 150 líneas de cálculo puro: hiladas conservadas con apoyo ≥ 62 %, perfil de derrumbe, pilares y selección de huecos conexos. Como están mezcladas con la creación de mallas, solo se pueden probar con Blender.

**T6: herramientas.**
- `dev.py find` imprime `·` y tildes, que salen como `�` en consolas Windows sin UTF-8.
- La versión y el nombre del ZIP se repiten en `bl_info`, en el título del panel (`v0.21`) y en `dev.py` ([dev.py:82](../dev.py#L82), [dev.py:88](../dev.py#L88)).
- Los nombres de caso se repiten en [dev.py:107](../dev.py#L107) y en `blender_probe.py`.
- `blender_path` solo busca Blender 5.2 en la ruta por defecto.

### Mantenimiento

- **M1.** `_build_wall` ([walls.py:96-358](../src/ruinas_panel/structure/walls.py#L96-L358)) ocupa 260 líneas con funciones anidadas que capturan 8 variables, y mezcla plan, mallas y metadatos. `generation` llama a esta función privada.
- **M2.** Hay datos constantes fuera de `config`, en contra de la regla de `AGENTS.md`:
  - presets por calidad en [terrain.py:38-39](../src/ruinas_panel/geometry/terrain.py#L38-L39), [terrain.py:90-91](../src/ruinas_panel/geometry/terrain.py#L90-L91) y [timber.py:21-22](../src/ruinas_panel/geometry/timber.py#L21-L22);
  - 19 llamadas a `material()` que repiten nombre y color;
  - medidas de ventana y viga (15, 16, 14, 49,5, 4,5) en `openings.py`;
  - `QUALITY` como tupla posicional (`[0]` subdivisión, `[1]` vóxel, `[2]` segmentos de bisel);
  - `'MURO · sólido exportable'` repetido en `preview.py` y `export.py`.
- **M3.** Los callbacks se instalan al importar, mutando `__annotations__[campo].keywords['update']` ([registration.py:13-15](../src/ruinas_panel/registration.py#L13-L15)). Esto depende de detalles internos de `bpy.props`.
- **M4.** Código muerto o engañoso:
  - `primitives.relief` y `fracture.small_rubble` no se usan;
  - el parámetro `rh` de `trim_door_courses` es en realidad la tabla de cotas;
  - hay un comentario en francés en [timber.py:47](../src/ruinas_panel/geometry/timber.py#L47);
  - `parametros_muro` se escribe dos veces ([walls.py:357](../src/ruinas_panel/structure/walls.py#L357), [generation.py:41](../src/ruinas_panel/services/generation.py#L41)) y `plan_door` se calcula dos veces;
  - la comprobación de apoyo de ventanas duplica `wall_hit` ([openings.py:150-156](../src/ruinas_panel/structure/openings.py#L150-L156)).
- **M5.** Dependencias: `geometry/rubble` importa `structure/layout`; `geometry/*` importa `services/profiling`; `timber` y `fracture` leen `runtime.settings` en vez de recibir parámetros. `ARCHITECTURE.md` describe un ciclo entre generación y exportación que ya no existe.
- **M6.** Documentación:
  - `USERGUIDE.md` es una copia de `README.md` (sin `#` en el título y con CRLF) y no explica los parámetros ni el flujo de exportación;
  - README incluye la ruta de Python de otro equipo (`C:\Users\yhora\...`);
  - la habilidad y el README están orientados a Codex.
- **M7.** No hay repositorio git, aunque existe `.gitignore`. Los finales de línea están mezclados: `weather.py` combina CRLF y LF, mientras `dev.py` y README usan LF.
- **M8.** Empaquetado: el complemento usa `bl_info`, el formato heredado; desde Blender 4.2 las extensiones usan `blender_manifest.toml`. El autor figura como `'Codex'`.
- **M9.** Los cuatro operadores comparten el mismo contrato genérico (`IA: Operador Blender: respeta UNDO…`), contra la regla de evitar instrucciones repetidas.

## Plan de propuestas

Principios:

1. Crear la red de seguridad antes de cambiar nada.
2. Separar los cambios que conservan la paridad exacta de los que cambian la geometría.
3. Aceptar cada cambio de geometría con los mismos parámetros: medir tiempo y caras, revisar render y cierre, y regenerar los digests de referencia de forma explícita.

Esfuerzo: **S** es un cambio local en uno o dos archivos; **M** abarca varios módulos o pruebas nuevas; **L** rediseña un subsistema.

### Fase 0: red de seguridad (sin cambiar geometría)

| # | Propuesta | Resuelve | Esf. |
|---|---|---|---|
| 0.1 | ✅ `git init`, `.gitattributes` con finales de línea y primer commit que incluya `reports/` | M7 | S |
| 0.2 | ✅ `dev.py test` compara con `reports/expected.json` (digests, versión de Blender, caras degeneradas conocidas); `--update-expected` acepta cambios | T2 | S |
| 0.3 | ✅ Comprobación de cierre por pieza en `blender_probe`: falla ante aristas abiertas y registra las caras de área casi nula | T4, C9 | S |
| 0.4 | ✅ (como `window_detail`) Casos nuevos: `holes_cracks_work` (L, agujeros, grietas 0,6), `export_work` (`preview=False`, `make_solid` y comprobación manifold) y `detail_smoke` | T1, C1, C3 | M |
| 0.5 | `dev.py test --lifecycle` con un .blend creado por la propia prueba; pasos: deshacer, abrir otro archivo y regenerar | T3, C2, C5 | M |
| 0.6 | `dev.py`: ✅ salida en UTF-8; pendiente: versión leída de `bl_info` y casos en una sola lista | T6 | S |

Criterio de salida: los casos actuales conservan su digest. Los casos nuevos quedan documentados, incluidos los que fallen por C1–C3, que es lo esperado.

### Fase 1: corrección

| # | Propuesta | Resuelve | Esf. | Geometría |
|---|---|---|---|---|
| 1.1 | ✅ Handlers `@persistent` en `load_pre`, `undo_pre` y `redo_pre` que vacíen `runtime.cache`, `pending` y `settings` sin tocar IDs. En `load_post` y `undo_post`, borrar los huérfanos `__RUIN_CACHE__*` buscándolos por nombre. A medio plazo: caché de datos puros (vértices, caras, materiales, propiedades) sin objetos Blender | C2 | S (+M) | Igual |
| 1.2 | ✅ Operadores: `poll` (Modo Objeto y `ruin_settings` disponible), `try/except` que llame a `self.report({'ERROR'}, …)`, eliminación del sólido parcial y restauración de la visibilidad | C4 | S | Igual |
| 1.3 | ✅ Clave estable `ob['ruin_key']`, asignada al crear con el mismo texto que el nombre actual, como semilla CRC; rol `ob['ruin_role']` para clasificar | C6 | M | Igual (mismos textos) |
| 1.4 | ✅ Para C3, medir dos opciones: (a) incluir `runtime.preview` en la firma; (b) biselar siempre el mortero. Elegir por tiempo y resultado | C3 | S | (a) igual; (b) cambia |
| 1.4b | ✅ C10: revertir la rama si el booleano quita más del 25 % del volumen, y prueba que lo detecta | C10 | S | Cambió `door_windows_work` |
| 1.5 | ✅ Grietas en el marco local del tramo (usando `wall_id` y el eje de `paredes_generadas`), decidiendo qué cara es la visible en cada pared | C1 | M | Cambia en L/U/habitación |
| 1.6 | ✅ En `undo_post`, si `parametros_muro` no coincide con los ajustes actuales, programar una vista previa | C5 | S | Igual |
| 1.7 | ✅ Renombrar el Decimate o corregirlo según la intención (COLLAPSE o DISSOLVE), midiendo caras y aspecto del STL | C7 | S | Solo el STL, si se corrige |

### Fase 2: rendimiento con paridad exacta

| # | Propuesta | Resuelve | Esf. |
|---|---|---|---|
| 2.1 | ✅ Contar llamadas a `bpy.ops` y medir ms por llamada según el número de objetos (ampliando `profiling.timed`) | R1 | S |
| 2.2 | ✅ Experimento de «escena de trabajo»: aplicar bisel, subdivisión, suavizado y booleanos de cada pieza en una escena temporal que solo contiene esa pieza y su cortador, y enlazarla después a la colección. Con los mismos modificadores, los digests deberían ser idénticos. Objetivo: coste por llamada constante | R1, R2 | M |
| 2.3 | ✅ `carve_rectangle`: caja envolvente con `foreach_get` y numpy, con la misma lógica de inclusión | R4 | S |
| 2.4 | ✅ (salvo `shade_smooth()`) Vectorizar las transformaciones de 90° y el recorte de X; usar `shade_smooth()` | R4 | S |
| 2.5 | Componentes conexos de `make_solid` y `crack_stone` con numpy (union-find) | R4 | S |

Criterio: digests idénticos y tiempos medidos en los mismos casos. Si 2.2 no conserva la paridad, pasa a la Fase 3.

### Fase 3: rendimiento que cambia la geometría (requiere decisión explícita)

| # | Propuesta | Resuelve | Esf. |
|---|---|---|---|
| 3.1 | (Parcial: Manifold ya hace barato cada booleano) Un solo booleano por piedra, con todas las ramas en un cortador (o un operando de colección) y sin copia de respaldo por rama | R2 | M |
| 3.2 | Subdivisión adaptativa según la longitud de arista en mm, sin subir la densidad por defecto; comparar caras, tiempo y render | R3 | M |
| 3.3 | `bmesh.ops.bevel` en lugar del modificador; comprobar si el resultado coincide | R1 | M |
| 3.4 | Recortar las ventanas en el plan de hiladas, como la puerta, en lugar de usar booleanos | R1 | L |

### Fase 4: mantenibilidad

| # | Propuesta | Resuelve | Esf. |
|---|---|---|---|
| 4.1 | Extraer la planificación de `_build_wall` a `structure/plan.py` (puro) y probar: apoyo ≥ 62 %, sin solapes, huecos conexos, pilares fuera de la puerta y determinismo por semilla. Conservar el orden de las llamadas aleatorias y verificar digests | T5, M1 | M |
| 4.2 | En `config`: `QUALITY` con campos con nombre, presets por calidad de terreno y madera, `MATERIALS`, medidas de huecos y `SOLID_NAME`. Sustituir las exclusiones sueltas por grupos de campos (`GEOMETRY_FIELDS`, `DAMAGE_FIELDS`, `UI_FIELDS`) | M2 | M |
| 4.3 | Pasar parámetros explícitos a `timber` y `fracture` en vez de leer `runtime.settings` | M5 | S |
| 4.4 | Declarar `update=` en `settings.py` y eliminar la mutación de anotaciones | M3 | S |
| 4.5 | Retirar el código muerto, corregir comentarios y contratos repetidos, y actualizar `ARCHITECTURE.md` | M4, M5, M9 | S |

### Fase 5: experiencia de uso y distribución

| # | Propuesta | Resuelve | Esf. |
|---|---|---|---|
| 5.1 | ✅ Barra de progreso (`window_manager.progress_*`) y pausa automática de la vista previa cuando la última generación supere un umbral (por ejemplo, 3 s), con aviso en el panel | R5 | S |
| 5.2 | ✅ Subpaneles plegables (`layout.panel` o `bl_parent_id`), conservando los identificadores RNA | UX | S |
| 5.3 | ✅ Mensajes de error de exportación que digan qué cambiar | C4 | S |
| 5.4 | ⏸ Descartado por ahora (decisión del usuario) `blender_manifest.toml` junto a `bl_info`, con una única fuente de versión y el autor correcto | M8, T6 | S |
| 5.5 | ✅ `USERGUIDE.md` real (parámetros, flujo, exportación STL, límites) y README sin rutas de otro equipo | M6 | S |
| 5.6 | ✅ (preferencia «Escena en milímetros») Fijar las unidades solo al crear la colección la primera vez, o mediante una opción, y documentarlo | C8 | S |
| 5.7 | ✅ (grupo `scene['ruinas']`, `meta.py`) Guardar los metadatos JSON en la colección o bajo una sola clave | C8 | S |

### Orden recomendado

1. 0.1, 0.2, 0.3 y 0.6: una sesión, sin tocar geometría.
2. 1.1 y 1.2: eliminan el riesgo de cierre y los errores visibles, con paridad intacta.
3. 2.1 y después 2.2: la mayor mejora esperada; su resultado decide si hace falta la Fase 3.
4. 0.4 y 0.5, y después 1.3–1.7 con los casos nuevos.
5. Fases 4 y 5 según prioridad; la Fase 3 solo tras aprobar el cambio visual.

## Fuera de alcance

- Reformatear todo el código: cambio masivo sin beneficio funcional que ensucia los diffs.
- Subir la densidad por defecto para ocultar artefactos.
- Reescribir en Geometry Nodes: podría resolver R1 y R5 y permitir edición no destructiva, pero es una reescritura completa y convendría evaluarla como proyecto aparte.

## Resultados de la verificación (Blender 5.2.2, 2026-09-25)

- **`dev.py test`:** pasa en 66 s. Los tres digests son idénticos a la referencia. Tiempos: 1,58 s, 8,02 s y 36,79 s (antes 1,50 s, 7,47 s y 42,90 s).
- **`blender_lifecycle.py`:** pasa con un .blend de prueba creado en v0.21 (58 641 caras en el sólido). No prueba la compatibilidad con archivos de v20.
- **C1 confirmado.** En `door_windows_work`, los vértices nuevos de las seis piedras `right.*` agrietadas están todos a menos de 1,6 mm de su cara −Y. En esas piezas, −Y es la cara de junta, porque el tramo corre en Y (12 mm), y ninguna grieta llega a las caras exteriores. En la fachada, −Y es el frente, que es lo correcto.
- **C2 confirmado para la carga de archivo.** Tras generar y cargar otro archivo sin limpiar la caché, la siguiente generación falla con `ReferenceError: StructRNA of type Object has been removed`; la posterior funciona. Blender no se cerró. Deshacer no se puede probar en modo `-b`.
- **C2 y C4 resueltos (propuestas 1.1, 1.2 y 5.3).**
  - `registration` instala handlers `load_pre`, `undo_pre` y `redo_pre` que sueltan las referencias de `runtime`, y handlers `*_post` que borran por nombre las plantillas huérfanas.
  - `runtime.pending` guarda el nombre de la escena, no la escena.
  - Los operadores tienen `poll` con mensaje, y sus errores llegan como informe de Blender, no como traza.
  - Si `make_solid` falla, borra las copias y el sólido parcial.
  - `blender_probe` lo comprueba: carga con caché llena, handlers de deshacer simulados, puerta que no cabe y fragmento suelto en la fusión.
  - La recarga en caliente deja una sola copia de cada handler.
  - Queda pendiente probar Ctrl+Z real con interfaz. La caché sigue guardando objetos Blender entre deshaceres; la caché de datos puros es la mejora a medio plazo de 1.1.
- **C3 confirmado.** En `basic_draft`, la «exportación» tras una vista previa sale de la caché: el mortero tiene 509 caras y el digest difiere. Sin vista previa previa, el mortero tiene 1 781 caras.
- **C3 resuelto con la opción (a) y la caché separada por modo.** Medidas en la misma sesión, calidad Trabajo:

| | basic | door_windows |
|---|---|---|
| Vista previa actual | 20,2 s | 17,1 s |
| (b) vista previa biselando el mortero | 20,9 s (+4 %) | 18,7 s (+9 %) |
| Exportar desde la caché de vista previa (antes) | 19,7 s | 15,8 s |
| (a) exportar reconstruyendo | 27,5 s (+40 %) | 28,3 s (+78 %) |
| Diferencia entre sólidos, media / p99 / máx. | 0,02 / 0,33 / 1,15 mm | 0,02 / 0,34 / 1,16 mm |

  Motivos de la elección: la vista previa, que es la acción frecuente, no se toca; los digests de referencia no cambian; y la exportación recibe la geometría biselada prevista. `cache.cache_key()` usa `(calidad, modo)`: exportar no expulsa la caché de vista previa, y repetir la exportación sin cambios usa su propia caché. `blender_probe` lo comprueba, y falla con la clave anterior (solo calidad).
- **C10 descubierto** durante la verificación de C1 (ver hallazgo).
- **C9 y T4:** ninguna arista abierta en los tres casos (1 460 piezas). Solo hay una cara de área casi nula, en `Piedra caída · fractura 3551.1`. El recorte de X no produce los problemas previstos.
- **R1 confirmado.** Coste medio de `bevel` en `room_beams_draft` según el número de objetos en `bpy.data`:

| Objetos | 0–99 | 200–299 | 400–499 | 600–699 | 800–899 | 900–999 |
|---|---|---|---|---|---|---|
| ms por llamada | 2,2 | 9,8 | 17,7 | 28,1 | 41,9 | 46,7 |

El coste por llamada crece de forma lineal, así que el total es cuadrático. La causa queda confirmada con la propuesta 2.2: cada operador trabajaba sobre toda la escena principal.
- **R1 resuelto (2.2, escena de taller).** `primitives.apply_modifier` aplica cada modificador de pieza (bisel, subdivisión, suavizado y booleanos de grietas y huecos) en la escena `RUINAS · taller`, que solo contiene la pieza y su cortador. La escena se busca por nombre y `generation.generate` la borra al terminar, aunque falle. Los digests son idénticos en los tres casos y la geometría no cambia. Se desactiva con `config.ISOLATE_MODIFIERS`.

| Caso | Sin taller | Con taller | Mejora |
|---|---|---|---|
| basic_draft | 3,4 s | 1,4 s | ×2,4 |
| door_windows_work (dos muestras alternas) | 13,0 s | 7,3 s | ×1,8 |
| room_beams_draft | 74,3 s | 6,8 s | ×11 |
| Vista previa real con interfaz (habitación, Borrador) | 72,9 s | 6,9 s | ×10,6 |

  La prueba con interfaz recorrió el camino real: callback, temporizador y generación. Hubo que arrancar Blender con `--gpu-backend vulkan`, porque desde la consola de desarrollo el driver OpenGL de NVIDIA se cierra al abrir la ventana, incluso sin el complemento. `blender_probe` comprueba que la escena de taller no queda tras generar ni tras un fallo.
- **Exportación sin pérdida de detalle (objetivo de resina).** El remallado vóxel de `make_solid` (0,32 mm en Trabajo) borraba grietas, vetas y biseles, y dejaba goterones en las juntas. Ahora `config.EXPORT_METHOD='MANIFOLD'` une las copias con un booleano Manifold exacto; el vóxel sigue disponible como alternativa. Con volumen con signo, las cáscaras sueltas de menos de `EXPORT_DEBRIS_MM3` (2 mm³) se eliminan como residuos, los huecos interiores también, y un fragmento mayor rechaza la exportación.

| Caso | Calidad | Fusión | Caras | Residuos | Huecos |
|---|---|---|---|---|---|
| basic_draft | Borrador | 0,7 s | 13 015 | 2 | 1 |
| door_windows_work | Trabajo | 4,1 s (vóxel: 9,3 s) | 108 410 (vóxel: 170 684) | 5 | 48 |
| room_beams_draft | Borrador | 6,3 s | 60 278 | 4 | 15 |
| 3 agujeros | Detalle | 8,0 s | 308 217 | 11 | 31 |

  Todos quedan en una sola pieza cerrada. `blender_probe` comprueba que el sólido es cerrado, de una pieza y con la misma caja envolvente que la fuente.
- **Grietas imprimibles en resina (Anycubic Photon P1 Max, píxel de 24,8 µm; escala 28–35 mm).**
  - Con la sección en V, el ancho en la superficie hundida por el desgaste es 2w·(d−e)/(d+0,2). Al 0,2 solo entre el 33 % y el 77 % del largo de cada grieta superaba 0,15 mm, y cerca de la punta la grieta no llegaba a atravesar la superficie erosionada.
  - `fracture.printable` aplica `config.CRACK_PRINT`: 0,15 mm de ancho en superficie, suponiendo 0,25 mm de erosión, y 0,5 mm de profundidad hasta el 85 % del largo; después se afina de forma continua hasta la punta. Las partidas aplican los mínimos en todo su largo.
  - Resultado: entre el 85 % y el 95 % del largo supera 0,15 mm, también al 0,2. El aspecto al 0,6 apenas cambia (renders revisados).
  - Los valores son provisionales hasta calibrarlos con una impresión de prueba. `python dev.py calibrate` (`tools/print_test.py`) genera una placa de 72 × 44 mm, cerrada y de una sola pieza, con leyenda: filas de ancho, de profundidad y de pivotes, y dos piedras reales en Detalle. El usuario decidió no imprimirla (2026-09-25): los valores se quedan como están, elegidos a partir de la ficha de la impresora; la placa queda disponible como herramienta opcional.
- **Huecos de ventanas y vigas con Manifold (fallo heredado de v20).** `carve_rectangle` usaba EXACT, que fallaba en silencio igual que en las grietas: devolvía una malla casi vacía y la pieza se borraba.
  - En el caso de referencia `door_windows_work` (Trabajo) desaparecían 5 piedras junto a las ventanas (`hilada 02.01`, `hilada 04.01`, `right.2.1`, `right.3.0` y `right.4.1`), y en su lugar solo se veía mortero.
  - En Detalle desaparecían más, el marco de la ventana quedaba flotando y la exportación Manifold lo rechazaba.
  - Ahora se usa `config.BOOLEAN_SOLVER='MANIFOLD'` (antes `CRACK_SOLVER`) con una protección: si el booleano quita más volumen que el cruce de la pieza con el hueco, se restaura la pieza y se marca `hueco_revertido`. Renders revisados y referencias actualizadas.
- **Detalle fino para resina (solo en calidad Detalle, `config.FINE_DETAIL`).**
  - `weather.refine_visible` subdivide hasta ~0,22 mm las caras visibles y los biseles (frente, dorso y techo); las juntas y la base no.
  - `weather.fine_relief` añade picado Voronoi (poros de ~0,45 mm, hasta 0,12 mm de hondo) y grano de nubes (0,04 mm) con modificadores Displace en coordenadas globales, siempre hacia dentro.
  - Coste en la puerta con grietas al 0,6 en Detalle: generar 87 s y fundir 74 s; 1,42 millones de caras fuente y 1,09 millones en el STL. Sin detalle fino: 34 s + 18 s y 391 000 caras.
  - En los bordes superiores queda una arista unos 0,03 mm más saliente, porque el relieve se aplica en diagonal en el bisel; está por debajo del píxel de la impresora.
- **Rendimiento de Detalle y Detalle por defecto (2026-09-25).** La calidad de exportación por defecto pasa a Detalle; los .blend guardados conservan su valor.
  - El perfil (cProfile) señaló cuatro causas:
    - `foreach_get` con matrices float64 copiaba valor a valor; ahora lee en float32, el tipo nativo.
    - `refine_visible` recorría las aristas en Python; ahora usa numpy.
    - `terrain.surface` recorría los triángulos uno a uno; ahora lanza un rayo sobre un BVH.
    - Había bucles por vértice en `wall_tree`, `carve_rectangle`, las transformaciones de tramo, los escombros, las cajas de grieta y el recorte de X; ahora usan numpy.
  - Además, Detalle parte de subdivisión nivel 2 en vez de 3, y `refine_visible` pone la densidad solo en caras visibles. Así desaparece también el reborde de los bordes superiores.
  - Puerta con grietas al 0,6 en Detalle: generar 87 → 34 s, fundir 74 → 34 s, STL de 1 091 000 → 607 000 caras. Trabajo y Borrador también mejoran (puerta 6,7 → 4,3 s).
  - Las referencias cambian como mucho 0,0002 mm en tierra y escombros, por el BVH en float32.
- **Caso `window_detail` (0.4).** Genera en Detalle y en modo exportación un muro de 80 mm con ventana, agujero y grietas al 0,6. Exige que ningún booleano se revierta y que el sólido Manifold salga en una sola pieza cerrada.
- **Vista previa sin bloqueos largos (5.1, R5).**
  - `preview.ProgressCursor` muestra el progreso en el cursor, contando las piezas creadas frente a la generación anterior.
  - `runtime.durations` guarda lo que tardó la última generación de cada calidad. Con `config.PREVIEW_PAUSE_SECONDS`, el refinado espera a «Actualizar» por encima de 4 s y la vista rápida por encima de 10 s; el panel lo explica.
  - Probado con interfaz (Vulkan) en una habitación: Borrador sigue siendo automático y Trabajo (31 s) queda en pausa.
  - `primitives.remove_objects` borra con `bpy.data.batch_remove`. Borrar pieza a pieza recorría el archivo en cada llamada: tras una habitación en Trabajo, regenerar Borrador pasa de 12,1 a 6,5 s.
  - Pendiente: la habitación en Trabajo con grietas al 0,6 tarda 31 s.
- **Interfaz según las guías de Blender (5.2, 5.6, 5.7).**
  - Panel principal: acciones arriba («Actualizar», «Preparar sólido»), estado con icono (pausa, error o información), semilla con variante y candado compacto.
  - Subpaneles generados desde `config.SECTIONS`, con `bl_parent_id`: Construcción, Distribución y Acabado abiertos; Puerta y Ventanas con la casilla en la cabecera; Calidad y los avanzados plegados. El botón de restablecer va en `draw_header_preset`.
  - `use_property_split`; lo que no aplica se atenúa en vez de ocultarse; tipo y altura en filas completas.
  - Nombres visibles cortos, con el detalle en `description`; las claves RNA no cambian.
  - `draw()` memoriza el JSON en lugar de decodificarlo en cada redibujado.
  - Entrada «Ruina» en Añadir > Malla y `bl_description` en los operadores.
  - `AddonPreferences`: umbrales de pausa, escena en mm y fusión (Manifold por defecto).
  - Los metadatos pasan de 14 propiedades sueltas a un grupo `scene['ruinas']`.
  - Revisado con capturas reales de Blender (Vulkan).

Pendiente:

- [x] C1: render de un muro en L para confirmarlo visualmente.
- **C1 resuelto, junto con un rediseño del aspecto de las grietas.**
  - `crack_frame` elige la cara exterior de cada tramo usando el eje de `paredes_generadas`, y en habitación y U el lado opuesto al centro del edificio.
  - Las grietas son ahora trazos quebrados (tramos de ~0,8 mm de longitud irregular) con sección en V que se afina hasta una punta cerrada, y como mucho una rama más fina.
  - Renders revisados: en la pared lateral las grietas ya están en la cara visible.
  - En `door_windows_work`, el paso de grietas baja de 6,6 s a 4,2 s (dos muestras alternas en la misma sesión) y las caras pasan de 142 069 a 142 206.
  - Nueva cara degenerada en `Piedra · right.2.2`; la malla sigue cerrada y queda anotada en la referencia.
- **Solver Manifold para grietas (hallazgo nuevo).** Con EXACT fallaban en silencio unas 25 de cada ~90 ramas de grieta en `door_windows_work` al 0,6: el cortador estaba bien (cerrado, volumen positivo, sin autointersecciones), pero EXACT devolvía una malla de volumen cero y la protección de C10 lo deshacía. `config.CRACK_SOLVER='MANIFOLD'` (Blender 4.5+): 0 reversiones y el paso de grietas baja de 4,5 s a 2,0 s. Candidato para `carve_rectangle` (ventanas y vigas) en la fase de rendimiento.
- **Piezas partidas y tensión cerca de huecos (petición de uso).**
  - `crack_stress` da una tensión de 0 a 1 según la cercanía (16 mm) a puerta, ventanas, agujeros y extremos del tramo. Los sillares de pilar tienen un mínimo de 0,4; los pilares de conexión siguen sin grietas.
  - Con esa tensión suben la probabilidad de grieta y la de «partida», una grieta de borde a borde por el lado corto que parte la pieza por la mitad. Todas las cifras están en `config.CRACK_STRESS`.
  - Las piedras sin partida conservan exactamente la forma que tenían.
  - Los trazos terminan al tocar el borde de la cara, sin deslizarse sobre él.
  - Renders revisados y aceptados. `door_windows_work`: 142 206 → 142 044 caras.
- **Fase 1 cerrada (1.3, 1.6 y 1.7), sin cambios de geometría.**
  - **1.3:** `mesh_obj` guarda `ruin_key` con el nombre pedido, y `piece_key()` alimenta la semilla CRC de las grietas. Duplicar la colección ya no cambia las grietas de una nueva generación. La clasificación sigue por prefijo de nombre: los sufijos `.001` no la alteran, así que no hacen falta roles.
  - **1.6:** `after_undo` (handlers `undo_post` y `redo_post`) compara `parametros_muro` con los ajustes actuales y, si difieren, reprograma la vista previa. Probado simulando el estado que deja un deshacer; el Ctrl+Z real con interfaz sigue pendiente.
  - **1.7:** se mantiene COLLAPSE al 28 % y se corrige el nombre. Medido sobre el mismo remallado: COLLAPSE da 122 575 caras en 5,4 s con 0,037 mm de desviación máxima; DISSOLVE a 5° da 58 394 caras pero tarda 133 s.
  - Además, la limpieza de handlers en recarga retira cualquier handler del módulo, aunque cambie su nombre.
- [ ] C2 y C5 con deshacer: requieren Blender con interfaz (generar, pulsar Ctrl+Z, mover un deslizador).

Cuando un hallazgo quede demostrado en Blender, anótalo en `docs/STATUS.md` como límite conocido o márcalo aquí como resuelto.
