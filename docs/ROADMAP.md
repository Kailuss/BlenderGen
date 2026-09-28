# Prioridades después de 0.31

La 0.31 se centra en la respuesta del desgaste y sus controles. Los sistemas siguientes
son trabajo pendiente, no funcionalidades incluidas en esa versión.

1. **Construcción antes que decoración.** Definir cimentación, espesores, encuentros,
   apoyos de dinteles, vigas y cubiertas. La decoración debe consumir esa estructura.
   Aceptación: comprobar apoyos y continuidad en perfiles Tabique/Pared/Muralla y
   distribuciones recta/L/U/habitación antes de añadir acabado.
2. **Destrucción por regiones.** Un foco, intensidad y selección de elementos afectados.
   Resolver primero daño a soportes, después pérdida de cubierta y por último escombros
   vinculados al volumen y material retirado. Aceptación: variar el foco conserva la
   estructura fuera de su región; no quedan elementos suspendidos por soportes eliminados.
3. **Mampostería controlada.** Aparejos, familias de tamaños y resolución de esquinas,
   con límites de irregularidad por familia. Aceptación: juntas trabadas, esquinas
   resueltas y dimensiones mínimas, reproducibles con la misma semilla.
4. **Intersecciones resueltas.** Empezar con pocas cubiertas que adapten muros, ventanas
   y madera entre sí. Aceptación: pruebas de encuentros y huecos de cada combinación
   admitida; no ampliar el catálogo sin validar sus uniones.
5. **Jerarquía de detalle.** Controles independientes para deformación general,
   daño arquitectónico y desgaste superficial. Aceptación: cambiar un nivel no
   redistribuye los demás ni invalida cachés ajenas a ese nivel.

Para cada entrega de geometría: comparar aspecto, cierre, tiempo y caras con los mismos
parámetros y semillas. No aumentar densidad por defecto para ocultar defectos. La prueba
de impresión en resina sigue pendiente.
