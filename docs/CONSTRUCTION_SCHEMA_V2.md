# Paso 0 — esquema constructivo 2

Identidad de esta entrega: versión de esquema **2** más commit Git. No se reutiliza un ZIP de una versión anterior. La actualización de esquema no cambia el BUILD_ID del paquete todavía pendiente de entrega.

Cada elemento registrado por el adaptador tiene `id`, `kind`, `material`, `volume_mm3`, `mass_kg`, `rests_on`, `load_N`, `capacity_N`, `fragility_class`, `exposed_area_mm2`, `pozo_de_colapso`, `representation`, `print_parts` y `properties`. La representación semántica no requiere una malla. Varias entidades pueden referirse a una misma pieza imprimible sin fusionar sus identidades estructurales.

Las unidades son mm, mm³, mm², kg y N. La masa se deriva del volumen y las densidades centrales existentes en `config.PHYSICS_DENSITIES`; no incluye PHYSICS_MASS_SCALE ni PHYSICS_SOLVER_SCALE. Carga y capacidad no son impulsos: no se trasladarán directamente a `breaking_threshold` de Bullet. Esa conversión debe calibrarse con el paso temporal y la escala del solucionador en las pruebas de uniones.

`rests_on` se deriva de las relaciones SUPPORTED_BY: no es una segunda lista editable que pueda divergir. El validador detecta divergencias, magnitudes negativas/no finitas, materiales no registrados y masas incompatibles. `None` significa desconocido, mientras que cero es una cantidad medida nula. `pozo_de_colapso` arranca en falso; todavía no modifica el generador de daño. Fragilidad y área expuesta quedan reservadas pero no estimadas a partir de cajas envolventes.

## Criterio de hecho y límites del paso 0

- Aplicación del esquema al adaptador nominal y restauración desde caché: comprobada en casa de tres plantas.
- Pruebas puras de unidades y consistencia: 27 pruebas totales aprobadas.
- Materiales: se reutiliza la tabla de densidades actual. Falta centralizar y calibrar capacidades, fragilidad y el tratamiento heredado del revoco en el trabajador; no se considera terminada la tabla mecánica completa.
- Capacidad, carga, volumen y material de conjuntos nominales: desconocidos hasta registrar sus elementos físicos; no se deducen de su nombre.
- Comparación planificador–Bullet BALANCED/PRECISE y captura de apoyos: **pendiente** para la primera familia. Esta entrega no declara terminadas vigas, cabeceros o postes.

## Contrato para cada familia posterior

Registrar los elementos y los contactos con punto de aplicación, área y longitud de asiento. Rechazar el apoyo que no cumpla asiento mínimo. Registrar reparto de carga entre contactos, dirección de viguetas y cabeceros, y distinguir capacidad de la pieza de capacidad de su unión. La partición imprimible debe leer los mismos IDs sin definir el camino de cargas.

El triángulo de descarga a 45° y el empuje por ausencia de tirante serán reglas artísticas explícitas y acotadas, no certificados estructurales. Se conservarán soleras y tirantes como entidades aunque el detalle no requiera geometría imprimible.

Para declarar una familia hecha: esquema completo con datos conocidos o incertidumbre señalada; prueba de pérdida de apoyo contrastada con Bullet en ambos modos; comprobación de no propagación a elementos ajenos; captura del encuentro y del resultado; versión y manifiesto únicos. Un test de esquema o un render aislado no sustituye esta aceptación.
