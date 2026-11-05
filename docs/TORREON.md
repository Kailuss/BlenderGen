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

## Siguiente
1. Integrarlo como tipo de edificio en el panel; desgaste y grietas de la fábrica actual en los sectores.
2. Interior: forjados de vigas radiales o paralelas con asiento en `seat.py`, escalera de caracol embebida o
   adosada, terraza con `roof_support` (ya exige apoyo real).
3. Lúgubre: coronación rota con almenas perdidas, sillares caídos al pie, saeteras ensanchadas por el daño,
   pátina y verdín por cara expuesta; todo sembrado y paramétrico.
4. Grafo causal completo (muro → forjado → terraza) para que el derrumbe deje solo lo que se sostiene.
