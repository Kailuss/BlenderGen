# Torreón: unidad estructural de referencia

Propuesta del usuario (5-11-2026): igual que el ladrillo es la unidad de la fábrica, el torreón es la unidad
estructural mínima de un edificio y el lugar donde empezar el estilo lúgubre (no el edificio aséptico).
Dos variantes: **circular** y **cuadrada**.

## Paso 1 (hecho): aparejo puro — `structure/tower_plan.py`
- `courses(altura, hilada)`: hiladas iguales que suman la altura exacta, ninguna menor de 3 mm.
- `round_plan(radio, grosor, altura, hilada, ...)`: por hilada, piedras como intervalos angulares; número par
  de piedras con arco medio ≈ 1,9 × hilada; contrapeo de medio módulo entre hiladas; variación sembrada.
- `square_plan(lado, grosor, altura, hilada, ...)`: cuatro muros; las esquinas alternan dueño por hilada
  (frente y trasera / laterales), es decir, esquinas **trabadas**; juntas contrapeadas cada dos hiladas.
- Saeteras: un tramo de tres hiladas por planta, giradas entre plantas (circular) o repartidas por caras
  (cuadrada); los recortes menores de 3,2 mm se absorben en la piedra vecina.
- Pruebas puras: `tests/test_tower_plan.py` (cierre de la vuelta, contrapeo, sin solapes, esquinas trabadas,
  área exacta restada por saetera).

## Paso 2 (hecho): mallas — `structure/tower_building.py`
- Circular: cada piedra es un sector anular cerrado (cuerda ≤ 1,6 mm); un anillo de mortero por hilada,
  embebido como en los muros, rellena las juntas por dentro.
- Cuadrada: bloques con `primitives.block` (bisel incluido) y núcleo por muro y hilada.
- Juntas de 0,12 mm entre piedras y los mismos retranqueos de hilada que la fábrica; marcas de aparejo C5-5.
- Prueba `tests/blender_tower_building.py`: mallas cerradas con volumen positivo y vista Workbench.

## Paso 3 (hecho): coronación en ruina con apoyo verificado
- `crown_field`: perfil de pérdida sembrado alrededor de la torre (pocos cosenos, sin texturas globales).
- `ruin_round` / `ruin_square`: quitan las piedras por encima del perfil y luego, de abajo arriba, toda piedra con
  menos de la mitad de su arco o área apoyada en piedras vivas de la hilada inferior (nada queda flotando).
- El núcleo de mortero solo se construye bajo piedras vivas (sectores en hiladas rotas).
- Cuadrada: rejilla de juntas común por muro con medio módulo de contrapeo por hilada (antes dos hiladas
  seguidas podían repetir juntas). Sectores circulares biselados.

## Paso 4 (hecho): en el panel
- Subpanel «Torreón (prueba)»: planta (circular/cuadrada), diámetro o lado, altura, plantas, saeteras y ruina de
  coronación; botón «Generar torreón». Crea la colección `Ruinas · Torreón` (sustituye la anterior) sin tocar la
  casa; grosor y altura de hilada salen del tipo de construcción, la semilla es la de la casa.
- Prueba `tests/blender_tower_operator.py`.

## Paso 5 (hecho): escombro y desgaste
- `lost_angles` y `heap_directions`: el escombro cae donde más coronación se perdió (hasta dos montones).
- Cada montón: tierra con `terrain.earth_patch`, piedras partidas (`fracture.broken_stone`) asentadas y grava;
  una pieza por cada ~4 piedras retiradas (máximo 14 por montón).
- Desgaste de la fábrica (`weather.weather_stone`) en las piedras del torreón según «Desgaste».

## Paso 6 (hecho): forjados sobre ménsulas y escalera de caracol — `structure/tower_floors.py`
- Un forjado entre cada dos plantas. Las vigas (eje X, sección de `seat.py`) apoyan en **ménsulas**: perpiaños de
  la hilada inferior que atraviesan el muro y vuelan 4 mm (circular) o 3 mm (cuadrada) hacia dentro. La ménsula es
  una piedra del aparejo: entra en el plan antes de la ruina y sigue su regla de apoyo.
- Entrega mínima de 1,2 mm en el borde más desfavorable. En la circular las vigas oblicuas cerca del muro no se
  ponen: su ménsula pasaría de 9 mm o la cabeza no entregaría. Si la ménsula caería sobre una saetera o la viga roza
  la escalera, la viga se corre hasta 3 mm.
- Tablas en Y sobre las vigas, con vuelo máximo de 4,5 mm más allá de la última viga; necesitan dos vigas y el
  centro entre ellas.
- Escalera: hélice continua de peldaños de piedra pegados al muro (volada, sin machón), una vuelta por planta; cada
  peldaño monta un 30 % sobre el anterior. En la cuadrada sigue el paramento y quiebra en las esquinas.
- El hueco de la escalera sale del choque: las vigas que tocarían un peldaño no se ponen y las tablas se recortan.
  La llegada se orienta para que el tramo bajo el forjado pase por +Y, lejos de las cabezas de viga.
- Tras la ruina queda solo lo que se sostiene: viga con sus dos ménsulas vivas, tabla con dos vigas vivas, peldaño
  con el anterior vivo y al menos un 30 % de su arco con muro detrás. Lo que cae se retira (recuento en `interior.lost`).
- La cuadrada tenía el núcleo de mortero corrido por todo el muro y tapaba la saetera por dentro. Ahora hay un
  núcleo por tramo continuo de piedras.
- Pruebas: `tests/test_tower_floors.py` (puras: continuidad de la hélice, entregas, ménsulas en el plan, hilada que
  cierra, choque independiente madera/peldaño, cobertura ≥ 40 %, ruina) y `tests/blender_tower_interior.py` (mallas
  cerradas, choques con BVH, `.blend` en `dist/pruebas`, vista en corte).
- Límite conocido: no se garantiza altura libre de paso bajo el forjado, solo que no haya choque. La escalera
  termina en el último forjado.

## Paso 7 (hecho): terraza bajo el pretil y escalera hasta arriba
- Opción «Terraza» del subpanel (activa por defecto). Las plantas se reparten bajo un pretil de 3 hiladas, y las
  saeteras se centran en esas plantas (parámetro `parapet` de `round_plan` y `square_plan`).
- La terraza es un forjado más: vigas sobre ménsulas y tablas, y encima losas de piedra de 5 mm a soga, con medio
  módulo de contrapeo por fila.
- **Losas:** dentro del paramento, sin chocar con la escalera y con al menos el 60 % de su área sobre tablas. Tras la
  ruina, la misma regla con las tablas que quedan.
- **Último tramo:** no da la vuelta completa. Gira lo justo, cerca del paso angular del tramo anterior, para que el
  arco que pasa bajo la terraza quede centrado en ±Y, lejos de las cabezas de viga. Termina en el piso de losas.
- **Ménsulas:** se rechazan si ocuparían una saetera o un hueco de su propia hilada (`corbel_in_masonry`).
- **Choques:** la búsqueda deja 0,15 mm de holgura (`CLASH_MARGIN`) para cubrir el muestreo.
- **Límite:** en la torre circular de 40 mm no caben viga y escalera en todas las plantas, y alguna se queda sin
  tablas.

## Paso 8 (hecho): lo que pierde apoyo cae dentro («dejar a la naturaleza hacer»)
- **Antes:** vigas, tablas, losas y peldaños sin apoyo tras la ruina se retiraban.
- **Ahora** (`tower_floors.fallen`, `tower_building.build_fallen`): caen en vertical, de abajo arriba, sobre la
  superficie viva más alta por debajo: tablas o losas de un piso que aguanta, otro escombro o el suelo.
- **Dónde caen:** solo en la zona central libre de escalera.
- **Cómo se posan:**
  - Se prueban 16 sitios sembrados y se queda el más bajo, para que el escombro se esparza.
  - Ningún montón pasa de 10 mm sobre su piso, ni toca las vigas de un piso vivo de encima.
  - Al menos el 40 % de la huella tiene que descansar a su cota.
- **Piezas largas:** las vigas y tablas que no caben se parten en trozos.
- **Marcas:** las piezas caídas llevan `escombro` y `tower_fallen`.
- **Límite:** máximo 40 piezas; lo que no cabe se da por retirado (`interior.cleared`).
- No es simulación: es una caída geométrica en la generación. El laboratorio de física puede asentarlo después.
- **Pruebas:**
  - `test_fallen_pieces_rest_without_clashing`: zona central, se posa en algo y sin cruces.
  - `blender_tower_interior`: escombro sin choques BVH con peldaños, madera, losas, ménsulas ni entre sí, y vista de
    derrumbe 0,85.

## Siguiente
1. Almenas en el pretil; desagüe de la terraza.
2. Grietas en los sectores; saeteras ensanchadas por el daño; pátina y verdín por cara expuesta.
3. Llevar la misma caída a la terraza y cubiertas de la casa (`tower_roof.fall` ya hace algo parecido).
4. Grafo causal completo (muro → ménsula → viga → tabla, muro → peldaño).
