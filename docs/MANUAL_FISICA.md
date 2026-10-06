# Ruinas — manual de física y escenas de ejemplo

## Ver la demostración sin instalar nada

1. Abre **ruinas_v0324_fisica_interactiva.blend**. Deja activada la opción **Cargar interfaz / Load UI** al abrir para recuperar el encuadre preparado.
2. Se abre **00 REPRODUCIR - Espacio para ver la caída**, en el fotograma 1.
3. Pon el cursor sobre la vista 3D y pulsa **Espacio**. La pieza roja es el apoyo que se retira de forma controlada; las piezas superiores caen por gravedad.
4. Pulsa Espacio para pausar. **Mayús + Flecha izquierda** vuelve al principio. También puedes escribir 1, 12, 24 o 120 en el campo de fotograma de la línea de tiempo.
5. La animación está guardada en fotogramas clave. No necesita addon, autorun ni volver a calcular la física. Los colores alternos identifican piezas individuales; no son el acabado definitivo.

La retirada del apoyo es una acción de ensayo deliberada. La trayectoria de caída de las piezas superiores procede del motor de cuerpos rígidos, no de una animación manual. La demostración usa tiempo físico ralentizado al 20 % para facilitar la observación.

## Cambiar de etapa

En la barra superior de Blender abre el **selector de escena**, junto al nombre de la escena actual; no es el selector de capas de vista. El archivo contiene:

- **00 REPRODUCIR**: animación calculada y guardada, con módulos detallados.
- **01 CASA CON TEJADO**: casa completa intacta, con tejas, hastiales y acabado de madera/cal. Sus piezas son independientes; no es un STL fusionado.
- **02 CASA EDITABLE**: casa con daño y parámetros del generador. Tiene tabiques por secciones. La cubierta permanece activada; el daño puede retirar partes sin apoyo.
- **03 LABORATORIO**: colisionadores del ensayo, cuerpos rígidos y retirada de apoyo. Esta escena se puede recalcular con el addon.

Después de cambiar de escena, pulsa **Inicio / Home** con el cursor en la vista 3D para encuadrar. Si tu teclado no tiene esa tecla, usa **Vista → Encuadrar todo**.

Para comprobar la modularidad, entra en Modo Objeto y selecciona una pieza de madera. Cada sección tiene su propio objeto e identificador. En el archivo de demostración la agrupación de vista está desactivada. No confundas una escena de piezas con el sólido unido de exportación.

## Repetir con tus ajustes

1. Instala **ruinas_panel_v0324.zip** desde Preferencias → Complementos → Instalar desde disco. Reinicia o recarga el addon si ya usabas una versión anterior.
2. Ve a **02 CASA EDITABLE**. Abre la barra lateral con **N → Ruinas**. Mantén desactivada la vista automática mientras exploras.
3. Ajusta el daño y pulsa **Actualizar**. Las habitaciones solo se generan si caben los mínimos de 60 × 60 mm y pasos de 35 mm.
4. En **Distribución**, elige **Estancia 1/2/3** en Zona de física y pulsa **Preparar física de la zona**. La escena de ensayo es independiente de la casa.
5. Opcional: selecciona una sección de la fila inferior y pulsa **Retirar apoyo seleccionado (ensayo)**. Solo se admite una retirada por ensayo. Este paso sirve para probar la pérdida de un apoyo; no se ejecuta automáticamente al generar una casa.
6. Pulsa **Simular derrumbe**. Espera a que termine. Revisa los fotogramas o reproduce desde el inicio. Para aceptar, vuelve a pulsar Simular y deja el fotograma final.
7. **Volver a la casa** no acepta ningún resultado. **Aceptar para exportación** conserva las poses sobre las piezas detalladas y vuelve a la casa. Si no te convence, usa **Descartar resultado físico**.
8. Pulsa **Preparar sólido** cuando hayas revisado el resultado aceptado. Exporta solo el sólido seleccionado a STL, escala 1 y sin aplicar Scene Unit. Cambiar parámetros geométricos tras aceptar requiere descartar y repetir la física.

Si quieres reiniciar el laboratorio ya guardado, vuelve a la casa y prepara una escena nueva. No edites los IDs internos de las piezas.

## Qué está implementado y qué falta

Actualmente se simulan los tabiques de una estancia contra un suelo plano. Los dinteles se mantienen fijos. No hay todavía simulación estructural conjunta de muros de piedra, tejado y escaleras, ni colisiones contra todos esos elementos. Una pared estable puede asentarse sin derrumbarse: activar cuerpos rígidos no implica que deba caer. El botón de retirada de apoyo permite un ensayo visible y repetible.

El archivo anterior **ruinas_v0324_proceso_completo.blend** abre en el sólido final porque se guardó después de exportar. Sí contiene otras escenas, pero la variante exportada se ensayó sin cubierta. Se conserva como prueba de exportación, no como demostración principal de derrumbe. Su STL fue reimportado y validado; la nueva demostración de retirada de apoyo no se presenta como un sólido imprimible ya validado.
