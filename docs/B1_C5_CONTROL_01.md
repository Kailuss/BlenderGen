# Orden B1 C5 y Ejercicio 02 primer control

3 de noviembre de 2026. Rama de física `codex/lab-render-v03221`. Este control es parcial: no acredita el cierre de E-1 a E-10 ni de B1-C5. El vídeo entregado se conserva como referencia y no se ha recalculado.

## Decisión sobre el banco

El usuario exige eta <= 0,3 también en el banco, modelando disipación adicional. Se adopta un modelo ideal de contacto unidimensional que reduce la restitución efectiva, conserva momento y contabiliza la energía perdida. No se aplica un recorte de poses. Para masas iguales y restitución solicitada 0,3, la restitución efectiva máxima es sqrt(1,2)-1, aproximadamente 0,095445. La transferencia ideal baja de 0,4225 a 0,3. Un presupuesto inferior al choque completamente inelástico se rechaza: necesita otro mecanismo físico.

Este modelo es una referencia matemática, no una calibración aprobada de Bullet ni un modelo de fractura de mampostería. La implementación pura y el cálculo de masa por área y espesor real pasan sus pruebas. Su integración en las familias finas sigue pendiente.

## Banco observado

`tests/blender_impact_calibration.py` barre razones de masa 0,1, 1 y 10, restituciones 0,1 y 0,3 y 40/160 subpasos. Usa proyectil dinámico antes de tocar el blanco y ausencia de gravedad para aislar la transferencia central. Es un precursor de E-9: no sustituye todavía el panel pequeño ni mide alcance balístico.

La referencia inicial sin disipación adicional falló el límite de error del 15 %: máximo 17,915 %. Activar split impulse no corrigió el resultado. El banco con disipación explícita también mantiene incumplimientos de presupuesto y referencia analítica. Los informes conservan los valores medidos y el script termina con error al incumplirlos. No se han relajado los umbrales.

El código de Bullet combina corrección de penetración e impulso de velocidad según el umbral del split impulse. Es una hipótesis a contrastar para esta desviación, no una causa demostrada de todas las expulsiones de la casa: https://github.com/bulletphysics/bullet3/blob/master/src/BulletDynamics/ConstraintSolver/btSequentialImpulseConstraintSolver.cpp

## Respuestas técnicas provisionales

**R-1.** El Ejercicio 02 guía cinemáticamente los proyectiles durante el trayecto dentro del edificio. Solo cede a dinámica en los frames 57, 97 y 133. Durante el trayecto guiado no pierde velocidad al empujar. `stage_shrapnel_house.py` crea el montaje y `revise_shrapnel_house.py` fija 0,8 m/s. El nuevo argumento `specification` de `impact_physics.launch` permite parámetros explícitos y rechaza PRESS, pero aún no se ha usado para repetir el ejercicio.

**R-2.** El origen es 2200 kg/m³ multiplicados por `impact_mass=20`: densidad esférica nominal 44000, no un material de 45500. La discrepancia con la estimación de 45500 puede proceder del volumen de la esfera poligonal; falta contrastarlo por volumen de malla. La auditoría del archivo 03e mide masas 19624,984375, 25478,568359 y 17068,650391. Los proyectiles tienen restitución 0, fricción 1, amortiguación lineal 0,04 y angular 0,1. Las piezas habituales tienen restitución 0, fricción 1, lineal 0,04 y angular 0,5; el inventario registra excepciones por familia. La hipótesis del diagnóstico con e cercano a 1 no describe la configuración guardada.

**R-3.** La escena editable conserva 40. `shrapnel_worker.precise_scale_solver` fuerza 160 y 60 iteraciones en el hijo que calculó la entrega. No son dos mediciones del mismo estado. Sigue pendiente la comparación de alcance del edificio entre ambas configuraciones; el precursor solo mide desplazamiento a tiempo fijo de dos cuerpos.

**R-4.** Se cuentan 465 cuerpos con masa mínima 0,001: madera 245, tejas 112, piedra 72, piedra entera 6, hierro 23, revoco 4, pilar 1 dos y plomo uno. El listado nominal completo está en `reports/e02_calibration_inventory.json`. La causa inmediata es el suelo impuesto por `max(.001, masa calculada)` y el límite de Blender. No demuestra que las 465 mallas sean degeneradas; decidir eliminación o fusión requiere medirlas individualmente.

**R-5.** El laboratorio toma `config.PHYSICS_DENSITIES` por `physical_role`, con excepción de revoco a 1200. `role()` busca teja/cerámica antes de metal y no identifica plomo explícitamente. Falta rastrear los materiales concretos de cada pieza de plomo antes de corregir la clasificación; no se ha cambiado su densidad a ciegas.

**R-6.** La entrega 05 es reproducción de poses sin simulación rígida activa. 04 conserva también escenas de etapas anteriores; se debe distinguir por escena, no afirmar que todo el archivo carece de cuerpos. Para revisar parámetros debe usarse 03e_laboratorio_entrega.blend, cuyo hash se registra en el inventario.

**R-7.** No hay medición comparable del vídeo completo con/sin humo a 1024 muestras. La prueba anterior de dos frames usó resolución y muestras reducidas y no permite estimar ese coste. El usuario ha renderizado el vídeo; no se dispone de su log de tiempos.

**R-8.** No existe aún un balance energético medido de los tres impactos de la casa. Es posible derivar energía traslacional de masas y diferencias temporales de poses, descontando escala del solver; la energía angular requiere inercia y velocidad angular. También hay que distinguir aportación gravitatoria, impactos sucesivos y trabajo del proyectil guiado. El banco pequeño sí mide el cociente traslacional y energía total de sus dos esferas.

**R-9.** Los parámetros del ejercicio son 240 x 240 mm, muro de 377 mm y cimentación de 16 mm, más cubierta. No es una casa de 170 mm de altura. A lambda=60, los 240 mm representan 14,4 m y el muro 22,62 m; esto es conversión geométrica, no validación de similitud dinámica. Falta medir la altura total y la distribución dimensional de sillares del archivo.

## Vía causal

Se ha comprobado `git diff --stat efa7e21 a7d429a`: solo cambian `reports/b1_c4_t1.json` y `reports/modular.json`; no cambia código. La rama causal continúa en `codex/b1-c4-causal`. Este control no modifica esa rama ni declara resueltos C5-2 a C5-6. Tampoco declara `dirty: false`: el checkout de física contiene informes previos ajenos a este trabajo.

## Pendientes para aceptación

Cerrar la desviación numérica y el presupuesto del banco; integrar materiales, espesores efectivos y disipación en la escena; resolver el inventario de masas mínimas; completar ficha automática, proyectil consumible y auditoría energética. Después repetir Ejercicio 02 y medir sus criterios. Mantener Ejercicio 03 e integración bloqueados por la orden. Responder y entregar el DOCX actualizado al completar el control, con verificación de paginación; este archivo es el registro de trabajo y no sustituye esa entrega.
