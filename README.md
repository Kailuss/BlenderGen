# RuinOS — proyecto modular para Blender

El código activo está en `src/ruinas_panel/`. Los módulos separan geometría, estructura, generación/caché e interfaz. Cada función contiene un contrato breve `IA:`. Las versiones anteriores permanecen en `../outputs/`.

La revisión actual incorpora la casa completa del ZIP aportado: chimenea desde planta
baja, tejas de media caña, hastiales con entramado y escalera de piedra con relieve.
La v0.32 corrige solapes de tejas, incorpora encuentro cerámico de chimenea,
bajantes por secciones y planos interiores iniciales. Entrega y límites en
[docs/V032.md](docs/V032.md).

La v0.32.5 añade tabiques de tablas continuas y un laboratorio experimental de
estructura completa sin mortero, con encajes y uniones rompibles. Consulta
[el manual](docs/MANUAL_ESTRUCTURA.md) y [sus límites](docs/V0325.md): el resultado
físico todavía no se convierte automáticamente en un sólido imprimible.

## Usarlo en Blender

**Uso normal:** guía completa en [USERGUIDE.md](USERGUIDE.md). En resumen: instala `dist/ruinas_panel_v0327.zip` desde Preferencias → Complementos → Instalar desde disco, actívalo y abre Vista 3D → N → Ruinas. Puedes abrir un .blend de v0.20: conserva los campos guardados. No ejecutes su antiguo `generador_muro.py`, porque volvería a registrar la versión anterior.

**Desarrollo:** abre `tools/load_in_blender.py` como archivo en el editor de texto de Blender y pulsa Ejecutar script. Repite tras editar un módulo: limpia callbacks y caché, recarga el paquete y mantiene los parámetros guardados. No es necesario volver a empaquetar ni reiniciar Blender. Usa solo una copia del addon activa.

El lanzador necesita la carpeta completa `ruinas`; los .py ya no funcionan aislados. No se concatenan módulos con `exec` ni se mantienen copias separadas de la lógica.

## Comandos de desarrollo

Desde esta carpeta, con Python 3.11 o posterior:

```powershell
python dev.py check
python dev.py find grieta
python dev.py find carve_rectangle
python dev.py test --case basic_draft
python dev.py test --case door_windows_work
python dev.py test
python dev.py test --update-expected
python dev.py test --baseline ../outputs/muro_20/generador_muro.py
python dev.py pack
python dev.py pack --project
python dev.py calibrate
```

Si `python` no está en PATH, usa la ruta completa de tu intérprete (3.11 o posterior).

`check` valida sintaxis, contratos y tres grupos de pruebas de cálculo puro, sin Blender. `find` consulta el AST sin cargar todas las fuentes en el chat. `test --case` limita el trabajo a un escenario; sin ese argumento ejecuta cuatro. `--blender <ruta>` permite elegir otra instalación. Los logs y resultados JSON se guardan en `reports/`.

`test` exige que cada pieza generada cierre (sin aristas abiertas) y que ninguna grieta reduzca una pieza por debajo de la mitad de su tamaño, y compara digests y caras degeneradas con `reports/expected.json`. Si la versión de Blender es otra, avisa y omite la comparación. `test --update-expected` acepta la geometría actual como nueva referencia: úsalo solo tras revisar render y cierre de un cambio de geometría intencionado.

`test --baseline` compara vértices redondeados a 6 decimales, caras y nombres contra el monolito, con semilla de ruido de Blender controlada para la prueba. No compara renders píxel a píxel ni demuestra equivalencia de todas las combinaciones posibles. Cada escenario también se regenera desde caché y debe coincidir exactamente.

`calibrate` genera `dist/placa_prueba_resina.stl` y su leyenda `.md`: ranuras en V de 0,05 a 0,40 mm, profundidades de 0,10 a 0,80 mm, pivotes de 0,2 a 1,0 mm y dos piedras reales agrietadas. Imprímela con la misma orientación que los muros, porque en caras verticales el detalle depende de la altura de capa. Con lo que se vea tras imprimar se ajusta `config.CRACK_PRINT`.

`pack` crea solo el addon, con rutas portables y sin renders ni cachés. No ejecuta Blender: ejecuta la prueba relevante antes de distribuirlo.
`pack --project` añade un segundo ZIP con el proyecto, documentación, habilidad y pruebas.

## Agente especializado en este mismo chat

Se entrega como habilidad **ruinas-dev**, con instrucciones de proyecto y herramientas deterministas. No es un modelo nuevo ni un proceso autónomo que trabaje sin instrucciones.

Puedes escribir ahora:

> Usa la habilidad `ruinas/agent/ruinas-dev/SKILL.md` y continúa con las grietas, manteniendo la densidad actual.

Si está descubierta en el selector, basta con `$ruinas-dev` y la petición. La copia preparada está en `agent/ruinas-dev/`; para descubrimiento local se coloca esa carpeta bajo `.agents/skills/` del directorio de trabajo. No hace falta una API key ni otro chat. La guía raíz `AGENTS.md` dirige a los módulos aunque no se use el selector.

La instalación de habilidades y la carga gradual de instrucciones están descritas en la [documentación oficial de habilidades](https://learn.chatgpt.com/docs/build-skills); la guía persistente usa [AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md).

## Coste y límites

Esta reorganización reduce búsquedas, contexto repetido y pasos manuales de edición. No garantiza un porcentaje de ahorro de tokens ni acelera por sí sola los operadores de Blender. `docs/ARCHITECTURE.md` permite localizar el cambio y `docs/STATUS.md` recoge limitaciones actuales. El aumento de resolución sigue siendo una decisión explícita; la prioridad es lowpoly.

Ensayo de ladrillos 0.32.6: [manual de impacto, selección múltiple y huecos](docs/MANUAL_LADRILLOS.md). Entrega local en `dist/ruinas_v0326_completo.zip`.

La v0.32.7 corrige la vista entre escalas y el traslado de la casa; añade impactos dirigidos, empuje y prefractura con juntas rompibles. [Manual de impactos](docs/MANUAL_IMPACTOS.md). Entrega: `dist/ruinas_v0327_completo.zip`.
