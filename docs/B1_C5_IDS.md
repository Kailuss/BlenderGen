# B1 C5 identidad de segmentos

3 de noviembre de 2026. Primer avance parcial, independiente de física.

El ID de segmento usa `seg.<muro>.f<planta de la viga>.b<banda>.<ordinal>`.
La planta de la viga permanece constante en todas las bandas de su columna de apoyo.
Se evita que las columnas de vigas de plantas diferentes compartan identidad por accidente.
El ordinal sigue asignado por aligned_axes antes de filter_axes; los filtros marcan estado.
Los consumidores del esqueleto y el ensayo causal se han actualizado juntos.

C5-5 no está completo: los IDs de piezas del RemovalLedger todavía dependen del nombre de Blender.
No se modificaron mallas, semillas, nombres visibles ni física. Falta la aceptación T1 de estrés,
los roles de fábrica y la predicción pieza sobre pieza desde layout. No se declara cierre B1.

La comparación solicitada de efa7e21 frente a a7d429a modifica solamente
reports/b1_c4_t1.json y reports/modular.json, sin cambios de código.

## C5-5 y primer paso de C5-3 (Claude, 4 de noviembre de 2026)

Las piezas de fábrica guardan su posición de aparejo en `layout_kind`, `layout_course` y `layout_index`
(`identifiers.tag`): piedras de muros de retorno (`stone`, hilada, j), piedras y núcleos del frente
(`stone`/`mortar`, hilada, índice), sillares de pilar (`pier<i>`, 0, j), cimientos (`found<lado>`, hilada,
índice) y escalones de entrada (`step`, 0, i). `removal_events.begin` construye el ID con
`identifiers.layout_key` cuando la pieza lleva esas marcas y recurre al nombre en caso contrario; el
registro anota `layout` y el papel de fábrica (`identifiers.role`: SILLAR, NUCLEO o CIMENTACION).

Los nombres con sufijo `.001` de Blender ya no entran en el ID de esas piezas. Siguen dependiendo del
nombre las piezas sin aparejo (tierra, maderas, tejas, decoración). No cambian mallas, nombres, semillas
ni digests (las propiedades personalizadas no entran en el digest). Los informes `b1_c4_t1.json` previos
usan el formato anterior y no son comparables clave a clave.

## C5-3: definición única de asiento (Claude, 4 de noviembre de 2026)

Había tres definiciones de asiento de viga que no se leían entre sí:

1. Constructor y auditoría (`openings`, ensayo causal): tres rayos a ±1,5 mm, 2,7 mm bajo el eje, dos aciertos.
   La caja del alojamiento, la cota 3,6/2,5 mm, la sección 4,2 × 4,7 mm y el vuelo de 4 mm eran literales repetidos
   en `openings`, `floors` y `stairs`.
2. Plan (`floor_frame.beam_skeleton`): contacto nominal fijo de 4,2 × 3 mm de modelo (180 mm de mundo),
   pasado a mano por el ensayo de base y sin relación con la viga construida, que atraviesa el muro entero.
3. Ensayo de daño (`blender_b1_c3_damage`): banda de piedra [z−4,5, z−2,7] y semiancho 2,6 mm propios.

`construction_core/seat.py` es ahora la única fuente: `beam_z`, `pocket`, `embed_length`, `BEAM_WIDTH_MM`,
`BEAM_HEIGHT_MM`, `samples`/`supported`, `bearing_overlap` y `plan_seat`. Constructor, forjado, cabecero de
escalera y los tres ensayos Blender la leen. Los valores son los mismos literales: la geometría no debe cambiar
(pendiente de confirmar con los cuatro digests de `dev.py test` en el PC).

Único cambio de criterio: `plan_seat(grosor)` da al plan una profundidad de asiento igual al grosor del muro
que la viga atraviesa (12 mm de modelo, 720 mm de mundo por defecto), en lugar de 3 mm. `b1_joint_baseline.json`
cambiará en `seat_mm` y `area_mm2` al regenerarse. El asiento sigue siendo geométrico: no es capacidad resistente.

Pendiente de C5-2: el T1 de estrés con pérdida.
