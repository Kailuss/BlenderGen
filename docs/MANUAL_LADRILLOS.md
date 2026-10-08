# Ruinas 0.32.6 — ladrillos, huecos e impacto

Abre `ruinas_v0326_ladrillos.blend`. La escena IMPACTO · REPRODUCIR contiene la animación calculada: pulsa Espacio o recorre los fotogramas 1–120. No necesita el complemento para reproducirse.

## Modificar el ensayo

1. Instala `ruinas_panel_v0326.zip` como complemento desde disco y actívalo.
2. En el panel Ruinas pulsa **Abrir laboratorio editable**, o elige IMPACTO · EDITAR en el selector de escenas.
3. Vuelve al fotograma 1 antes de editar. Cada ladrillo es un objeto independiente: Mayús+clic añade piezas y B selecciona un rectángulo. Activa rayos X (Alt+Z) si quieres seleccionar también las piezas ocultas.
4. **Abrir hueco: retirar ladrillos seleccionados** elimina todas las piezas elegidas del ensayo. El suelo y la piedra están protegidos. La casa original no cambia. Ctrl+Z deshace la retirada.
5. **Simular derrumbe** calcula los 120 fotogramas. Todos los ladrillos están activos simultáneamente; la gravedad hace caer los que pierdan apoyo.
6. Para repetir desde una construcción intacta, vuelve a **00 AJUSTES**. En Distribución elige **Ladrillos: impacto y huecos**, Muro o Torre y un límite entre 16 y 256. Pulsa **Preparar física de la zona**. Se completan hiladas de 8 o 14 piezas, sin superar el límite.
7. En el laboratorio nuevo pulsa **Añadir piedra de impacto**. Puedes mover la piedra con G en el fotograma 1 para elegir dónde golpea. Es un cuerpo bajo gravedad, sin trayectoria animada. Solo se admite una piedra por ensayo.

## Escenas incluidas

- IMPACTO: muro de 96 ladrillos y piedra de 36 mm de diámetro.
- HUECO: retirada simultánea de 11 ladrillos inferiores; caen piezas superiores por pérdida de apoyo.
- TORRE: torre hueca de 84 ladrillos con impacto.
- Cada caso tiene una escena REPRODUCIR y otra EDITAR. Editar el laboratorio no actualiza la reproducción ya calculada; consulta el resultado en el propio laboratorio.

## Alcance y límites

Este ensayo acotado usa mampostería seca idealizada, sin mortero, muelles ni uniones. El suelo pasivo mide un metro de lado; evita la caída al vacío dentro de ese recinto. Los ladrillos colisionan como cajas y la piedra como esfera. La forma visible tiene un bisel ligero, sin aumentar la densidad para ocultar fallos.

No es todavía la destrucción de una zona seleccionada de la casa. Los ladrillos se desplazan enteros: no se fracturan internamente. Abrir hueco retira piezas completas. La transferencia a la casa, la cohesión del mortero y la reconstrucción imprimible quedan pendientes. La masa está normalizada para el límite mínimo de Blender; no representa un ensayo de ingeniería.

En el laboratorio anterior de edificio completo, Soltar uniones seleccionadas ahora recoge todas las piezas seleccionadas, no solo la activa. Sus uniones rígidas y coste de cálculo siguen siendo experimentales.

## Validación

Blender 5.2.2: impacto mueve 74/96 ladrillos más de 6 mm; torre 16/84; hueco 83/85. Aproximadamente 2–4 segundos de simulación por caso en esta máquina. Mallas cerradas y piezas sobre el suelo, con tolerancias numéricas inferiores a 0,001 mm en estos resultados. También se comprueba el asentamiento de una construcción intacta y se reabre el archivo guardado.

El muro intacto se asienta menos de 0,48 mm durante los 120 fotogramas; no presenta el derrumbe del caso impactado. Los límites superiores de 256 piezas están disponibles, pero las mediciones anteriores corresponden exclusivamente a las escenas entregadas.
