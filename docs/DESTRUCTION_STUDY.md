# Destrucción, física y exportación — estudio de 2026-10-04

## Hallazgos del código local

`services/export.py` ya fusiona copias por bandas de altura de 20 mm y lotes de hasta 60.000 caras. Después reduce los resultados mediante un árbol de uniones de hasta cuatro operandos. No hace una única operación indiscriminada sobre toda la casa. Las bandas actuales son lotes de cálculo; no son plantas desmontables.

La validación final rechaza componentes desconectados apreciables. Una operación booleana puede terminar y aun así producir un resultado que no cumpla ese contrato. El remallado vóxel de respaldo puede perder detalle; tampoco es garantía de reparar apoyos inexistentes. Los errores de soporte, de topología y de coste deben medirse por separado.

## Referencias primarias consultadas

- [Cell Fracture, código de Blender](https://github.com/blender/blender-addons/blob/main/object_fracture_cell/fracture_cell_setup.py): `cell_fracture_boolean` intersecta cada celda con el objeto de origen, limpia geometría y puede separar islas. Es útil para fracturar una pieza individual; no elimina la necesidad de booleanas. Este repositorio es un archivo histórico, no una comprobación de compatibilidad con Blender 5.2.
- [Bullet Constraints Builder](https://github.com/KaiKostack/bullet-constraints-builder): crea conexiones entre cuerpos y umbrales de rotura según materiales, representando dependencias entre pilares, muros, vigas y losas. Su planteamiento respalda modelar uniones/apoyos antes de simular. No se ha instalado ni validado el complemento en nuestro Blender.
- [Consejos oficiales de cuerpos rígidos](https://docs.staging.blender.org/manual/en/latest/physics/rigid_body/tips.html): el índice consultado del manual 5.2 advierte de inestabilidad con objetos pequeños y recomienda aplicar escala cuando no se anima. La página completa no fue accesible desde la herramienta; no se basa ninguna cifra de calibración en ella.

No se ha copiado código de estos proyectos ni se ha incorporado un motor nuevo.

## Recomendación para Ruinas (inferencia de diseño)

Conservar la construcción por piezas. Separar tres representaciones: construcción intacta con apoyos, copias simplificadas de simulación y geometría detallada para impresión. Simular no garantiza superficies fusionadas ni contacto suficiente para resina; una pieza apoyada visualmente puede seguir siendo un componente desconectado.

1. Identificar módulos semánticos: planta baja, planta alta, cubierta y escombros. Asignarlos durante construcción, sin inferirlos solo del centro de cada objeto. Resolver explícitamente elementos que cruzan plantas: escalera, pilares y chimenea.
2. Añadir conectividad y apoyos. Una pérdida de soporte debe afectar a lo que descansa sobre él antes de añadir restos. Conservar un modo determinista sin física.
3. Prototipar física únicamente sobre una pared, una viga y un paño de forjado, con colisionadores simplificados. Calibrar escala, márgenes, pasos e iteraciones; evitar solapes iniciales. Hornear transformaciones sobre copias y aplicarlas a la representación detallada. No simular miles de caras de veta.
4. Exportar módulos imprimibles independientes, cada uno con cierre, espesor y conectividad comprobados. Diseñar superficies de asiento y encajes cuando se adopten plantas desmontables. No cortar automáticamente la casa final por alturas: podría cortar el hogar o generar piezas sin apoyo.
5. Comparar el exportador actual con lotes por vecindad espacial y presupuesto de caras, validando cada etapa. Un orden secuencial sobre un acumulado creciente puede ser más caro que un árbol; no se presupone una mejora por reducir el número de operandos a dos.

## Experimento propuesto, todavía no implementado

Mismos edificios, semillas, calidades y daños: (A) exportación actual, (B) módulos semánticos, (C) módulos y árbol por vecindad. Registrar tiempo por etapa, pico de memoria, caras, componentes, cierre después de triangulación y pérdida de relieve. Detener y conservar el primer lote que falla; nunca borrar fragmentos relevantes para aparentar éxito.

Aceptar física solo si mejora el aspecto del derrumbe sin empeorar control, reproducibilidad ni preparación imprimible. Empezar por asentar escombros locales; evaluar después derrumbes de forjado. No reemplazar aún toda la destrucción ni prometer que la física solucionará la exportación.
