# Estado del proyecto

## v0.32.19 — 2026-10-21

Reparada la triangulación de revocos y limitada la limpieza al plano de fractura; separados contactos Perlin puntuales antes de extruir. 48 combinaciones de semilla/daño verificadas. `repro_revoco_error.blend` preparado en 222,485 s: 3.960 cuerpos, 15.852 uniones, 167 fragmentos frágiles y ninguna pieza activa desconectada; reapertura y render verificados, no simulación completa. Vigas sin alojamientos traseros cuando terminan en cabecero; escalera superior de piedra hueca, vuelo de losa y seis muestras con 35 mm libres sobre desembarcos. Tejas rígidas ante hundimiento. Tres luces coloreadas, seguimiento de cámaras, materiales métricos y copia a reproducción. Manual y límites en `V03219.md`; entramado exterior y refinamiento artístico de fracturas siguen pendientes.

## v0.32.18 — 2026-10-20

Postes del desembarco junto al muro y travesaños inferiores. La regresión incluye los apoyos de la propia escalera contra todas las huellas, además del forjado: tres tramos, alturas distintas y ambos sentidos. Alcance y limitación de validación física en `V03218.md`.

## v0.32.17 — 2026-10-19

Reserva de escalera por planta, incluido desembarco y ancho de vigas; cabecero prolongado y postes de llegada retranqueados. Prueba de tres plantas en ambos sentidos, sin cruces volumétricos de vigas/postes de forjado contra peldaños o desembarcos. Uso y alcance en `V03217.md`.

## v0.32.16 — 2026-10-19

Escaleras con número de peldaños por desnivel, huella y contrahuella editables; valla por vanos sin postes duplicados; barrotes sobre plataforma. Cancelas de balcón, marco interior y tejadillo; ejes exactos de vanos y mortero retranqueado. Torreón con daño localizado y retirada de losas/parapetos sin apoyo. Corregidas unidades del selector de zona. Preparaciones completas de madera y piedra: 2.524/3.222 cuerpos, sin piezas inicialmente desconectadas; cierre, caché y regresión general verificados. No certifica todas las semillas ni simulación completa de ambos ejemplos. Uso y límites en `V03216.md`.

## v0.32.15 — 2026-10-19

Selección elipsoidal por pieza maestra o cursor, porcentaje del centro hacia fuera y acumulación de focos. Liberar uniones reactiva explícitamente las colisiones de las parejas afectadas. Ensayo de caja sobre apoyo pasivo durante 120 fotogramas y pruebas de selección. No certifica todavía el caso completo del usuario ni propagación por pérdida de apoyo. Uso y límites en `V03215.md`.

## v0.32.14 — 2026-10-18

Distribución de vanos por planta y reservas para tejadillos; derrumbe inicial suavizado, cubierta asentada sobre apoyos medidos y pérdida de tejas por regiones. Revoco de miradores con variación local y refinamiento limitado. Cinco intensidades verificadas visualmente y con mallas cerradas. Flujo integrado con 3.180 cuerpos, 512 piezas seleccionadas y diez fotogramas hasta STL cerrado: preparación 1.134 MB, simulación 1.001 MB y exportación 3.044 MB de pico del trabajador. El asentamiento del generador es procedural; no certifica estabilidad estructural ni todas las semillas. Medidas y límites en `V03214.md`, uso en `MANUAL_V03214.md`.

## v0.32.13 — 2026-10-17

Miradores agrupables con revoco claro y daño Perlin independiente, hojas con postura editable y tejadillos cerámicos. Perfil longitudinal/asimétrico compartido con accesorios. Prefractura del relieve triangulada antes del corte para conservar volumen. Regresión de cuatro casos, cierre/caché de fachadas y flujo completo de 3.101 cuerpos hasta STL cerrado verificados. Medidas y límites en `V03213.md`; uso en `MANUAL_V03213.md`. Las hojas no son bisagras Bullet; la fractura no es adaptativa durante el impacto. El ejemplo selecciona 512 piezas y calcula diez fotogramas, sin certificar un derrumbe completo asentado.

## v0.32.12 — 2026-10-16

Torreón de terraza/parapeto/almenas, tres plantas y forjados por cota, cuotas independientes de balcones y ventanas, cimientos/patio, daño asimétrico compartido de cubierta y corrección de falsos encajes. Zarandeo de diez fotogramas sobre selección, cámaras conservadas y resistencia por familias. Prueba integrada hasta STL con 2.048 piezas seleccionadas; límites y mediciones en `V03212.md`, uso en `MANUAL_V03212.md`.

La torre conecta las tres plantas y la terraza mediante tres tramos, huecos y desembarcos; acceso a terraza abierto, sin tapa. Corregido el límite interno de altura y los refuerzos que cruzaban vanos. El descriptor arquitectónico inicia la migración del briefing. Aún no hay reconstrucción local por regiones sucias, materialización física parcial ni genealogía semántica de todos los fragmentos. Preparar sigue procesando la casa completa. Habitaciones solo en planta baja, terrazas sin drenaje propio, sin mortero reconstruido ni fractura adaptativa. Diez fotogramas no validan un derrumbe asentado ni la impresión del STL.

## v0.32.11-r2 — 2026-10-14

Escala interna de colisión para evitar el pico de memoria de las miniaturas,
sin cambiar dimensiones del generador o de la reproducción. Caso de arranque
con 5.192 cuerpos / 4.121 activos: 1.533 MB medidos, frente a más de 4 GB antes.
Madera dañada en tramos rectos, selección por porcentaje y altura, vanos de
balcón independientes, vigas sobre juntas y hastial con daño Perlin.
La revisión r2 reconstruye la entrega con fuente y laboratorio coincidentes,
comprueba medidas de puertas y ventanas y distingue la compilación en el panel.
El trabajador omite residuos de piedra recortada menores de 0,2 mm en todos
los ejes: uno de ellos atravesaba el suelo pese a completar el cálculo.
Validaciones y límites: [v0.32.11](V03211.md).

## v0.32.10 — 2026-10-12

Corregida la triangulación del ladrillo que impedía preparar la casa y el
encaje de cerámica contra chimenea. Caso real preparado: 2.204 cuerpos,
6.317 uniones. Proyectiles con vencimiento reversible y cubierta con
hundimiento previo al desprendimiento. [Uso, pruebas y límites](V03210.md).

## v0.32.9 — 2026-10-10

Alturas independientes, ventanas/balcones repartidos, pilares equidistantes o
manuales y cancelas sin aplastamiento. Prefractura cerrada de revocos/chimenea
sobre copias físicas, con conductos huecos conservados y límite de 256 fragmentos.
Pruebas de reposo/impacto, casa real y exportación de la reproducción reabierta.
Uso y límites: [V0329.md](V0329.md). No se certifica todavía la casa máxima con
esta nueva prefractura ni fractura adaptativa al impacto.

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

## 0.32.8 — 9 de octubre de 2026

Los cruces metálicos de los balcones se conservan como soldaduras sin colisión mutua; no se restan tubos finos entre sí. La preparación prioriza la escalera de piedra ante rastreles y reintenta encajes numéricamente problemáticos desplazando solo el cortador temporal unas milésimas de mm. La fuente permanece intacta.

Preparación, simulación y exportación se ejecutan en otro Blender con arranque de fábrica, cancelación con Esc y vigilancia de memoria/tiempo (4.096 MB residentes y 20 minutos, comprobados periódicamente). Un fallo nativo del hijo no se ejecuta dentro del Blender de edición. La reproducción conserva escalas, modificadores evaluados y poses cada cuatro fotogramas con interpolación lineal. El ensayo heredado de tabiques conserva su aceptación sobre la casa.

Carga medida: casa de 240 × 240 mm y dos plantas, calidad Trabajo, 390.980 caras expandidas al generar; 4.779 cuerpos y 16.622 uniones al preparar. Tras agrupar terreno y reducir contactos, ensayo con 4.110 cuerpos totales y 2.048 móviles incluido el proyectil: 96 fotogramas, 2.036 objetos animados, 1.102 s y pico de 3.020 MB. Balcones torcidos/partidos: prueba separada con 72 soldaduras. La simulación completa y la variante con 3.000 cuerpos móviles superaron el límite de memoria al arrancar el segundo fotograma. No hay garantía para otras combinaciones; la reducción de contactos modifica la rigidez artística.

Exportación por bloques del fotograma 96 a 0,50 mm: 6.437.706 triángulos, 46 s y 2.323 MB. Comprueba cierre, orientación y volumen antes de escribir. La unión a 0,35 mm de esta casa supera el límite de memoria. El remallado puede perder detalles finos y conserva escombros desconectados; no reconstruye mortero arquitectónico.

Límites de cobertura: en este caso máximo, chimenea y bajantes estaban activadas pero sus reglas de colocación no generaron piezas. No queda probada su física en esta carga, ni la calidad Detalle. El movimiento observado es principalmente asentamiento; este ensayo no demuestra derrumbe generalizado ni rotura adaptativa. Informes `reports/stress_max_*.json`; uso y alcance en `docs/MANUAL_CARGA_MAXIMA.md`.
