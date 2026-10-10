# Mapa de edición

La base 0.31 integra el edificio completo aportado en `dist/ruinas_v031_completo.zip`. El código editable vive únicamente en `src/ruinas_panel/`; el ZIP es una referencia de entrada, no una segunda fuente.

| Tema | Archivo en `src/ruinas_panel` | Contrato principal |
|---|---|---|
| Perfiles, campos, secciones, calidad | `config.py` | Constantes sin dependencia de Blender |
| Estado temporal | `runtime.py` | Única instancia por sesión; no persiste en .blend |
| Datos de auditoría en la escena | `meta.py` | Un solo grupo `scene['ruinas']` con JSON por clave; borra las claves sueltas antiguas |
| Aparejo, alturas, planificación de puerta | `structure/layout.py` | Cálculo de intervalos y cotas sin crear mallas |
| Planos interiores y tabiques | `structure/floor_plan.py`, `structure/interiors.py` | Plan puro de estancias y conexiones antes de vanos; geometría de planta baja consume sus reservas |
| Fachada, pilares, paredes contiguas | `structure/walls.py` | Orquesta piezas; asigna wall_id |
| Integración del edificio | `structure/assembly.py` | Ordena derrumbe, huecos, apoyos, suelos, escaleras y cubierta antes del acabado |
| Derrumbe y continuidad espacial | `structure/destruction.py`, `structure/spatial.py` | Campo compartido entre muros y esquinas; retira piezas sin apoyo |
| Activación de daño | `structure/damage.py` | Vista de lectura que neutraliza daño sin escribir ajustes RNA; generación y runtime consumen esa vista |
| Ventanas, alojamientos y vigas | `structure/openings.py` | Recorta antes de añadir carpintería; exige apoyos |
| Reserva de escalera y contactos | `structure/placement.py`, `structure/relations.py` | Evita vanos sobre el macizo y conserva mampostería junto a la carpintería |
| Agujeros de daño | `structure/holes.py` | Perfora la fábrica montada respetando madera y contactos reservados |
| Suelos y entreplanta | `structure/floors.py` | Tablones cerrados sobre apoyos; cotas comunes de `config` |
| Escaleras | `structure/stairs.py` | Reserva huella y desembarco; acabado propio para piedra y madera |
| Tejado, tejas y hastiales | `structure/roof.py` | Paños sobre cerchas supervivientes; perfil compartido de alero a cumbrera |
| Daño y escombros de cubierta | `structure/roof_damage.py` | Regiones reproducibles cortan estructura y cubierta; escombros asociados |
| Chimenea, canalones y bajantes | `structure/roof_accessories.py` | Planifica accesorios y sus reservas para integrarlos con muros y cubierta |
| Cajas, bisel, material, recorte plano, aplicación de modificadores | `geometry/primitives.py` | Mallas cerradas en mm; modificadores de pieza solo con `apply_modifier` (escena de taller) |
| Relieve de cal | `geometry/plaster.py` | Cuadrícula recortada, malla cerrada con borde conservado |
| Desgaste | `geometry/weather.py` | Erosión hacia dentro y densidad por calidad |
| Grietas y roturas | `geometry/fracture.py` | Semillas locales, grietas desde aristas, sin islas grandes |
| Tierra, peana, grava, asentamiento | `geometry/terrain.py` | Superficie física compartida con los escombros |
| Cúmulos de escombros | `geometry/rubble.py` | Construye y asienta piezas con huella suficiente |
| Puerta, marco, veta, herrajes | `geometry/timber.py` | Sección cerrada y orientación 3D coherente |
| Balcones, alféizares e hierro | `geometry/balconies.py` | Piezas cerradas ancladas a los tramos; vanos libres |
| Materiales y veta visual | `geometry/surfaces.py` | Paletas compartidas y UV; el bump visual no se exporta como relieve |
| Instancias de mampostería | `geometry/instances.py` | Variantes compartidas en Geometry Nodes; materializa copias para exportación |
| Agrupación de vista previa | `geometry/batching.py` | Agrupa sin fusionar sólidos; conserva IDs, UV y materiales |
| Generación y métricas | `services/generation.py` | Validación → caché/construcción → daño → métricas |
| Caché | `services/cache.py` | Plantillas anteriores a grietas, copiadas antes de editar |
| Fusión/exportación | `services/export.py` | Fuente intacta; valida componentes del sólido |
| Ensayo físico de tabique | `services/physics.py` | Cajas en metros por estancia; poses aceptadas se aplican fuera de caché antes de agrupar/exportar; firma bloquea resultados obsoletos |
| Ensayo de edificio completo | `services/structural_physics.py` | Copias sin aglutinante, componentes separados, encajes booleanos y uniones por proximidad; colisiones de malla en metros, sin aceptación para impresión |
| Cálculo físico aislado | `services/physics_jobs.py`, `services/physics_worker.py` | Preparación, simulación y exportación en otro Blender; vigilancia de recursos y reproducción sin cuerpos rígidos |
| Exportación tras física | `services/physical_export.py` | Copias del fotograma en mm; unión vóxel explícita, cierre y STL binario; permite escombros desconectados |
| Revisión previa a física | `services/geometry_audit.py` | Auditoría de mallas y variantes; no valida contactos ni construye colisionadores |
| Medición | `services/profiling.py` | Decorador acumulativo por etapa |
| Propiedades guardadas | `ui/settings.py` | Mantener identificadores RNA compatibles; los nombres visibles son cortos y el detalle va en `description` |
| Preferencias del complemento | `ui/preferences.py` | Umbrales de pausa, unidades y fusión; `preferences.value()` con respaldo en `config` si no está activado |
| Temporizadores de edición | `ui/preview.py` | Debounce, modo rápido y protección busy |
| Acciones | `ui/operators.py` | Operadores delegan en servicios |
| Panel, subpaneles y menú Añadir | `ui/panel.py` | Subpaneles generados desde `config.SECTIONS`; `draw()` solo lee (JSON memorizado) |
| Ciclo de vida | `registration.py` | Limpia versión anterior, registra clases y handlers de carga/deshacer |

## Flujo

`UI → preview → generation → walls → assembly → geometry`

`assembly` resuelve derrumbe, ventanas/vigas, contactos, agujeros, suelos/escaleras y cubierta en ese orden. `roof` comparte el perfil de `spatial` y consulta reservas de chimenea y regiones de daño antes de colocar piezas.

`generation → cache` almacena geometría antes de `fracture.apply_damage` o `instances.build`. La agrupación de vista previa se hace al final y nunca se guarda como plantilla.
`export.make_solid` reconstruye la fuente si estaba agrupada, materializa las instancias y fusiona copias. Valida la triangulación imprimible; puede normalizar por vóxel si la unión exacta no triangula cerrada.
Todos los módulos consultan `runtime` para calidad, parámetros activos y temporizadores.
Los imports explícitos de módulos hacen visibles las dependencias. El ciclo entre generación y exportación solo referencia funciones en ejecución, no genera objetos al importar.

La API de `__init__.py` carga servicios de Blender al llamarlos. Por eso `config`, `runtime` y `structure/layout` se pueden importar desde Python normal para ejecutar pruebas rápidas.

## Editar un parámetro

1. Declara la propiedad RNA en `ui/settings.py`.
2. Añádela a `config.FIELDS` si afecta generación; esto también instala el callback e incluye la propiedad en la firma de caché.
3. Inclúyela en `config.SECTIONS` para mostrarla: cada entrada es un subpanel (`toggle` = casilla en su cabecera, `closed` = plegado). Si es un enum de 2-3 opciones, añádela a `EXPANDED_ENUMS` o `FULL_WIDTH_ENUMS`. Nombre visible corto; el detalle, en `description`.
4. Modifica solo el módulo que consume el parámetro. Si es daño reaplicable, revisa conscientemente `CRACK_FIELDS`; excluir un campo incorrecto puede mostrar geometría antigua.
5. Comprueba dos valores y una regeneración con caché; conserva el valor anterior si estás migrando datos guardados.

## Contratos delicados

- Los nombres de piezas entran en la semilla CRC de las grietas. Renombrar puede cambiar el resultado visual.
- Al tallar huecos: actualizar mesh/depsgraph del cortador, recalcular normales, eliminar directamente piezas totalmente contenidas. Omitirlo produjo bloques con la forma del cortador.
- Nunca uses `from runtime import quality` para estado mutable: quedaría una copia local del valor.
- Para conservar partidas de aleatoriedad, usa `random.Random(seed)` local; no cambies el orden de llamadas durante un refactor sin comprobar diferencias.
- Campos internos heredados de giros siguen presentes para leer .blend; los perfiles públicos los derivan.
- Las plantas miden 55 mm; cimentación a 2 mm, entreplanta a 57 mm y coronación de dos plantas a 112 mm. Usa `config.FLOOR_PITCH`, `UPPER_FLOOR` y `BEAM_LEVEL` para que escaleras, vigas y suelos coincidan.
- Los perfiles Tabique/Pared/Muralla tienen espesores de 6/9/15 mm; no reutilices las dimensiones anteriores a la base completa.
- Borrador y Trabajo omiten el daño fino según `config.DAMAGE_QUALITIES`. Las pruebas de cierre y caché deben incluir las variantes y transformaciones de Geometry Nodes; los puntos del array por sí solos no prueban la geometría visible.

## Localización económica

`python dev.py find ventana`, `python dev.py find cache`, `python dev.py find timber_beam`.
El índice se calcula desde AST sin importar Blender y sin un archivo duplicado que pueda quedar desactualizado.

El laboratorio acotado vive en `services/masonry_physics.py`: piezas activas independientes, colisiones primitivas, retirada múltiple, suelo y proyectil. No consume ni modifica la geometría de la casa. Los controles se guardan en RNA y no afectan la caché de generación.

`services/impact_physics.py` controla lanzamiento, empuje y prefractura del laboratorio en metros. No modifica geometría fuente ni depende de UI. `ui/operators.configure_view` y `frame_view` ajustan recorte y encuadre según cotas de la escena, excluyendo el suelo de seguridad.
