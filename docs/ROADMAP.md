# Rumbo después de la revisión 0.31

Decisión del usuario (2026-10-03): adoptar el rumbo de `ruinas_analisis_critica.docx`. Este documento recoge trabajo aprobado pendiente, no sistemas ya implementados. El destino es escenografía para miniaturas e impresión en resina: priorizar silueta, daño coherente y detalle imprimible, sin simular toda la construcción real.

## Orden de desarrollo

1. **Construcción intacta verificable.** Separar la activación del daño de la calidad de acabado, conservando compatibilidad con las propiedades guardadas. Probar diez edificios intactos con semillas y parámetros registrados antes de extender la destrucción. Comprobar apoyos, vanos, encuentros, cierre y aspecto.
2. **Modelo previo a las mallas.** Introducir datos de muros, vanos, plantas y planos de cubierta; empezar por vanos y cubierta. Las cotas deben proceder de ese modelo, sin deducir la envolvente a partir de piedras ya dañadas.
3. **Campo de daño único.** Planificar eventos con posición, radio, tipo e intensidad. Muros, forjados y cubierta consultarán el mismo campo espacial; conservar controles independientes para deformación general, daño arquitectónico y desgaste superficial. Un mismo evento debe explicar las pérdidas relacionadas.
4. **Apoyos explícitos.** Registrar identificadores y relaciones de apoyo al construir: muro sobre muro, dintel sobre jambas, viga sobre muro y cubierta sobre solera. Extender la retirada de piezas sin apoyo a piedra, madera y cubierta, sin motor físico. Resolver soportes, pérdida de cubierta y escombros en ese orden; asociar los restos al material perdido y a su zona de caída.
5. **Consolidación acotada.** Al introducir parámetros de eventos, unificar declaraciones de campos y metadatos de caché y dividir la orquestación extensa de construcción. Conservar planificadores puros, instancias, nombres y semillas locales. Documentar las migraciones necesarias.

No ampliar tipos de destrucción sobre los planificadores independientes actuales. Los diagnósticos concretos del Word son hipótesis hasta reproducirlos: comprobar cubierta y apoyos con derrumbe 0,8 y seguir la procedencia de los escombros del tejado. No registrarlos como fallos demostrados sin una prueba contra el código actual.

## Correcciones visuales aprobadas

- **Chimenea:** reducir el saliente e integrarla en el muro; piedra asimétrica con relieve físico, hogar y conducto libres. Resolver el encuentro con las mismas tejas del edificio, eliminando el aspecto de placa metálica. Reservar el refinado costoso para acabado/exportación, sin subir densidad por defecto.
- **Tejas:** conservar la media caña; calcular orientación a partir de la tangente del faldón y solape aritmético entre filas. Verificar espesores y encuentros con chimenea, alero y cumbrera. Adornos opcionales de hierro en cumbrera, anclados y con desgaste coherente.
- **Canalones y bajantes:** mayor presencia, latón abollado, tramos irregulares y juntas visibles; permitir secciones rotas, separadas o ausentes vinculadas al daño. El relieve exportable no puede depender solo del material.
- **Mampostería:** familias de tamaños, aparejos y esquinas trabadas con límites de irregularidad. Puede mejorarse localmente sin esperar al sistema entero.

Estas correcciones siguen pendientes. Integrarlas con el modelo y el daño compartidos, evitando sumar excepciones independientes de destrucción.

## Validación y colaboración

Por entrega de geometría, comparar cierre y aspecto, tiempo, caras y memoria con los mismos parámetros y semillas. Verificar caché, instancias, guardado/reapertura y exportación/reimportación. Piezas cerradas no garantizan una casa fusionada imprimible. La prueba física de resina sigue pendiente.

Solicitar a RafaYafa revisión de exportación y barrido de controles (mínimo, intermedio y máximo), registrando parámetros, semilla y efecto observado. Mantener Trello actualizado separando entregado, validación y pendiente. Publicar cambios validados en `origin/develop` y distinguir futuras entregas con una versión inequívoca; no reutilizar 0.31 para paquetes diferentes.
