"""meta — ver docs/ARCHITECTURE.md para contratos y dependencias."""

import json


# Todos los datos de auditoría y estado de la ruina viven en una sola propiedad de escena:
# en Propiedades > Escena > Propiedades personalizadas aparece una entrada en lugar de catorce.
KEY = 'ruinas'
LEGACY = ('ruinas_metricas', 'parametros_muro', 'aparejo_escalonado', 'mortero_retranqueado', 'pilares_generados',
          'huecos_generados', 'huecos_solicitados', 'puerta_generada', 'escombros_generados', 'hiladas_generadas',
          'giros_generados', 'paredes_generadas', 'ventanas_generadas', 'vigas_generadas')


def raw(scene, name):
    'IA: Texto JSON guardado bajo name, o None; sirve para copiar metadatos sin decodificarlos.'
    group = scene.get(KEY)
    return group.get(name) if group is not None else None


def put_raw(scene, name, text):
    'IA: Guarda texto JSON ya codificado bajo name; crea el grupo si falta.'
    if scene.get(KEY) is None:
        scene[KEY] = {}
    scene[KEY][name] = text


def put(scene, name, value):
    'IA: Codifica value como JSON y lo guarda bajo name.'
    put_raw(scene, name, json.dumps(value, ensure_ascii=False))


def get(scene, name, default=None):
    'IA: Valor decodificado de name, o default si no existe.'
    text = raw(scene, name)
    return default if text is None else json.loads(text)


def drop_legacy(scene):
    'IA: Borra las propiedades sueltas de versiones anteriores; los datos se regeneran en la siguiente generación.'
    for name in LEGACY:
        if name in scene:
            del scene[name]
