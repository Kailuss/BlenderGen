# Estado del proyecto

Base: v0.20, convertida a paquete modular v0.21. El usuario prioriza modelos lowpoly, mampostería coherente y edición fácil.

Ya existe: perfiles Tabique/Pared/Muralla; ruina baja/una/dos plantas; Ninguna/L/U/Habitación; ventanas por pared con apoyo; puerta de madera con picaporte; vigas alojadas; derrumbes escalonados; daño de agujeros, grietas ramificadas; tierra/grava y escombros asentados.

Límites conocidos: el coste de subdivisiones, operadores y booleanos sigue siendo alto al regenerar habitaciones. Modularizar no elimina ese coste. Borrador omite grietas finas. No hay suelo de tablones, cubierta, simulación física completa de escombros ni ensamblaje mecánico de módulos.

Las alturas 27/52/102 mm son presets de diseño, no garantías sobre reglas oficiales de juegos. No se ha hecho una prueba física de impresión.

Límites demostrados en Blender 5.2.2 (2026-09-25; detalle en `docs/AUDIT.md`), heredados de v20:

- En L/U/habitación, las grietas de las paredes de retorno se tallan en la cara de junta.
- Una grieta puede dejar una piedra reducida a una esquirla (`door_windows_work`, `hilada 06.05`).
- «Preparar sólido» reutiliza la geometría de vista previa si ambas calidades coinciden.
- La primera generación tras cargar otro archivo falla con `ReferenceError`.
- El coste de cada bisel crece de forma lineal con el número de objetos (2 ms → 47 ms), así que el total es cuadrático.

Las pruebas de migración están en `reports/`; los resultados históricos de cierre de malla v20 están en `../outputs/muro_20`. Para cambios posteriores de geometría debe renovarse la validación correspondiente.
