# Estado del proyecto

## v0.32.5 — 2026-10-08

Tablas interiores continuas con travesaños y ensayo experimental del edificio
completo, sin mortero físico, con recortes de encuentros y uniones rompibles.
Conserva la fuente y añade reproducción horneada con vista interior separada.
No reconstruye todavía mortero imprimible tras la simulación.
Validación y límites: [V0325.md](V0325.md). Uso: [MANUAL_ESTRUCTURA.md](MANUAL_ESTRUCTURA.md).
Entrega: `dist/ruinas_v0325_estructura_interactiva.blend`.

## v0.32.4 — 2026-10-06

Relieve geométrico de madera y cal; física por estancia con aceptación de poses
antes de exportar. Ejemplo completo reabierto y STL reimportado, ambos validados.
Alcance limitado a tabiques y suelo plano: [V0324.md](V0324.md).
Entrega: `dist/ruinas_v0324_proceso_completo.blend`.


## v0.32.3 — 2026-10-06

Corregidos el grosor real del perfil Tabique, la variación ignorada en muros
laterales/trasero y controles activos sin efecto. Primer ensayo físico separado
con secciones recuperables también desde vista agrupada. Validación y límites
en [V0323.md](V0323.md). Todavía no hay uniones ni derrumbe estructural simulado.
Entrega actual: `dist/ruinas_v0323_completo.zip`.

## v0.32.2 — 2026-10-05

Tabiques seccionados, cuartos útiles de 60 × 60 mm, circulación de 35 mm y
reparación local de caras degeneradas. Diagnóstico comparativo, pruebas y límites
en [V0322.md](V0322.md). La revisión de todas las mallas del caso completo queda
en `reports/physics_readiness.json`; no se certifican aún contactos físicos.

La desviación del mortero de 0,01 mm no resolvió las 125 caras degeneradas del
caso reproducido; la soldadura local de 0,00001 mm sí, conservando cotas. Sigue
pendiente el problema independiente de fragmentos desconectados al exportar.

## v0.32.1 — tabiques de madera

Tabiques con juntas y veta geométrica por ambas caras, sin booleanas ni tablas
sueltas; espesor mínimo 2,3 mm. Veta responde a `wood_grain` sin cambiar topología.
Pruebas de triangulación, cierre, espesor y dos orientaciones en
`tests/blender_wood_panel.py`; integración y caché en los tres planos correctas.
Caso de tres estancias: 276.327 → 283.159 caras expandidas (+2,47 %),
5,62 → 5,67 s en la medición realizada con los mismos ajustes. No es un benchmark
de rendimiento estadístico. Pruebas generales sin cambios en sus referencias.

Estudio de alternativas en [DESTRUCTION_STUDY.md](DESTRUCTION_STUDY.md):
se recomienda evaluar módulos semánticos por plantas y física sobre copias
simplificadas. No se ha cambiado el exportador ni implementado esa física.

Entrega actual: `dist/ruinas_v0321_completo.zip`; addon `ruinas_panel_v0321.zip`.

## v0.32 — 2026-10-04

Tejas alineadas y orientadas por pendiente, encuentro cerámico de chimenea,
canalización por secciones y primeros planos interiores de planta baja.
Pruebas, entrega y límites en [V032.md](V032.md). Los apartados siguientes
describen entregas anteriores; el solape de tejas se ha corregido en los casos
ensayados de esta versión. El daño unificado y el grafo de apoyos siguen pendientes.

## Activación independiente del daño — 2026-10-04

Nuevo control «Activar daño» en Acabado. Desactivarlo neutraliza derrumbe,
agujeros, roturas de suelo/cubierta/madera, desgaste, grietas, hierro dañado y
escombros sin borrar intensidades ni semillas guardadas. Por defecto permanece
activo, incluidos archivos anteriores. La calidad sigue regulando el acabado:
Borrador y Trabajo no calculan las grietas finas de Detalle.

Validación: `dev.py check`, `dev.py test` (cuatro escenarios sin cambios en sus
referencias) y `tests/blender_intact.py`: diez semillas de habitación de una planta,
80 × 70 mm, repartidas entre las tres calidades, con cubierta, ventanas, bajantes
y chimenea alterna. Piezas cerradas y caché reproducible; apagar/encender/apagar
recupera la geometría intacta. Informe y vista en `reports/intact_buildings.*`.

Esto no valida todavía diez tipologías, todos los apoyos ni un sólido fusionado
imprimible. La revisión visual confirma que el solape de tejas sigue pendiente.
El modelo previo de construcción, campo común de daño y grafo de apoyos siguen
en la hoja de ruta; este interruptor es su primera base de comparación.

## 0.31 completa — revisión de la casa aportada

La base actual procede del addon incluido en `dist/ruinas_v031_completo.zip`, aportado
por el usuario después del primer push 0.31. Es una línea más avanzada: incluye
plantas de 55 mm, grosores 6/9/15 mm, balcones, suelos, escaleras, cubierta y geometría
instanciada. Se han incorporado sus módulos a `src/ruinas_panel/`; los apartados
anteriores se conservan como historial, no describen esta nueva base completa.

Revisión terminada: chimenea desde planta baja con hogar abierto, campana, conducto
hueco y leños carbonizados; reserva de paso por forjado y cubierta; babero y peto.
Las tejas y la cumbrera tienen sección de media caña y espesor. Los hastiales tienen
revoco de 3,2–5 mm retranqueado y entramado visible. Las huellas de piedra tienen
relieve físico y cantos gastados, conservando apoyo central de 20 × 20 mm y acceso
de 35 mm. Se conserva el modo de desgaste Personalizado del repositorio.

Validación en `docs/HOUSE_REVISION.md`. Piezas nuevas cerradas, conducto libre y
caché reproducible; no se entrega un sólido fusionado de la casa completa.
Límites heredados y reproducidos contra el ZIP: caras de área inferior a 1e-8 mm²
en algunos escenarios y rechazo de fragmentos aislados al fusionar ciertas ruinas
dañadas. La chimenea se coloca solo si hay un tramo conservado sin vanos ni escalera;
puede quedar desactivada geométricamente si no existe ese espacio.

## 0.31 — desgaste y controles (2026-09-28)

Desgaste reforzado con amplitud progresiva, límite de erosión principal según el tamaño
de pieza y grano que no satura antes del máximo. El refinado ocurre antes de deformar:
no cambia el objetivo de 0,22 mm, pero sí la topología respecto a versiones anteriores.
Nuevo modo Personalizado: conserva `wear` entre generaciones, incluidos 0 y 1. Los tres
presets y las claves RNA existentes se conservan. Borrador y Trabajo siguen omitiendo
desgaste, grietas y escombros por diseño.

Validación en Blender 5.2.2: cuatro escenarios, caché, ciclo de vida y sólido conectado;
sin nuevas caras degeneradas en los escenarios de regresión. Prueba adicional de
desgaste personalizado 0/0,55/1, cierre y exportación al máximo. Comparación visual y
mediciones en [WEAR_031.md](WEAR_031.md). No se ha validado cada combinación ni impreso
la nueva erosión. La geometría de Detalle cambia al regenerar archivos antiguos.

Las cinco prioridades constructivas acordadas quedan en [ROADMAP.md](ROADMAP.md);
no se añaden cubiertas ni destrucción regional en 0.31.

## Antecedentes y límites

Base: v0.20, convertida a paquete modular v0.21. El usuario prioriza modelos lowpoly, mampostería coherente y edición fácil. Actualización (2026-09-25): el destino es la impresión en resina, así que se prioriza el detalle imprimible y se aceptan cambios de geometría revisados.

Ya existe: perfiles Tabique/Pared/Muralla; ruina baja/una/dos plantas; Ninguna/L/U/Habitación; ventanas por pared con apoyo; puerta de madera con picaporte; vigas alojadas; derrumbes escalonados; daño de agujeros, grietas ramificadas; tierra/grava y escombros asentados.

Límites conocidos: el coste de subdivisiones, operadores y booleanos sigue siendo alto al regenerar habitaciones. Modularizar no elimina ese coste. Borrador omite grietas finas. No hay suelo de tablones, cubierta, simulación física completa de escombros ni ensamblaje mecánico de módulos.

Las alturas 27/52/102 mm son presets de diseño, no garantías sobre reglas oficiales de juegos. No se ha hecho una prueba física de impresión.

Límites demostrados en Blender 5.2.2 (2026-09-25; detalle en `docs/AUDIT.md`), heredados de v20:

- En L/U/habitación, las grietas de las paredes de retorno se tallan en la cara de junta. Resuelto después: se tallan en la cara exterior de cada tramo, con trazo quebrado que se afina.
- Una grieta puede dejar una piedra reducida a una esquirla (`door_windows_work`, `hilada 06.05`). Resuelto después: se revierte la rama si el booleano quita más del 25 % del volumen.
- «Preparar sólido» reutiliza la geometría de vista previa si ambas calidades coinciden. Resuelto después: la caché se separa por modo; la primera exportación tras una vista previa reconstruye (+40–80 % de tiempo).
- La primera generación tras cargar otro archivo falla con `ReferenceError`. Resuelto después: handlers de carga y deshacer sueltan las referencias.
- El coste de cada bisel crece de forma lineal con el número de objetos (2 ms → 47 ms), así que el total es cuadrático. Resuelto después: los modificadores se aplican en una escena de taller (habitación en Borrador: 74 s → 7 s, misma geometría).

Borrador y Trabajo muestran solo la estructura; desgaste (tres niveles), grietas y escombros aparecen en Detalle. El derrumbe tiene silueta irregular dependiente de la semilla.

El sólido exportable se une con Manifold y conserva el detalle de la fuente (antes, el remallado vóxel de 0,32 mm borraba grietas y vetas).

Las pruebas de migración están en `reports/`; los resultados históricos de cierre de malla v20 están en `../outputs/muro_20`. Para cambios posteriores de geometría debe renovarse la validación correspondiente.

## 0.32.6 — 8 de octubre de 2026

Ensayo acotado de mampostería seca: muro/torre, hasta 256 ladrillos activos independientes, retirada múltiple y piedra bajo gravedad, con suelo pasivo. Archivo reproducible y manual en docs/MANUAL_LADRILLOS.md. Corrige selección múltiple de uniones en el laboratorio estructural anterior. El ensayo acotado todavía no extrae zonas de la casa ni fractura internamente los ladrillos; no reconstruye mortero imprimible. Validación: tests/blender_masonry_physics.py y blender_masonry_reopen.py, además de las regresiones existentes.

## 0.32.7 — 9 de octubre de 2026

Corrección de recorte y encuadre al pasar entre generador en mm y laboratorio en metros. Preparar casa deja de crear inadvertidamente el ejemplo; este tiene botón independiente. Impactos múltiples dirigidos y empuje cinemático, suelo de seguridad bajo la casa, zona móvil limitada por selección y prefractura acotada de piedras con juntas rompibles. La prefractura usa dos mitades oblicuas, no fractura adaptativa. El empuje prescribe movimiento, no fuerza calibrada. Aún sin reconstrucción imprimible del mortero. Manual: docs/MANUAL_IMPACTOS.md.

Validación 0.32.7: casa completa de 1.549 cuerpos tras preparar 16 ladrillos en 32 fragmentos; 29 fragmentos se desplazan en el impacto calculado, fuente intacta. Reapertura sin autorun y auditoría de cierre de todas las mallas del laboratorio. Vista de la casa: distancia 332 unidades mm, recorte adaptativo; laboratorio: distancia 0,378 m. Prueba pequeña de cohesión: deriva 0,021 mm en reposo y separación tras impacto. El cálculo de la zona acotada tarda unos 77 s en esta máquina. Dos residuos del tejado (0,200 y 0,049 mm³, espesor equivalente inferior a 0,01 mm) se excluyen de las copias físicas tras recortes.
