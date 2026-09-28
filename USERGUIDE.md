# Guía de uso · Ruinas v0.31

Ruinas genera muros de mampostería en ruinas para miniaturas de 28 a 35 mm, listos para imprimir en resina. Todo se mide en milímetros.

## Instalación

1. En Blender 5.0 o posterior: **Editar → Preferencias → Complementos → Instalar desde disco** y elige `dist/ruinas_panel_v031.zip`.
2. Activa **Ruinas — Muro de fantasía**.
3. Abre la barra lateral de la Vista 3D (tecla **N**) y la pestaña **Ruinas**.

Usa solo una copia del complemento. Si abres un archivo de la v0.20, no ejecutes su antiguo `generador_muro.py`: los ajustes guardados se conservan igualmente.

## Primera ruina

- **Añadir → Malla → Ruina**, o el botón **Actualizar** del panel, genera la ruina con los ajustes de la escena.
- Con **Vista previa automática** activada, cada cambio de un control regenera la vista unos instantes después.
- **Otra variante** (el botón junto a la semilla) cambia los detalles sin cambiar los ajustes.
- El **candado** junto a la semilla fija la distribución de piedras, pilares y agujeros: con él cerrado, la semilla solo cambia el desgaste y las grietas.

El derrumbe tiene una silueta irregular que cambia con la semilla (con el candado cerrado, solo cambia al abrirlo o al tocar la semilla de distribución).

La ruina se crea en la colección **MURO · fuente procedural**. No la edites a mano, porque se regenera en cada cambio.

## El panel

Arriba están las acciones y el estado. Debajo, un subpanel por tema, con un botón ↶ para volver a los valores por defecto de ese subpanel.

| Subpanel | Qué controla |
|---|---|
| **Construcción** | Tipo (Tabique 8 mm, Pared 12 mm o Muralla 18 mm de grosor), altura (Baja 27 mm, 1 planta 52 mm o 2 plantas 102 mm), longitud y vigas de entreplanta (solo con 2 plantas) |
| **Distribución** | Paredes contiguas: ninguna, L, U o habitación. También el fondo y el lado de la L |
| **Acabado** | Derrumbe, desgaste (Ligero / Medio / Fuerte / Personalizado), intensidad personalizada, grietas, escombros, y tierra y grava |
| **Puerta** | La casilla de la cabecera activa la puerta. Dentro: hoja, posición, anchura, altura, marco y vetas |
| **Ventanas** | La casilla de la cabecera las activa. Se colocan solo donde hay piedra que las sostenga, así que puede haber menos de las pedidas |
| **Calidad** | Calidad de edición y de exportación, y vista rápida |
| Avanzados, plegados | **Aparejo**, **Grietas**, **Derrumbe y agujeros**, **Pilares** |

Los controles que no aplican se ven atenuados, por ejemplo el fondo con una sola pared. Pasa el ratón sobre cualquier control para ver su descripción.

### Grietas

- Salen más cerca de puertas, ventanas, agujeros y extremos de muro. Ahí algunas piedras quedan partidas de borde a borde.
- Los sillares de los pilares también se agrietan. Los pilares de conexión no, para que encajen al montar módulos.
- Las grietas, como el desgaste, cambian con la semilla: siguen un recorrido aleatorio distinto en cada variante.

## Calidades y vista previa

| Calidad | Para qué |
|---|---|
| **Borrador** | Estructura con biseles mínimos, instantánea |
| **Trabajo** | Estructura con biseles y aberturas, sin desgaste, grietas ni escombros. Para editar la forma |
| **Detalle** | Todo: desgaste, grietas, escombros, y poros y grano finos para resina. Es la calidad de exportación por defecto y la más lenta |

El desgaste, las grietas y los escombros solo se ven en Detalle; el panel lo recuerda en Acabado y Grietas. Para verlos mientras editas, pon la calidad de edición en Detalle.

En **Desgaste → Personalizado**, el deslizador **Intensidad** permite ajustar de 0 (sin
erosión superficial) a 1 (máxima). En los otros modos queda atenuado y muestra la
intensidad del preset después de generar. El desgaste no desactiva los daños de agujeros,
derrumbe ni grietas: tienen sus propios controles. La 0.31 acentúa las depresiones y
mantiene una respuesta progresiva del grano hasta el máximo, sin subir la resolución
configurada. Los archivos anteriores conservan las claves y presets; su acabado en
Detalle cambia al regenerar con el nuevo algoritmo.

Con **Vista rápida**, cada cambio muestra primero Borrador y después refina en la calidad de edición. Si una generación tarda demasiado, la vista automática se pausa y el estado lo indica, por ejemplo «Pausa: work tarda 31 s · pulsa Actualizar»:

- por defecto, el refinado se pausa si tardó más de 4 s;
- la vista rápida entera, si tardó más de 10 s.

**Actualizar** siempre genera. Mientras trabaja, el cursor muestra el progreso.

## Exportar para imprimir

1. Pulsa **Preparar sólido**. Genera en la calidad de exportación y une todas las piezas en un único sólido cerrado, **MURO · sólido exportable**, que queda seleccionado. En Detalle, un muro con puerta tarda alrededor de un minuto.
2. **Archivo → Exportar → STL** con **Solo selección**, **Escala 1** y **Unidad de escena** desactivada. El STL sale en milímetros.
3. En el slicer, el tamaño está pensado para 28 mm. Para escala de 35 mm, escala al 125 %.

El sólido conserva todo el detalle de la vista: grietas, vetas y biseles. Los restos diminutos y los huecos cerrados interiores se eliminan solos.

Consejos para resina (Anycubic Photon P1 Max o similar):
- Imprime los muros con la misma orientación siempre: el ancho de las grietas en caras verticales depende de la altura de capa.
- Las grietas mantienen al menos 0,15 mm de ancho y 0,5 mm de fondo en casi todo su largo, y se afinan hasta la punta.
- `python dev.py calibrate` genera una placa de prueba opcional para comprobar qué detalles sobreviven a tu resina y tu imprimación.

## Preferencias del complemento

En **Preferencias → Complementos → Ruinas**:

| Preferencia | Por defecto |
|---|---|
| Pausar refinado a partir de | 4 s |
| Pausar vista rápida a partir de | 10 s |
| Escena en milímetros: pone las unidades de la escena en mm al generar | activada |
| Fusión del sólido | Unión exacta (conserva el detalle). Vóxel suaviza y pierde el detalle fino |

## Mensajes frecuentes

| Mensaje | Qué hacer |
|---|---|
| «No cabe la puerta entre los pilares» | Alarga el muro, reduce el grosor o quita los pilares de conexión |
| «Fragmento suelto de … mm» al preparar el sólido | Alguna pieza no toca el resto. Prueba **Otra variante** o reduce derrumbe y daño |
| «Pausa: … tarda … s» | Normal con habitaciones o calidades altas. Pulsa **Actualizar** cuando quieras ver el resultado |
| Botones desactivados | Cambia a **Modo Objeto** |

## Límites actuales

- No hay suelos de tablones, cubiertas ni simulación física de escombros.
- Las alturas 27, 52 y 102 mm son medidas de diseño, no reglas de ningún juego.
- Una habitación de dos plantas en Trabajo con muchas grietas puede tardar medio minuto.
- Si el Detalle se queda corto o el sólido tarda demasiado, anótalo: son las siguientes mejoras previstas.
