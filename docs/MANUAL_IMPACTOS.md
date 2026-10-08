# Ruinas 0.32.7 — casa real, impactos y rotura

## Generador y vista

Actualizar y volver a la casa ajustan el recorte a las dimensiones de la geometría. El laboratorio trabaja en metros; el generador, en milímetros. Volver a la casa recalcula también la distancia de vista. Ya no conserva el recorte del ejemplo ni depende de un límite fijo de 10 metros.

**Preparar casa diseñada / zona** prepara las piezas de la casa actual. Si un archivo anterior tenía seleccionado el modo de ejemplo, este botón lo cambia a Edificio completo. **Crear ejemplo aislado (no usa la casa)** es una acción separada. El original permanece en su propia escena.

## Ensayo sobre la casa

1. Genera tu casa y pulsa Preparar casa diseñada / zona. La preparación resuelve encuentros y puede tardar: sigue siendo experimental en edificios densos.
2. En el fotograma 1 selecciona ladrillos con Mayús o B. Para atravesar piezas ocultas al seleccionar, activa Alt+Z. El suelo de seguridad no es un ladrillo.
3. Para reducir el cálculo, usa **Simular solo la selección; resto como soporte**. La casa entera permanece visible; las piezas no seleccionadas se convierten en soportes pasivos. El límite es configurable hasta 256. Para recuperar todos los cuerpos originales, prepara otro laboratorio desde la casa.
4. Selecciona hasta 32 ladrillos móviles y pulsa **Preparar rotura de ladrillos seleccionados**. Cada uno se divide mediante un corte oblicuo en dos fragmentos cerrados, unidos por una junta rompible. Configura Resistencia de fractura antes de prepararlos. Reduce el valor si no rompen.
5. Configura Dirección XYZ, Velocidad en mm/s, Radio y Multiplicador de masa. Dirección (0,1,0) avanza en Y; (0,0,-1) golpea hacia abajo. El blanco es el centro de las piezas seleccionadas; sin selección se usa la estructura móvil.
6. **Añadir impacto dirigido** admite hasta ocho piedras. Para evitar cuerpos superpuestos, las piedras nuevas con la misma posición inicial se desplazan lateralmente. Puedes cambiar la selección o la dirección para otro golpe.
7. **Lanzamiento** utiliza un tramo inicial de aceleración cinemática y luego deja la piedra libre con velocidad heredada y gravedad. **Empuje continuo** mantiene el avance impuesto como un actuador: no mide una fuerza física en newtons y puede atravesar elementos demasiado resistentes.
8. **Simular derrumbe** calcula desde el inicio. Los contactos usan mayor fricción; las juntas aportan cohesión antes de romper. Los escombros pueden deslizar tras un golpe: no están bloqueados artificialmente al suelo.

Modificar parámetros no cambia piedras ni fracturas ya creadas: deshaz la operación o prepara un laboratorio nuevo. Editar una escena de laboratorio tampoco regenera una reproducción horneada.

## Archivo de comprobación

`ruinas_v0327_casa_impacto.blend` contiene la casa procedimental original, un laboratorio con una zona móvil acotada y una reproducción calculada. La zona de prueba tiene 64 ladrillos móviles antes de dividir 16 en 32 fragmentos; el resto funciona como soporte pasivo. Así se prueba la casa real sin calcular el derrumbe completo de todo el tejado. La reproducción funciona sin complemento; para editar, instala `ruinas_panel_v0327.zip`.

## Límites

La prefractura de dos mitades es un primer modelo de rotura, no fractura adaptativa en el punto exacto de contacto. No representa pulverización, flexión ni resistencia de materiales calibrada. El mortero imprimible sigue sin reconstruirse después de la simulación. La masa está normalizada para el mínimo admitido por Blender. Los resultados no son un cálculo de ingeniería.

La vista corregida evita los recortes y la pérdida de precisión provocados por mezclar escalas; no repara automáticamente una malla externa con normales invertidas. Las pruebas de generación comprueban aparte cierre y geometría.

La preparación descarta residuos de booleanas únicamente si tienen menos de 1 mm³ y un espesor equivalente 2V/A inferior a 0,01 mm; quedan registrados en el informe de preparación. La fuente conserva todas sus piezas. Esto evita convertir láminas residuales casi coincidentes en cuerpos físicos.
