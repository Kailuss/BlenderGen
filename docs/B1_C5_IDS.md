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
