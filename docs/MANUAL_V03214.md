# Ruinas 0.32.14 — distribución y derrumbe

Reinicia Blender después de instalar el complemento. Usa esta versión para
los ejemplos nuevos; los archivos de entregas anteriores conservan su versión.

## Reglas de fachada

Las cuotas de ventanas y balcones siguen siendo totales por pared. Ahora se
reparten entre las plantas: las ventanas desde la planta baja y los balcones
desde la primera planta superior. No se aumenta silenciosamente la cantidad.
Si un vano no cabe por dimensiones, escalera, pilares o apoyos, se informa en
el panel y no se fuerza su construcción.

Las ventanas superiores intentan seguir los ejes de planta baja. Un balcón
frontal único intenta alinearse con la entrada, cuando hay espacio y apoyos.
La planta baja reparte ventanas en la franja libre junto a la puerta. Las cotas
reservan espacio para los tejadillos; el de entrada limita su altura para no
invadir el balcón de la planta siguiente.

Los tejadillos comparten curvatura transversal, elevación longitudinal y sesgo
con la cubierta principal. Sus dimensiones siguen limitadas por el hueco y la
altura libre de planta.

## Derrumbe

El inicio del control es más suave. La cubierta consulta la cota real de sus
dos muros de apoyo y puede asentarse sobre ellos. El descenso se limita al
menor valor entre 32 mm y el 55% de la altura de planta superior. Si faltan
apoyos válidos, las regiones de pérdida recortan tejas y madera. Las cerchas
aisladas y sus hastiales no se mantienen como triángulos suspendidos.

Cada teja se decide por su posición dentro del campo de daño, aunque muchas
se dibujen juntas para reducir objetos. No es necesario crear un objeto de
Blender por teja en la vista previa. El laboratorio separa las piezas físicas.
Los remates de miradores y balcones que exceden la envolvente de derrumbe
se recortan o eliminan. No se aplica una destrucción arbitraria a todos los
elementos que quedan por debajo de la zona afectada.

## Revoco

Daño del revoco conserva su control independiente. El campo combina dos
escalas de Perlin con desplazamiento por semilla. Se refina a 2 mm únicamente
el paño de mirador dañado; el resto mantiene el paso de 4 mm. Los perímetros
protegidos son menores en los miradores, permitiendo roturas menos uniformes.
La madera sigue siendo madera; el relleno es cal con relieve geométrico.

## Archivos

`ruinas_fachada_derrumbe_000.blend`, `003`, `020`, `055` y `085` muestran una
casa de tres plantas con los mismos parámetros y diferentes intensidades.
Los sufijos representan 0, 0.03, 0.20, 0.55 y 0.85. La comparación usa daño
del revoco de 0.95 para que sea visible incluso con derrumbe cero.

`ruinas_v03214_integrada.blend` contiene la fuente editable, el laboratorio,
la reproducción de diez fotogramas y el sólido final en cuatro escenas.
Usa el selector de escena de Blender para cambiar de etapa. El ejemplo físico
usa derrumbe 0.20 y revoco 0.80; selecciona 512 piezas superiores para zarandear.
No representa un derrumbe completo asentado. El STL entregado usa una resolución efectiva de vóxel de 0.35 mm.

## Límites

El asentamiento inicial es procedural, no un cálculo de resistencia estructural.
Las reglas evitan los fallos reproducidos, pero no certifican todas las semillas
ni combinaciones extremas. Los paños estrechos conservan borde y pueden mostrar
menos perforación. Las hojas tienen una postura inicial, no bisagras articuladas
en Bullet. La exportación conserva sus validaciones: no acepta silenciosamente
una malla abierta o un fragmento grande suelto.
