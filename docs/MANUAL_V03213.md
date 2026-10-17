# Ruinas 0.32.13 — fachadas y cubiertas

Instala `ruinas_panel_v03213.zip` como complemento y reinicia Blender antes de
abrir los ejemplos. Los archivos anteriores deben usarse con su versión previa.

## Miradores de revoco

En Ventanas, **Proyección** separa el frente de la pared. **Unir miradores**
agrupa ventanas de la misma planta cuando su separación cabe en el umbral;
las puertas y los pilares impiden unir esos vanos. El espacio interior se abre
entre las ventanas agrupadas. Los laterales y entreventanas son de revoco claro;
los marcos, fondos y ménsulas siguen siendo de madera.

Activa daño y ajusta **Daño del revoco** para generar pérdida de material con
Perlin. Con cero se conserva el panel y su relieve. Las perforaciones aparecen
con valores altos; los bordes quedan protegidos. Un panel estrecho puede no
perforarse. Es geometría real, no una textura de color.

**Hojas de ventana** añade marcos y pernios. El ángulo establece su posición
inicial; no anima una bisagra física. Los tejadillos de puertas y ventanas usan
tejas de media caña y el perfil transversal de la cubierta.

## Cubierta

Los controles de curvatura longitudinal, desigualdad entre extremos y asimetría
desplazan el perfil de la cubierta. Los apoyos, hastiales, chimenea y canalones
siguen esas cotas. La deformación longitudinal se resuelve con piezas rectas
entre apoyos. Estos controles no sustituyen el daño ni su semilla.

## Archivos para comprobar el cambio

`ruinas_v03213_fachadas.blend`: miradores agrupados, revoco intacto y hojas abiertas.

`ruinas_v03213_fachadas_revoco.blend`: mismo ejemplo con daño del revoco en 0.95.

`ruinas_v03213_integrada.blend`: cuatro escenas. En **01 · Casa editable** está
la fuente; **02 · Laboratorio** conserva la preparación; **03 · Zarandeo
calculado** contiene la reproducción de diez fotogramas; **04 · Sólido frame 10**
contiene el resultado de impresión. Cambia de escena desde la barra superior.

Para repetir, abre la fuente y prepara la casa diseñada desde Distribución.
Selecciona las piezas del laboratorio y usa Zarandear. La prueba entregada
selecciona 512 piezas superiores; no demuestra un derrumbe completo asentado.
El revoco se prefractura según el tamaño máximo de fragmento del laboratorio.
Tras aceptar el fotograma, exporta desde el laboratorio con resolución de vóxel
explícita. La fuente editable se conserva.

## Límites

La pérdida Perlin es previa a la simulación; no añade fracturas adaptativas durante
el impacto. Las piezas restantes se prefracturan antes de Bullet. El ensayo
entregado utiliza vóxel de 0.5 mm para el sólido. No garantiza todas las semillas
ni todas las combinaciones extremas. Una exportación directa de un muro dañado
puede rechazar ladrillos realmente sueltos: no se ha eliminado esa validación.
