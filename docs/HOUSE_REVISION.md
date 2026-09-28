# Casa 0.31: chimenea, escalera y cubierta

La entrega aportada y el repositorio usaban el mismo número de versión con contenidos
distintos. Se adopta como base de esta revisión el addon del ZIP del usuario, conservando
el archivo original y editando únicamente los módulos de `src/ruinas_panel/`.

## Cambios

- Hogar desde la planta baja, con base pétrea, jambas, dintel, campana y conducto
  hueco continuo. El tamaño deriva de las hiladas y el grosor del edificio. Se busca
  un muro libre de vanos y escalera; en la casa entregada queda junto al frente,
  donde puede existir un hogar accesible. Incluye dos leños carbonizados.
- Tablones y vigas dejan paso a la chimenea; cabeceros rodean la entreplanta.
  La cubierta reserva el conducto con un hueco rectangular, y lleva babero y peto.
- Tejas cerradas de media caña, solapadas, con pared nominal de 0,58 mm y cumbrera
  curva. Ocho segmentos describen el arco, sin subdivisión por desgaste.
- Hastial de revoco con espesor, retranqueo y entramado de montantes y riostras.
- Losas de escalera de 1,05 mm, con depresiones, poros y cantos gastados; el núcleo
  queda por debajo del relieve. Mantiene el área de apoyo de 20 × 20 mm y la reserva
  de acceso de 35 mm. Borrador y Trabajo siguen omitiendo la erosión fina.

## Verificación

Blender 5.2.2 con `--python-exit-code 1`. Se revisaron los renders de casa, hogar,
tejas/hastial y escalera además de las comprobaciones geométricas.

- `dev.py check`: sintaxis, contratos y seis pruebas puras.
- `dev.py test`: cuatro escenarios, variantes GN, caché, registro y exportación.
- `tests/blender_house_revision.py`: parámetros del archivo aportado, hogar en
  planta baja, entrada y eje de humo libres, cierre de piezas nuevas y fuente,
  reproducción exacta desde caché y guardado del `.blend` revisado.
- `tests/blender_stairs_surface.py`: calidades/semillas/desgaste, ambos sentidos,
  medidas de apoyo, cierre y unión de losas con macizo.
- `tests/blender_roof_surface.py`: arco, espesor, cierre, curvas extremas, reserva
  de chimenea y hastiales recortados.

La comparación del pequeño paño de tejado conserva 254 tejas: pasa de 10.699 a
18.599 caras por la sección curva y el entramado. La casa aportada tenía 498.129
caras expandidas; la revisión queda en torno a 525.000 (consultar métricas exactas
en `reports/house_revision.json`). No se ha aumentado la resolución global.

La batería general se repitió contra el addon original extraído del ZIP. Sus cuatro
escenarios conservan geometría y caras al no activar las partes aquí revisadas.
Las caras diminutas son iguales antes y después: 6 en `door_windows_work`, 17 en
`room_beams_draft`, 5 en `window_detail`; no hay aristas abiertas. Datos originales:
`reports/import_baseline.json`; revisión: `reports/modular.json`.

El exportador heredado rechaza de forma controlada un fragmento de 473,7 mm³ en la
ruina dañada usada por la prueba de sesión. En una pared íntegra puede recurrir a
normalización de 0,3 mm (desviación de caja medida: 0,118 mm). La casa revisada se
entrega como fuente procedural, no como sólido fusionado certificado para imprimir.
La validación no cubre todas las combinaciones de parámetros ni una impresión física.

## Entrega

`dist/ruinas_v031_revisada_completo.zip` contiene la escena revisada, addon instalable,
vistas y esta nota. Para regenerar, instalar `ruinas_panel_v031.zip` manteniendo una
sola versión activa. La escena se abre con la geometría guardada; se ha retirado de
la copia revisada el activador embebido antiguo para que no restaure otra versión.
El ZIP y `.blend` originales permanecen intactos.
