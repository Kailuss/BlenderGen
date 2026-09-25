# Edición de Ruinas

- Fuente única: `src/ruinas_panel/`. No edites scripts embebidos ni ZIP como código fuente.
- Consulta `docs/ARCHITECTURE.md` para elegir módulo; `python dev.py find <símbolo o tema>` devuelve ubicación y contrato. Lee solo el módulo y sus dependencias relevantes.
- Unidades de geometría: mm. Conserva nombres de objetos, semillas locales y claves RNA: afectan caché, grietas y archivos guardados.
- Cada función tiene un docstring `IA:` con su contrato. Actualízalo si cambia; evita instrucciones genéricas repetidas. No uses anotaciones diferidas en clases de propiedades Blender.
- `runtime` contiene estado de sesión; importa el módulo, no sus valores mutables. Geometría no importa interfaz. Los datos constantes viven en `config`.
- Verifica cambios pequeños con `python dev.py check` y pruebas del subsistema. Para geometría, caché, registro o empaquetado usa `python dev.py test`. Para comparar contra v20: `--baseline ../outputs/muro_20/generador_muro.py`.
- Blender debe ejecutarse con `--python-exit-code 1`. Un render bonito no prueba cierre de malla; una malla cerrada no prueba buen aspecto. Comprueba ambos cuando cambie la geometría.
- No subas densidad por defecto para esconder artefactos. Mide tiempo, caras y resultado con los mismos parámetros. Borrador omite grietas booleanas por diseño.
- Desarrollo interactivo: ejecutar `tools/load_in_blender.py` recarga módulos y limpia timers/caché. Empaquetar: `python dev.py pack`.
- Alcance actual y limitaciones en `docs/STATUS.md`; documenta nuevos límites demostrados sin reescribir el historial del chat.
