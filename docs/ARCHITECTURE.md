# Mapa de edición

La versión 0.21 reorganiza v0.20. La geometría conserva sus algoritmos; el cambio principal es la mantenibilidad.

| Tema | Archivo en `src/ruinas_panel` | Contrato principal |
|---|---|---|
| Perfiles, campos, secciones, calidad | `config.py` | Constantes sin dependencia de Blender |
| Estado temporal | `runtime.py` | Única instancia por sesión; no persiste en .blend |
| Aparejo, alturas, planificación de puerta | `structure/layout.py` | Cálculo de intervalos y cotas sin crear mallas |
| Fachada, pilares, paredes contiguas | `structure/walls.py` | Orquesta piezas; asigna wall_id |
| Ventanas, alojamientos y vigas | `structure/openings.py` | Recorta antes de añadir carpintería; exige apoyos |
| Cajas, bisel, material, recorte plano, aplicación de modificadores | `geometry/primitives.py` | Mallas cerradas en mm; modificadores de pieza solo con `apply_modifier` (escena de taller) |
| Desgaste | `geometry/weather.py` | Erosión hacia dentro y densidad por calidad |
| Grietas y roturas | `geometry/fracture.py` | Semillas locales, grietas desde aristas, sin islas grandes |
| Tierra, peana, grava, asentamiento | `geometry/terrain.py` | Superficie física compartida con los escombros |
| Cúmulos de escombros | `geometry/rubble.py` | Construye y asienta piezas con huella suficiente |
| Puerta, marco, veta, herrajes | `geometry/timber.py` | Sección cerrada y orientación 3D coherente |
| Generación y métricas | `services/generation.py` | Validación → caché/construcción → daño → métricas |
| Caché | `services/cache.py` | Plantillas anteriores a grietas, copiadas antes de editar |
| Fusión/exportación | `services/export.py` | Fuente intacta; valida componentes del sólido |
| Medición | `services/profiling.py` | Decorador acumulativo por etapa |
| Propiedades guardadas | `ui/settings.py` | Mantener identificadores RNA compatibles |
| Temporizadores de edición | `ui/preview.py` | Debounce, modo rápido y protección busy |
| Acciones | `ui/operators.py` | Operadores delegan en servicios |
| Menú | `ui/panel.py` | Dibuja sin generar geometría |
| Ciclo de vida | `registration.py` | Limpia versión anterior, registra clases y handlers de carga/deshacer |

## Flujo

`UI → preview → generation → walls/openings → geometry`

`generation → cache` almacena geometría antes de `fracture.apply_damage`.
`export.make_solid` fusiona copias; nunca sustituye los originales editables.
Todos los módulos consultan `runtime` para calidad, parámetros activos y temporizadores.
Los imports explícitos de módulos hacen visibles las dependencias. El ciclo entre generación y exportación solo referencia funciones en ejecución, no genera objetos al importar.

La API de `__init__.py` carga servicios de Blender al llamarlos. Por eso `config`, `runtime` y `structure/layout` se pueden importar desde Python normal para ejecutar pruebas rápidas.

## Editar un parámetro

1. Declara la propiedad RNA en `ui/settings.py`.
2. Añádela a `config.FIELDS` si afecta generación; esto también instala el callback e incluye la propiedad en la firma de caché.
3. Inclúyela en `config.SECTIONS` para mostrarla. Las secciones desde índice 6 son avanzadas.
4. Modifica solo el módulo que consume el parámetro. Si es daño reaplicable, revisa conscientemente `CRACK_FIELDS`; excluir un campo incorrecto puede mostrar geometría antigua.
5. Comprueba dos valores y una regeneración con caché; conserva el valor anterior si estás migrando datos guardados.

## Contratos delicados

- Los nombres de piezas entran en la semilla CRC de las grietas. Renombrar puede cambiar el resultado visual.
- Al tallar huecos: actualizar mesh/depsgraph del cortador, recalcular normales, eliminar directamente piezas totalmente contenidas. Omitirlo produjo bloques con la forma del cortador.
- Nunca uses `from runtime import quality` para estado mutable: quedaría una copia local del valor.
- Para conservar partidas de aleatoriedad, usa `random.Random(seed)` local; no cambies el orden de llamadas durante un refactor sin comprobar diferencias.
- Campos internos heredados de giros siguen presentes para leer .blend; los perfiles públicos los derivan.

## Localización económica

`python dev.py find ventana`, `python dev.py find cache`, `python dev.py find timber_beam`.
El índice se calcula desde AST sin importar Blender y sin un archivo duplicado que pueda quedar desactualizado.
