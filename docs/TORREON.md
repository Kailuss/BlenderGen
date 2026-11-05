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

## Siguiente
1. Constructor de mallas: sectores anulares cerrados (circular) y bloques (cuadrada) desde el plan, con el
   mismo bisel, desgaste y grietas que la fábrica actual; IDs de aparejo (`identifiers.tag`) desde el inicio.
2. Interior: forjados de vigas radiales o paralelas con asiento en `seat.py`, escalera de caracol embebida o
   adosada, terraza con `roof_support` (ya exige apoyo real).
3. Lúgubre: coronación rota con almenas perdidas, sillares caídos al pie, saeteras ensanchadas por el daño,
   pátina y verdín por cara expuesta; todo sembrado y paramétrico.
4. Grafo causal completo (muro → forjado → terraza) para que el derrumbe deje solo lo que se sostiene.
