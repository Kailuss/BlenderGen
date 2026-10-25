# Núcleo constructivo vigente B1-C3

Estado del 25 de octubre de 2026. Esquema 3, magnitudes estructurales en mundo y escala explícita en la frontera del adaptador. Los materiales mantienen confianza C salvo evidencia documental específica; no se han calibrado umbrales Bullet.

## Productores y consumidores

layout.front_courses y return_courses calculan aparejo sin mallas. front_stone_bounds es la fuente única de límites y encuentros de piedra frontal, consumida por walls y masonry_intervals. El resultado frontal se memoiza en runtime con firma de ajustes, límite de 16 entradas y copia defensiva. config_masonry nombra retranqueos y tolerancias.

construction_plan publica reservas previas, pero delega en stairs.plan, upper_plan y terrace_plan. No es todavía el productor único: persisten cálculos duplicados en consumidores. El grafo del edificio existente se adapta después de las mallas; no gobierna aún todos los objetos.

floor_frame emite un esqueleto mínimo de viga y segmentos, no el forjado completo. WALL_SEGMENT se aloja en WALL y transmite apoyo hacia segmento inferior o cimentación, que apoya en terreno. Los IDs numeran la banda inferior con nivel 0 y el primer forjado con nivel 1. Los ordinales de eje se asignan antes de filtrar; filter_axes marca bloqueos sin renumerar. El campo de daño aún no retira piedras mediante estos segmentos.

## Políticas del grafo

SUPPORTED_BY transmite apoyo; HOSTED_BY expresa alojamiento, CONNECTED_TO conexión y ARRIOSTRADO_POR arriostramiento. support_groups exige k de n por grupo y es incompatible con minimum_supports, incluso si este vale None. loss valida todas las políticas antes de evaluar, también las ajenas a la retirada solicitada; un grupo inválido lanza ValueError.

La política de tres valores compara clausuras optimista y pesimista. unsupported son pérdidas confirmadas y requires_review solo elementos cuyo resultado depende de apoyos con política desconocida. Un apoyo redundante suficiente evita revisión. loss no propaga desaparición por HOSTED_BY: la carpintería no puede considerarse resuelta por esta función. La futura eliminación del anfitrión debe tener una regla explícita de alojamiento/daño; no basta perder un segmento cercano para borrar un vano entero.

Los IDs de vanos se basan en pared, planta, familia y posición, no en el ordinal de iteración. La escala de la miniatura no se confunde con la escala numérica de Bullet. Las capacidades desconocidas siguen siendo None.

## Verificación y límites

Los cuatro digests geométricos se conservan. El baseline intacto compara dos cotas de viga y una sonda de coronación, nunca tres forjados. T1/T2 miden daño/vanos y sensibilidad del asiento, pero carecen de predicción causal independiente: derrumbe_global y huecos_generados contienen conteos/zonas, no IDs de retirada; prune_support no publica eventos por piedra. No se afirma cero discrepancias ni cierre de B1.0. Los informes expresan los resultados desconocidos con null.

Los logs y el catálogo de pruebas de B1-C3 incluyen el commit y las pruebas añadidas desde A1. No equivalen a simulaciones Bullet. El banco de calibración y la integración completa de forjado/escaleras siguen pendientes. Historial anterior en CHANGELOG.md y commits de A1/B1.
