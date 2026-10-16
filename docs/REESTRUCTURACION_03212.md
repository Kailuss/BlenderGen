# Reestructuración incremental: decisiones y dependencias

El briefing aportado propone separar el edificio lógico de su representación geométrica. Estoy de acuerdo: debe hacerse por adaptadores y con regresiones de cada etapa. Reescribir simultáneamente geometría, física y exportación impediría distinguir qué cambio provoca un fallo.

## Referencias contrastadas

El equipo de THE FINALS describe módulos que combinan geometría con datos auxiliares y reglas de dependencia: ventanas requieren paredes y los suelos comparten cotas. También separa identificación de habitaciones y estilo. Aplicamos ese principio al descriptor y al grafo nominal de Ruinas; no copiamos su tecnología de destrucción ni atribuimos al addon su rendimiento. [Artículo técnico de SideFX](https://www.sidefx.com/community/making-the-procedural-buildings-of-the-finals-using-houdini/).

BuildingNodes organiza la generación mediante paneles/estilos y una base de edificio. Sirve como referencia para separar reglas reutilizables de la forma, no como demostración de física o exportación imprimible. [Repositorio del autor](https://github.com/Durman/BuildingNodes).

La gramática de Müller y colaboradores describe refinamiento jerárquico de formas. Refuerza la conveniencia de representar paredes, plantas y vanos antes de materializar piezas; no resuelve por sí sola contactos entre miles de ladrillos. [Procedural Modeling of Buildings, 2006](https://doi.org/10.1145/1179352.1141931).

## Qué se conserva y qué se adapta

| Área | Decisión | Dependencias |
|---|---|---|
| Primitivas, vetas, erosión, fractura y materiales | Conservar, con pruebas de cierre y aspecto | Calidad, semillas locales, mm |
| Cotas y aparejo | Extender `layout` a tres niveles | Forjados, vanos, escaleras, chimenea |
| Cubierta | Generadores especializados: inclinada y torreón | Muros y cotas; opciones propias |
| Daño de tejado | Región pura compartida | Tejas, apoyos, madera, escombros |
| Vanos | Cuotas y medidas independientes; IDs por fachada/planta/familia | Pilares, escaleras, apoyo y techo de planta |
| Laboratorio | Trabajador aislado; mejorar filtrado y booleanas | Copias cerradas, contactos, presupuestos |
| Exportación | Fusión explícita del fotograma y auditoría | Reproducción en unidades originales |
| Modelo arquitectónico | Descriptor/grafo como adaptador | Reglas actuales siguen siendo autoridad geométrica |

## Implementado en 0.32.12

`structure/building_definition.py` describe dimensiones, plantas, semillas, cubierta y origen de construcción. Genera entidades nominales de paredes, habitaciones de planta baja, vanos, escaleras y partes de cubierta. Los IDs de vanos no dependen de enumerar globalmente todas las fachadas. El grafo distingue cubierta inclinada de terraza almenada y registra el acceso entre plantas y a la terraza.

`structure/damage_regions.py` contiene el campo de daño compartido y no importa Blender. Los controles de desgaste fino permanecen separados. La cimentación coloca el conjunto respecto al terreno; el descriptor identifica ese origen y conserva cotas arquitectónicas locales.

El grafo todavía no decide qué cuerpos Bullet conectar. Esas conexiones siguen derivándose de la geometría preparada y se validan por separado. Una relación arquitectónica nominal no equivale a un apoyo físico demostrado.

## Siguiente migración, pendiente

1. Llevar entidades y relaciones a un paquete `model` cuando su contrato esté probado por el piloto de paredes/vanos. Asignar `generated_from` a piezas, variantes, rangos y fragmentos sin sustituir nombres que hoy determinan semillas.
2. Registrar regiones sucias y reconstruir solo dependencias afectadas. Un vano invalidará pared, carpintería y alojamientos locales; no debería invalidar una cubierta alejada.
3. Materializar para física solo regiones activas y vecinos de soporte. Hoy se prepara todo el edificio antes de limitar móviles: es una oportunidad de ahorro mayor que aumentar RAM.
4. Añadir rotura específica por familia y reconstrucción de juntas para impresión. Los multiplicadores actuales cambian resistencia de uniones; no hacen deformables los materiales.

Cada fase necesita comprobar compatibilidad de ajustes, fuente intacta, dimensiones entre etapas, cierre, aspecto y consumo con el mismo caso. No se elimina geometría válida para ocultar un encaje fallido.
