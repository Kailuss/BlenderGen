# Coherencia constructiva — primera integración, 2026-10-23

## Auditoría

El descriptor `building_definition.define` describe cotas y semillas; su grafo se construye después de las mallas y no gobierna la construcción. Las relaciones de cubierta son nominales, no contactos físicos. `openings` decide vigas mediante consultas al muro y reserva alojamientos; `floors` añade un bastidor alternativo si faltan anclajes; `stairs` vuelve a calcular reservas por tramo; `roof` comprueba sus cerchas por separado. `relations.register` reserva mampostería próxima a carpintería antes de agujeros, pero esa proximidad no demuestra transmisión de carga. Esta dispersión sigue siendo el problema principal.

## Incorporado

`construction_core/graph.py` no importa Blender. Consume elementos y relaciones JSON: SUPPORTED_BY, CONNECTED_TO y HOSTED_BY. Valida referencias, duplicados, tipos incompatibles, políticas y ciclos. Calcula orden de regeneración e invalidación de dependientes. Los contactos repetidos con el mismo elemento cuentan como un solo apoyo. La pérdida se evalúa según un mínimo explícito; si no hay política, se pide revisión y no se propaga una caída inventada.

`construction_core/adapter.py` lee el grafo nominal actual conservando sus identificadores. No añade resistencias ni interpreta los accesos o eventos de daño como apoyos. Los datos quedan en `scene['ruinas']`, claves `construction_model` y `construction_validation`, también después de restaurar caché. No cambia geometría, materiales, selección, RNA ni ajustes guardados.

La visualización inicial es una tabla HTML de elementos y apoyos declarados: ámbar significa información pendiente, azul relación nominal. No es todavía una coloración de objetos en el visor ni un certificado de estabilidad.

## Límites explícitos

- El adaptador aún no representa individualmente todas las vigas, cabeceros y postes, ni verifica sus superficies de contacto. Los forjados del grafo heredado describen niveles, no cada tablero portante.
- El mínimo de apoyos es una regla discreta. No mide luz admisible, área de asiento, material, voladizos, equilibrio o resistencia. No se asigna automáticamente a la casa real.
- La invalidación devuelve qué habría que regenerar; todavía no ejecuta regeneración selectiva ni modifica el caché geométrico.
- Los identificadores heredados de ventanas usan su posición ordinal. Son deterministas para la misma configuración, pero no garantizan identidad tras insertar otro vano anterior.
- Las reservas volumétricas y los conflictos de paso siguen en sus módulos actuales. El núcleo no sustituye aún esas reglas; no se considera cerrada la coherencia constructiva general.

## Siguiente integración necesaria

Convertir vigas, cabeceros, postes y forjados en elementos del plan previo a mallas; compartir una sola reserva de escalera por nivel entre vanos, alojamientos, tablas y cubierta de torreón. Después, resolver apoyos de ambos extremos y apoyos redundantes con dimensiones verificadas. Solo entonces activar reparación y daño causal, distinguiendo una dependencia inválida de una decisión artística explícita. El núcleo nuevo es infraestructura para ello, no una sustitución por excepciones adicionales.

## Verificación

Seis pruebas puras nuevas cubren redundancia, cascada, referencias inexistentes, ciclos, unión frente a apoyo, contactos duplicados, orden estable y política desconocida. La suite total pasó 25 pruebas; los cuatro casos geométricos conservaron su digest anterior. `tests/blender_construction_core.py` comprueba integración, regeneración desde caché y coste del validador en una casa de tres plantas. Resultados en `reports/construction_core.json`.
