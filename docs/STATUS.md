# Estado del proyecto

Base: v0.20, convertida a paquete modular v0.21. El usuario prioriza modelos lowpoly, mampostería coherente y edición fácil. Actualización (2026-09-25): el destino es la impresión en resina, así que se prioriza el detalle imprimible y se aceptan cambios de geometría revisados.

Ya existe: perfiles Tabique/Pared/Muralla; ruina baja/una/dos plantas; Ninguna/L/U/Habitación; ventanas por pared con apoyo; puerta de madera con picaporte; vigas alojadas; derrumbes escalonados; daño de agujeros, grietas ramificadas; tierra/grava y escombros asentados.

Límites conocidos: el coste de subdivisiones, operadores y booleanos sigue siendo alto al regenerar habitaciones. Modularizar no elimina ese coste. Borrador omite grietas finas. No hay suelo de tablones, cubierta, simulación física completa de escombros ni ensamblaje mecánico de módulos.

Las alturas 27/52/102 mm son presets de diseño, no garantías sobre reglas oficiales de juegos. No se ha hecho una prueba física de impresión.

Límites demostrados en Blender 5.2.2 (2026-09-25; detalle en `docs/AUDIT.md`), heredados de v20:

- En L/U/habitación, las grietas de las paredes de retorno se tallan en la cara de junta. Resuelto después: se tallan en la cara exterior de cada tramo, con trazo quebrado que se afina.
- Una grieta puede dejar una piedra reducida a una esquirla (`door_windows_work`, `hilada 06.05`). Resuelto después: se revierte la rama si el booleano quita más del 25 % del volumen.
- «Preparar sólido» reutiliza la geometría de vista previa si ambas calidades coinciden. Resuelto después: la caché se separa por modo; la primera exportación tras una vista previa reconstruye (+40–80 % de tiempo).
- La primera generación tras cargar otro archivo falla con `ReferenceError`. Resuelto después: handlers de carga y deshacer sueltan las referencias.
- El coste de cada bisel crece de forma lineal con el número de objetos (2 ms → 47 ms), así que el total es cuadrático. Resuelto después: los modificadores se aplican en una escena de taller (habitación en Borrador: 74 s → 7 s, misma geometría).

Borrador y Trabajo muestran solo la estructura; desgaste (tres niveles), grietas y escombros aparecen en Detalle. El derrumbe tiene silueta irregular dependiente de la semilla.

El sólido exportable se une con Manifold y conserva el detalle de la fuente (antes, el remallado vóxel de 0,32 mm borraba grietas y vetas).

Las pruebas de migración están en `reports/`; los resultados históricos de cierre de malla v20 están en `../outputs/muro_20`. Para cambios posteriores de geometría debe renovarse la validación correspondiente.
