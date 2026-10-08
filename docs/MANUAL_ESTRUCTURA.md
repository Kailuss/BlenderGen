# Ruinas — ensayo estructural sin mortero

Este laboratorio experimental incluye la mampostería, carpintería, suelos,
tabiques y cubierta presentes en el modelo generado. Conserva la casa original.
Todavía no produce un sólido imprimible después del derrumbe.

## Abrir la entrega y reproducirla

Abre **ruinas_v0325_estructura_interactiva.blend** con **Cargar interfaz**.
La escena **00 REPRODUCIR** conserva el edificio completo, incluido el tejado.
Pulsa **Espacio** para reproducir los 120 fotogramas guardados. No requiere
instalar el addon ni permitir la ejecución automática de scripts.

Para ver qué ocurre dentro cambia, en el selector de escena de la barra superior,
a **03 INTERIOR**. Muestra la misma simulación ocultando la mampostería y cubierta
solo en esa vista. El travesaño rojo pierde sus uniones en el fotograma 13 y cae
por gravedad. No se retira una pieza mediante una trayectoria animada.

**01 CASA EDITABLE** conserva el generador y **02 LABORATORIO ESTRUCTURAL** los
cuerpos y uniones recalculables. Instala **ruinas_panel_v0325.zip** para usar sus
controles. Pulsa Inicio tras cambiar de escena si necesitas encuadrar.

## Preparar una casa

1. Genera la casa con **Actualizar**. Para comprobar el ensamblaje inicial,
   empieza con **Activar daño** desmarcado y conserva la cubierta.
2. En **Distribución → Zona de física**, elige **Edificio completo**.
3. Ajusta **Fotogramas** y **Resistencia de uniones**. La resistencia es un
   factor artístico de impulso; no son unidades de resistencia de un material.
4. Pulsa **Preparar física de la zona**. La preparación puede tardar: materializa
   las instancias, separa piezas, recorta solapes y construye uniones.
5. Se abre **Ruinas · estructura sin mortero**. Pulsa Inicio para encuadrar.
   Cada tabla, sillar y teja es seleccionable; los vacíos de los vanos permanecen.

## Ensayar la pérdida de unión

1. Selecciona una pieza móvil de la casa. No selecciones el terreno ni un icono
   de unión. El terreno y algunos pies de cimentación permanecen anclados.
2. Pulsa **Soltar uniones seleccionadas**. Las conexiones de esa pieza se
   desactivan en el fotograma 13. La pieza no se desplaza mediante animación.
3. Pulsa **Simular derrumbe** o reproduce desde el fotograma 1.
4. Examina apoyos, huecos y piezas desprendidas. Quitar una unión no obliga a
   caer: una pieza que conserva apoyo puede permanecer en su sitio.
5. Para otro ensayo vuelve a la casa y prepara otro laboratorio. Los resultados
   anteriores permanecen en sus escenas.

El tiempo físico está ralentizado al 20 % para observar el proceso. Al reabrir
un laboratorio, vuelve al fotograma 1 y recalcula: el archivo no conserva
automáticamente la caché de Bullet.

El ejemplo de 3.018 cuerpos es costoso de recalcular: el registro del horneado
completo marca unos 52 minutos. Para ver el resultado usa las escenas de
reproducción; no hace falta ejecutar **Simular derrumbe** otra vez.

## Qué cambia respecto al ensayo anterior

- Los tabiques usan tablas verticales continuas y travesaños posteriores. Ya
  no tienen cortes horizontales que los hacían comportarse como ladrillos.
- La preparación excluye mortero y núcleos de unión. Su función de cohesión se
  representa mediante conexiones entre cuerpos, no mediante un macizo oculto.
- Los recortes adicionales se hacen sobre copias de simulación. La fuente
  procedural conserva sus piezas y su camino habitual de impresión.
- Las tejas agrupadas se separan por componentes conectados.
- Se emplean superficies cóncavas para colisión, no cajas que tapen ventanas,
  puertas o el canal de las tejas. Es más costoso que el antiguo ensayo.
- Las uniones se detectan por proximidad de las superficies dentro de 0,8 mm.
  Esta tolerancia representa juntas pequeñas; no demuestra un apoyo estructural.

## Límites que hay que tener presentes

Las piezas rígidas se desprenden o giran; no se doblan ni se astillan por dentro.
La rotura longitudinal de madera y la fractura interna de sillares requieren
otro nivel de geometría y aún no están implementadas. Los umbrales no están
calibrados para representar construcciones reales.

Las masas están multiplicadas por un factor común de 10.000 para evitar que el
mínimo de 1 gramo de Blender iguale el peso de piezas muy diferentes. Los umbrales
usan esas mismas masas normalizadas. Los valores de masa visibles en el laboratorio
no son los kilogramos reales de la maqueta.

Las uniones son fijas y rompibles: todavía no distinguen tracción, compresión,
cizalla o articulaciones de carpintería. Un resultado visual convincente no es
una certificación de estabilidad. Los ensayos antiguos por estancia permanecen
como compatibilidad; no equivalen al laboratorio del edificio completo.

## Mortero después de la simulación

La solución prevista es recalcular los contactos en la posición final y crear
puentes de material locales solo en los encuentros que se quieran conservar.
Hay que limitar su espesor y longitud, mantener vanos libres y comprobar los
componentes conectados antes de fusionar. Las piezas separadas deben exportarse
como piezas independientes o recibir un soporte de impresión explícito.

No se debe recuperar el mortero original: rellenaría huecos que ya no existen
en la construcción derrumbada. Por eso este laboratorio no ofrece **Aceptar
para exportación**. La reconstrucción de esos contactos imprimibles está pendiente.

## Referencias del motor

- [Cuerpos rígidos: movimiento sin deformación](https://docs.blender.org/manual/en/latest/physics/rigid_body/introduction.html).
- [Uniones y umbral de impulso](https://docs.blender.org/api/main/bpy.types.RigidBodyConstraint.html).

La elección de la tolerancia, el montaje y los umbrales es una decisión de diseño
de Ruinas, no una recomendación cuantitativa de esas referencias.
