# Ruinas 0.32.12 — prueba completa y uso

## Instalación

Instala `ruinas_panel_v03212.zip` desde las preferencias de Blender. Guarda tu trabajo y reinicia Blender si había otra compilación cargada. El panel debe indicar **v0.32.12**. Abrir el archivo de ejemplo no instala ni actualiza el complemento.

## Archivo entregado

Abre `ruinas_v03212_torre_integrada.blend`. Conserva cuatro escenas:

1. **01 · Torre editable**: casa del generador, tres plantas, terraza almenada, balcones, cimientos y patio.
2. **02 · Laboratorio torre**: piezas y uniones editables. La selección del ensayo incluye 2.048 piezas.
3. **03 · Zarandeo calculado**: reproducción sin cuerpos rígidos; pulsa Espacio o recorre los fotogramas 1–10.
4. **04 · Sólido frame 10**: copia fusionada del fotograma 10. El STL está incluido por separado.

La reproducción contiene un movimiento corto y daños iniciales, no un derrumbe asentado. Para un ensayo largo, vuelve al laboratorio y usa **Simular** con impactos y duración propios. La opción **Soltar uniones seleccionadas** libera en el fotograma 13; no es el zarandeo de diez fotogramas.

## Preparar y zarandear tu casa

1. Configura la casa y pulsa **Actualizar**. Para la terraza elige **Construir cubierta → Torreón**. Las opciones de tejado inclinado se desactivan.
2. En Distribución elige **Edificio completo** y **Preparar casa diseñada / zona**. El botón del ejemplo aislado crea otro ensayo y no importa tu casa.
3. En el laboratorio selecciona piezas manualmente o por familia, porcentaje, semilla y preferencia por altura. El límite máximo seleccionable actual es 2.048.
4. Ajusta **Recorrido del zarandeo**. Pulsa el botón de zarandeo: calcula una copia con cuatro empujes de esquina entre 1 y 4, suelta la selección en 2 y desactiva impactos en 5. Termina en 10. El resto permanece pasivo.
5. Revisa la reproducción antes de exportar. El laboratorio anterior conserva sus cuerpos, uniones y selección.

El recorrido se expresa en mm y prescribe una trayectoria; no representa fuerza calibrada. Al soltar una unión deja de actuar su resistencia. Para estudiar diferencias entre familias manteniendo uniones, usa la simulación normal con impactos y los multiplicadores de resistencia.

## Impactos y cámaras

**Mostrar impactos en render** afecta a los nuevos impactos y al zarandeo. Desactivado permite ver la estructura, aunque las esferas siguen visibles en el visor hasta que venza su duración. El vencimiento también desactiva colisiones.

El selector **Cámara de render** permite elegir Estática, Órbita 120 o Interior. Son objetos de cámara normales: puedes moverlos y cambiar su óptica. La cámara interior apunta hacia la entrada y puede requerir recolocación si un tabique o una escalera tapa la vista.

La órbita completa está animada de 1 a 120. No alarga el cálculo físico de diez fotogramas. Para renderizar toda la vuelta en la reproducción puedes ampliar su rango final a 120: el edificio mantiene la última pose calculada después del 10. No significa que haya 120 fotogramas de física calculados. El ejemplo usa Workbench; para Eevee/Cycles añade iluminación.

## Construcción y exportación

Ventanas y balcones tienen paneles y cantidades independientes **por pared**, repartidas entre sus plantas disponibles. Si un balcón no cabe en alto/ancho aparece un aviso: reduce sus medidas o amplía la pared/planta. No se aplasta para hacerlo caber.

**Cimientos y patio** permite elevar la casa, ajustar la huella de los escalones, el espacio del patio y la altura de su valla. Tres plantas comparten la altura de las dos superiores; cada forjado usa su cota. Las habitaciones interiores se generan todavía en planta baja.

Con **Torreón**, **Tres plantas**, forjados y escaleras activados, hay tres tramos: baja a primera, primera a segunda y segunda a terraza. Los desembarcos coinciden con las cotas de sus suelos. La terraza reserva el hueco completo, incluido el desembarco, y sus vigas lo rodean con brochales. El acceso queda abierto, sin tapa de trampilla. Si la huella no cabe, el panel avisa; no reduce los peldaños para disimularlo. El recorrido necesita volver por la zona libre del forjado hasta el comienzo del siguiente tramo. Los peldaños conservan una huella útil de 20 × 20 mm y la aproximación al tramo reserva 35 mm.

La imagen `v03212_tower_interior.png` muestra los forjados y las escaleras con la fábrica oculta, para revisar las conexiones. El archivo editable conserva todos los muros.

En la reproducción elige el fotograma y **Exportar**. Menor vóxel conserva más detalle pero consume más memoria. La prueba usa 0,5 mm. Verifica los escombros en el aire, piezas desconectadas y soportes de impresión antes de laminar. La fuente del generador y el laboratorio se conservan.

## Si falla

No aumentes el límite de memoria como primer remedio. Conserva el mensaje y la carpeta de diagnóstico indicada; incluye el `.blend` fuente, medidas y versión del panel. El error de encaje indica geometría inválida, mientras que el mensaje de límite de recursos informa memoria/tiempo medidos y sus máximos configurados. Son fallos diferentes.

Mediciones, pruebas y límites concretos: `V03212.md`. La prueba reproducible del flujo completo es `tests/blender_v03212_integration.py`.
