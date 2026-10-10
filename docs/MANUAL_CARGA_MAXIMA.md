# Ruinas 0.32.8 — casa máxima y cálculo protegido

## Abrir la entrega

Instala `ruinas_panel_v0328.zip` como complemento y abre `ruinas_v0328_maxima.blend`. Para ver la reproducción no hace falta instalarlo ni permitir scripts automáticos.

El selector de escenas contiene cuatro etapas:

- **00 REPRODUCCION · ESPACIO**: poses calculadas. Vuelve al fotograma 1 y pulsa Espacio. No vuelve a ejecutar Bullet.
- **01 CASA MAXIMA · EDITAR**: casa procedimental original de 240 × 240 mm y dos plantas. Conserva sus controles.
- **02 LABORATORIO · ZONA MOVIL**: piezas, apoyos, uniones y proyectil editables. La zona delantera es móvil; el resto sirve como soporte fijo.
- **03 SOLIDO · STL**: resultado del último fotograma unido para exportación en milímetros.

La casa conserva interiores, cubierta, tejas, canalones, escalera de piedra, puerta, ventanas y balcones. Chimenea y bajantes están activadas en los parámetros, pero sus reglas de colocación no encontraron sitio en esta configuración: no están presentes y esta prueba no valida su física. La calidad de esta prueba es **Trabajo**: no prueba desgaste fino ni grietas booleanas de Detalle. Los valores de daño son moderados para conservar suficiente edificio. No equivale a poner todos los deslizadores al máximo.

## Preparar y calcular otra prueba

1. En la casa, configura el edificio y pulsa **Actualizar**. Después usa **Preparar casa diseñada / zona**. El cálculo trabaja sobre una copia sin mortero; el original permanece editable.
2. En el laboratorio, vuelve al fotograma 1. Selecciona las piezas con Mayús o B; Alt+Z permite seleccionar las ocultas. El panel indica cuántos cuerpos son móviles.
3. Para limitar el coste, ajusta **Límite de piezas** y pulsa **Simular solo la selección; resto como soporte**. Admite hasta 2.048 piezas seleccionadas; el ejemplo aislado conserva su máximo de 256 ladrillos. Este máximo no garantiza que cualquier geometría quepa en memoria.
4. Opcionalmente prepara la rotura de hasta 32 ladrillos seleccionados. Es una prefractura de dos mitades; la casa máxima de esta entrega no añade esta operación a sus miles de cuerpos.
5. Configura dirección XYZ, velocidad, radio y masa; selecciona el blanco y pulsa **Añadir impacto dirigido**. El lanzamiento queda libre tras acelerarse. El empuje continuo impone movimiento, no una fuerza calibrada.
6. Pulsa **Simular derrumbe**. Otro proceso de Blender realiza el cálculo. El panel muestra progreso; **Esc** cancela el proceso hijo. No pulses reproducir en el laboratorio si quieres mantener esta protección: la reproducción directa de Blender ejecuta Bullet en la sesión abierta.
7. Al terminar se abre una reproducción nueva. Cambiar el laboratorio no cambia reproducciones anteriores. Para repetir con todos los cuerpos originales, prepara un laboratorio nuevo desde la casa.

La preparación, la simulación y la exportación tienen un límite por proceso de **4.096 MB de memoria residente y 20 minutos**. Si se supera, se detiene únicamente ese proceso y se conserva la fuente. El error muestra una carpeta temporal con el archivo de entrada, `worker.log`, progreso y, cuando lo registra el supervisor, `resource_limit.json`. Guarda tu trabajo antes de cerrar Blender. El límite no reserva memoria ni garantiza estabilidad en otros equipos.

## Optimizaciones y balcones

Los hierros que se cruzan se unen como soldaduras, sin restar tubos finos entre sí. Las soldaduras desactivan la colisión mutua. Los contactos del balcón con el edificio conservan uniones rompibles.

**Optimizar colisiones** conserva la malla visible. Usa envolventes convexas solo cuando su volumen añadido es pequeño: hasta un 5 % en piedra; en madera, hasta un 25 % y un relleno medio de 0,1 mm. Las concavidades mayores se conservan. Es una aproximación del contacto, no una simplificación visual.

**Reducir uniones redundantes** conserva las soldaduras y la conectividad del conjunto con menos restricciones. Puede cambiar la rigidez y el patrón de derrumbe; no reproduce resistencia de materiales real. **Equilibrada** utiliza 12 subpasos y 30 iteraciones; **Alta**, 40 y 60. El terreno pasivo se agrupa conservando su superficie.

## Exportar el fotograma elegido

En la reproducción, elige el fotograma y pulsa **Exportar fotograma físico a STL**. La exportación excluye el proyectil y el suelo de seguridad; conserva el terreno de la maqueta y los escombros. No exportes la escena completa con un exportador genérico si no quieres incluir esos auxiliares.

**Resolución STL (mm)** controla la unión por vóxeles, con 0,35 mm como valor inicial. Puede suavizar o eliminar detalles más pequeños y cerrar separaciones de tamaño parecido. No reconstruye mortero arquitectónico: une el volumen del resultado físico. Los fragmentos separados pueden quedar como sólidos independientes dentro del mismo STL.

El exportador comprueba cierre, triángulos no degenerados y volumen positivo antes de escribir el STL. El archivo se escribe en mm. Un resultado cerrado todavía necesita orientación, soportes y revisión en el laminador; no se ha realizado una impresión física de esta entrega.

## Alcance de la carga

La generación produjo 390.980 caras expandidas. La preparación creó 4.779 cuerpos antes de agrupar terreno, con 16.622 uniones y 835.631 caras. Se resolvieron 362 cruces soldados de hierro. Cuatro recortes necesitaron un desplazamiento numérico de milésimas de milímetro del cortador temporal; la casa original no se desplazó.

La simulación de toda la arquitectura y la prueba con aproximadamente 3.000 cuerpos móviles superaron el límite de memoria al comenzar el segundo fotograma. No se consideran pruebas superadas. La entrega acota el movimiento a 2.048 cuerpos contando el proyectil, y conserva el resto de la casa como apoyo pasivo. Los informes reproducibles están en `reports/stress_max_*.json`.

La reproducción guarda poses cada cuatro fotogramas e interpola linealmente. Permite inspección y exportación; no conserva una caché física editable ni captura todos los contactos entre muestras. No hay pulverización, astillas adaptativas, arena dinámica ni fractura automática de cada ladrillo.


Resultado medido: 96 fotogramas, 2.048 cuerpos móviles incluido el proyectil, 2.036 objetos animados, 1.102 s de proceso y 3.020 MB de pico residente. Predominan asentamientos y desplazamientos pequeños; no es una demostración de derrumbe generalizado. El STL entregado usa 0,50 mm y contiene 6.437.706 triángulos: exportación en 46 s con 2.323 MB. La unión a 0,35 mm superó el límite de memoria y no se entrega como validada.
