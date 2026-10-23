# Esquema 3 — mundo, arriostramiento y evento

## Corrección de escala

V2 no distinguía volumen de miniatura y volumen del edificio representado. El trabajador físico existente convierte mm a m y emplea multiplicadores numéricos propios: eso no demuestra similitud estructural 1:60. No se reutilizan sus masas como masas estructurales.

V3 exige `quantity_frame=world`: longitudes en mm de mundo, áreas mm², volúmenes mm³, masa kg, fuerzas N y momentos N·mm. `units.to_world(valor, dimensión, escala)` es la frontera geométrica. La escala debe ser explícita, positiva y finita; no se asume 60. El adaptador nominal todavía carece de volúmenes medidos: los mantiene desconocidos y no inventa una escala del edificio.

La prueba representa un pilar de mundo de 300 × 300 × 3000 mm con densidad 2200 kg/m³ a 1:30 y 1:60: en ambos casos obtiene 594 kg, 90.000 mm² y 0,064746 MPa bajo su peso. Cambiar λ sin cambiar la geometría de miniatura representa otro edificio y no debe conservar la tensión.

Los modelos v2 no se reinterpretan silenciosamente: el validador exige versión 3. Una regeneración reconstruye el adaptador nominal; para migrar medidas antiguas hace falta saber en qué escala se obtuvieron. Las propiedades dentro de `properties` siguen siendo registros heredados, no magnitudes estructurales verificadas.

## Relaciones y demanda

ARRIOSTRADO_POR invalida los elementos lateralmente dependientes, pero no cuenta como apoyo vertical ni introduce ciclos en el orden de regeneración. `braced_by` es una vista derivada, igual que `rests_on`. Las relaciones nominales nacen INTACTO; ASENTADO queda disponible para el grafo del resultado. Aún no se identifica automáticamente el contacto final desde Bullet.

Cada elemento dispone de `demanda_lateral_N`, dirección lateral, capacidad por modo, energía absorbible y modo de fallo. Compresión, tracción y cortante usan N; flexión usa N·mm. El momento resistente no se calcula como resistencia por área: requiere módulo resistente y orientación. Los campos desconocidos no constituyen una aceptación mecánica.

El evento conserva pico en kPa e impulso en kPa·s, más dirección normalizada. No genera una explosión ni decide una rotura. Igual pico con distinto impulso conserva dos acciones distintas. `collapse_override=AUTO/ALLOW/BLOCK` separa decisión artística de una futura regla energética; el booleano heredado se conserva pero no se activa como modelo energético.

## Revisión de las tablas recibidas

Fuente: documento del usuario «Ruinas tabla mínima de materiales y revisión del esquema v2». Se leyeron ambas tablas y sus notas. Todos sus valores siguen en C. No se trasladan a umbrales de Bullet ni se presentan como verificados.

- Madera: separar orientación de fibras, especie, humedad y calidad. El Wood Handbook de USDA explica que muchas tablas corresponden a probetas pequeñas, limpias y de fibra recta, no a vigas antiguas con nudos. No justifica elevar a B automáticamente los valores genéricos TIMBER_SOFT/HARD.
- La densidad actualmente compartida tampoco distingue madera blanda/dura, conjunto de mampostería, vidrio y carpintería mixta. Las filas mecánicas necesitan esa correspondencia explícita; no duplicar densidades en otra tabla.
- Terreno rígido y capacidad limitada de apoyo son dos modelos diferentes: hay que escoger el activo para cada prueba.
- Fricción por material no determina una pareja: falta definir y verificar la regla de combinación. Restitución y capacidades de fijación siguen pendientes de calibración.
- El factor dinámico 2 no es universal para cualquier caída. Debe quedar como hipótesis acotada. Comparar m·g·h con energía absorbida requiere desplazamiento/curva de resistencia y energía cinética de entrada; capacity_N por sí sola no proporciona julios.
- Los límites por presión deben mantenerse como referencias artísticas C hasta considerar duración, área, arriostramiento y geometría del elemento.

Fuentes primarias consultadas:

- USDA Forest Products Laboratory, Wood Handbook, capítulos 5 y 7: https://research.fs.usda.gov/fpl/wood-handbook — aplicabilidad de propiedades y calidad de madera; no valida aún las cifras del documento.
- DHS, Buildings and Infrastructure Protection Series 06, sección 3: https://www.wbdg.org/FFC/DHS/bips_06.pdf — impulso como integral presión-tiempo y limitación del pico aislado. Respalda la separación del esquema, no los umbrales de material propuestos.

## Aceptación y pendientes

31 pruebas puras aprobadas, incluyendo escala e independencia entre apoyo vertical, arriostramiento e impulso. Integración en tres plantas y caché mediante `tests/blender_construction_core.py`. Los cuatro casos de regresión conservaron sus digests geométricos. Sin sustitución de ZIP.

No se declara cerrada la calibración mecánica ni la familia de vigas: siguen pendientes fuentes por valor, capacidades/áreas reales, aplicación de envejecimiento y comparación BALANCED/PRECISE.

## Catálogo materials-0.1.0-C

Las dos tablas recibidas se registran en `config_materials.py`. `construction_core.materials` expone unidad, rango, confianza C y procedencia por campo. Las densidades se consultan en la tabla existente, con correspondencia provisional; vidrio, revoco y carpintería mixta quedan sin densidad resuelta. Los valores n/a no se convierten en resistencia infinita. La flexión del hierro tampoco recibe arbitrariamente el valor de tracción.

La firma SHA256 incluye datos, densidades referidas y procedencia. Se integra en la clave de caché y en el modelo constructivo. Un cambio de dato exige nueva versión de catálogo y registro de cambios. No se ha creado ni sustituido ningún ZIP en esta entrega; la identidad es esquema 3, catálogo materials-0.1.0-C y commit Git.

La variabilidad usa SHA256(seed, element_id), lognormal con normal latente truncada a ±2 sigma y RNG local. La media uno corresponde a la distribución anterior a truncar: no se garantiza media exactamente uno tras truncado. Se prueba repetición, cambio de semilla, límites y conservación del RNG global. No se aplica aún a uniones reales. Los rangos de edad se conservan como datos C, sin convertir automáticamente antigüedad en pérdida uniforme de resistencia.

La aceptación devuelve campos desconocidos y número de valores C del camino crítico: ninguna tabla provisional certifica una familia. Queda por medir un encuentro viga-muro y contrastar su comportamiento antes de conectar capacidades con Bullet.
