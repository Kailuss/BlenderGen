# Madera fracturada y selección por altura — 0.32.11-r2

## Instalar esta revisión

Guarda tu trabajo, instala `ruinas_panel_v03211_r2.zip` y reinicia Blender. Comprueba que la cabecera del panel indica **v0.32.11-r2**. Abrir un archivo `.blend` no actualiza el complemento instalado: una instalación anterior con el número 0.32.11 puede seguir usando el cálculo antiguo.

La entrega r2 reconstruye el laboratorio desde la fuente actual y comprueba las medidas de la carpintería. Si cambias los parámetros de la casa después de preparar el laboratorio, el panel avisa de que debes prepararlo de nuevo. Esta comprobación compara parámetros del generador; no detecta todas las ediciones manuales de mallas.

La madera afectada por el hundimiento de cubierta se reconstruye con tramos rectos rígidos. Los cortes tienen pérdida de fibra y extremos irregulares; las articulaciones entre tramos permiten representar el hundimiento sin doblar cada viga como metal. Es una prefractura geométrica, no un cálculo de tensiones de madera ni una rotura adaptativa durante el impacto. La curvatura arquitectónica del tejado sano conserva su control anterior.

En la primera etapa se conserva una unión rompible entre tramos consecutivos de la misma viga cuando el corte deja hasta 3 mm de separación. No se aplica a vigas distintas, grandes huecos o la etapa avanzada de pérdida de cubierta. La agrupación de terreno del laboratorio combina mallas directamente para evitar el coste de evaluar todas las uniones durante el operador de unión.

## Preparar un desprendimiento

1. Genera la casa y pulsa **Preparar zona de físicas**. Conserva la escena del generador.
2. En el laboratorio, abre **Preparar selección de desprendimiento**.
3. Elige material y porcentaje. **Todos** incluye piedra, teja, madera y metal; excluye suelo de seguridad, base y proyectiles.
4. Ajusta el gradiente: cero reparte uniformemente; un valor alto favorece las piezas superiores, manteniendo alguna posibilidad de seleccionar las bajas. El porcentaje se aplica al total de piezas elegibles y se redondea al entero más próximo.
5. Pulsa **Seleccionar por porcentaje y altura**. La selección es reproducible con la misma semilla. Puedes revisarla y modificarla con las herramientas habituales de Blender.
6. Para acotar el coste, usa la acción de limitar móviles a la selección. Las otras piezas quedan como colisionadores pasivos; esto modifica el resultado respecto a un edificio enteramente móvil.
7. Pulsa **Soltar uniones seleccionadas** y después **Simular derrumbe**. Las uniones se liberan juntas en el fotograma 13. El gradiente decide qué piezas entran, no el orden temporal de caída.
8. En la reproducción, elige el fotograma y exporta. La fuente y el laboratorio siguen disponibles para repetir el ensayo.

Una selección del 100 % puede superar la memoria disponible. El laboratorio mantiene sus límites de recursos y el cálculo aislado. El porcentaje no garantiza que todas las piezas elegidas se desplacen: algunas conservarán apoyo por contacto.

El cálculo omite residuos de piedra recortada menores de 0,2 mm en todos los ejes. Son restos minúsculos de booleanas que pueden producir colisiones inestables. El informe registra sus nombres; no se modifica la casa del generador ni se aplica este filtro a herrajes finos o piezas diseñadas sin recorte.

## Memoria y escala del cálculo

El motor calcula las colisiones con las mallas ampliadas 100 veces en una copia aislada. También adapta las trayectorias, la gravedad y los umbrales de rotura; al guardar la reproducción restaura las dimensiones originales. No amplíes la casa manualmente para usar esta corrección. El suelo de seguridad y las piezas pasivas también participan en la misma escala.

La comparación sobre un laboratorio de 5.192 cuerpos aisló el pico de memoria en los contactos a escala de miniatura: quitar todas las uniones o usar colisionadores convexos no bastaba. No es una garantía de coste constante para cualquier casa. Mantén el límite de memoria en 4.096 MB inicialmente; los controles de memoria y tiempo permiten ajustarlo a tu equipo. El límite corresponde al proceso hijo, además de la memoria que ya utiliza tu sesión de Blender.

Usa **Simular derrumbe** para calcular y reproduce después la escena de resultado. Esa reproducción contiene animación y no necesita volver a resolver cuerpos rígidos. Si falla una etapa, conserva la fuente y consulta el registro indicado por el mensaje.

El mensaje «límite de recursos» procede del vigilante de Ruinas. Por ejemplo, 4.648 MB supera el límite predeterminado de 4.096 MB; «12 s» indica el tiempo transcurrido, no un límite de doce segundos. El diagnóstico incluye ahora la versión, la ruta del trabajador y los límites utilizados. No se ha identificado Windows Defender como causa de este fallo y no es necesario desactivar su protección. CUDA/OptiX acelera el render compatible, no este cálculo de cuerpos rígidos.

## Construcción y detalle

Los valores iniciales de puerta pasan a 35 × 48 mm y los de ventana a 14 × 22 mm. El acceso al balcón dispone de ancho y alto propios (24 × 42 mm) y su plataforma de profundidad independiente (20 mm). Los valores de puerta y ventana ya guardados se conservan; los nuevos controles de balcón usan sus valores iniciales al abrir archivos antiguos.

Los alojamientos de vigas buscan juntas entre ladrillos de ambas paredes, con separación objetivo de al menos dos módulos o 24 mm, adaptada a los huecos disponibles. El estucado del hastial utiliza ruido Perlin coherente sobre su cuadrícula existente, sin aumentar la densidad por defecto ni añadir booleanas de daño. El retranqueo y el acabado superficial separan el estucado de la carpintería.

## Caso integrado reproducible

`tests/blender_synergy.py` genera una casa de 220 × 190 mm, dos plantas, calidad Trabajo, semilla 47. Verifica accesorios realmente presentes, cierre, caras degeneradas y madera afectada. Incluye balcones, chimenea, bajantes, tabiques, escalera de piedra, suelos, cubierta y hastiales. El plano respeta estancias de 60 mm y pasos de 35 mm; puede resolver una petición de tres espacios como dos habitaciones y un corredor.

`tests/blender_synergy_physics.py` prepara esa fuente en un proceso separado, intenta seleccionar el 35 % con gradiente 0,7 y reduce ese porcentaje si supera 2.048 móviles. El informe registra el porcentaje realmente usado. Calcula 72 fotogramas y guarda un checkpoint del laboratorio antes de calcular. `tests/blender_synergy_export.py` exporta a vóxel de 0,5 mm y conserva las escenas del proceso.

Resultado medido en r2: 6.170 cuerpos preparados, 5.880 objetos en la reproducción, 2.002 piezas seleccionadas (34 %) y 1.991 con desplazamiento. La selección incluye 344 piezas de piedra, 993 tejas, 623 maderas y 42 metales; el trabajador omite 16 residuos minúsculos antes de calcular. Los 72 fotogramas tardaron unos 308 segundos; incluyendo arranque y carga de la reproducción, unos 481 segundos. Pico observado en el proceso hijo: 1.670 MB. Las 5.880 piezas conservaron su geometría y posición inicial con error inferior a 0,00006 mm; ninguna terminó por debajo del suelo de seguridad. Los tiempos y consumos dependen del equipo y de la escena.

El archivo `ruinas_v03211_r2_integrada.blend` conserva las escenas **01 · Casa editable**, **02 · Laboratorio editable**, **03 · Reproducción** y **04 · Sólido exportado**. Elige la escena 03 y pulsa Espacio para ver lo calculado. Para un nuevo ensayo, vuelve a la escena 02 y utiliza los botones del laboratorio; para cambiar la construcción, vuelve a la escena 01. El STL separado contiene el fotograma 72; es una instantánea de ese momento, no una garantía de que todos los escombros hayan terminado de asentarse.

Trabajo omite las grietas booleanas finas. La escalera de piedra y la de madera, o distintos estilos de puerta, son alternativas: este caso no prueba simultáneamente todas las combinaciones. El STL remallado puede perder detalle fino y no reconstruye mortero arquitectónico.
