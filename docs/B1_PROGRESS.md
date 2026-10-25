# B1 — trabajo en curso

## Segundo control aplicado — 25 de octubre de 2026

Se ha extraído el cálculo de fachada a `layout.front_courses` y el de retornos/trasera a `layout.return_courses`. El constructor `walls` consume ambos. Se conservaron operaciones, orden de los generadores aleatorios, semillas y nombres; las regresiones mantienen los cuatro digests existentes. `masonry_intervals` y `masonry_joints` permiten consultar las juntas sin construir mallas. El baseline ya no duplica el algoritmo de trasera ni lee el registro del constructor de fachada.

Decisión escrita sobre incertidumbre: se sustituye la propagación conservadora por dos clausuras, optimista y pesimista. `unsupported` contiene pérdidas confirmadas en ambas; `requires_review` solo la diferencia entre ellas. Un tablón con redundancia suficiente incluso si falla su apoyo incierto queda fuera de revisión. Se mantiene la prueba adicional donde, al retirar también el apoyo redundante, la incertidumbre sí alcanza al tablón y a su dependiente.

`floor_frame` inicia el esqueleto D1 solicitado: emparejamiento uno a uno de juntas dentro de tolerancia explícita, ejes ordenados y descartes informados, una viga con dos grupos por extremo y segmentos encadenados hasta cimentación y terreno. Los WALL son anfitriones, nunca apoyos de la viga. Cada segmento tiene banda y ancho nominales; su geometría y contactos se expresan con escala explícita. No se inventan masa ni capacidad cuando falta el volumen de la pieza. Todas las dimensiones del esqueleto son argumentos, no nuevos valores por defecto del edificio.

Validación actual: 44 pruebas puras; 18 comparaciones de juntas; tres esqueletos construidos con ejes de las casas del baseline (semillas 1/20/73), dos segmentos por caso. Cada segmento contiene piedras de la malla intacta. Retirar uno deja como pérdida confirmada únicamente su viga. El baseline guarda ejes, descartes, conteos y pérdida. No se afirma equivalencia con Bullet ni validación de contacto por raycast.

Sigue pendiente para cerrar B1.0: ampliar la equivalencia a vanos de assembly y fábrica dañada. Sigue pendiente para cerrar B1: integrar los consumidores geométricos, productores de escalera, forjado completo y demás criterios de la orden. El esqueleto es la prueba mínima de paso solicitada, no una entrega del edificio completo.

## Orden actualizada y decisión D1

Referencia: `Orden de trabajo B1 el forjado gobernado por el plan (1).docx`, recibida del usuario. D1 pasa a regir la implementación pendiente: apoyos localizados mediante WALL_SEGMENT, alojados en WALL mediante HOSTED_BY y con cadena vertical de apoyo hasta cimentación. Los segmentos se emitirán en concentraciones de carga, no por cada piedra. El informe deberá contar segmentos y ejes descartados. No se conecta todavía la retirada de piedras al campo de evento.

Los ejes deberán concordar en fachada y trasera dentro de la tolerancia del alojamiento; esta tolerancia de emparejamiento no es la tolerancia de regresión entre cálculo y malla. El baseline utiliza ahora 0,05 mm para fachada y 0,001 mm para trasera.

Corrección del alcance de la prueba: 53,4 y 108,4 mm son las cotas de vigas de los dos forjados elevados, bajo plantas a 57 y 112 mm. La tercera muestra, 163,4 mm, es `altura de muro (167) - 3,6`: una sonda cerca de coronación, no un tercer forjado ni una viga de terraza. El informe la identifica como `wall_top_probe`, sin número de planta. Se conservan 18 casos, pero no acreditan tres forjados.

Ajustes del núcleo: políticas `support_groups` y `minimum_supports` mutuamente excluyentes; incertidumbre propagada por dependencias de apoyo como `requires_review`, sin convertirla en pérdida confirmada. Continúan pendientes las pruebas con segmentos emitidos por el planificador real.

## Primer control, 24 de octubre de 2026

No es una entrega B1 terminada ni una nueva versión del complemento. No se ha cambiado la chimenea ni el trabajador físico.

La prueba `tests/blender_b1_joint_baseline.py` compara 18 combinaciones (semillas 1/20/73, tres cotas y fachada/trasera), con tolerancia de eje de 0,3 mm, sobre fábrica intacta en Borrador y antes de vanos. El informe distingue las dos fuentes: cálculo puro independiente para la trasera, intervalos nominales registrados por el constructor para la fachada. Esta última aún necesita extraerse a un productor puro; no se declara cerrado B1.0. No cubre desgaste en Detalle, vanos ni fábrica dañada.

Se incorpora B1.3 al núcleo:

- `support_groups`: lista de grupos `{id, members, minimum}`. Cada grupo exige conservar su mínimo de apoyos únicos. Todos los apoyos deben estar declarados mediante `SUPPORTED_BY` y cubiertos por algún grupo. Un mismo apoyo puede participar en dos grupos si existen dos contactos funcionalmente distintos.
- `minimum_supports` sigue siendo la abreviatura de un solo grupo cuando no hay grupos explícitos. Sin ninguna política, el resultado sigue siendo «requiere revisión».
- Un grupo vacío, mínimo imposible, referencia no declarada o identificador repetido se rechaza. La pérdida también rechaza políticas inválidas aunque no se haya retirado aún un miembro del grupo.
- La suma de `load_share` conocidos en contactos `SUPPORTED_BY` de un elemento no puede superar uno (tolerancia numérica 1e-9). Los valores desconocidos siguen siendo desconocidos; no se impone que el reparto esté completo.

Pruebas: extremos independientes de viga, redundancia de tablones, cascada poste–cabecero–viga, grupos inválidos y reparto agregado. Esto comprueba el planificador; no es una comparación con Bullet. La geometría actual todavía no emite estos grupos.

Pendientes de la orden: productor puro completo de aparejo, cajas y ajustes de escalera con productor único, `floor_frame`, consumo geométrico del plan, eventos de omisión, contactos plan–raycast, A2 de tensiones sobre asiento, campos críticos, variabilidad efectiva, banco de calibración Bullet y consolidación de densidades/caché/documentación. No se altera la física para anticipar resultados del banco.

Incidencia de chimenea recibida durante este trabajo: `INCIDENCIA_CHIMENEA_2026-10-24.md`. Se conserva separada para no mezclar su diagnóstico con B1.
