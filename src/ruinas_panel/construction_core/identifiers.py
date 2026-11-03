"""Identificadores de piezas y apoyos sin ambigüedad de separadores."""
from urllib.parse import quote


def piece(wall,source_key):
    'IA: Identidad por pared y clave de construcción conservada; no usa punteros ni orden de objetos.'
    return 'piece/'+quote(str(wall),safe='')+'/'+quote(str(source_key),safe='')


def segment(wall,floor,band,axis):
    'IA: ID por muro, planta de la viga, banda y ordinal anterior a filtros; bandas de vigas distintas no colisionan.'
    if any(type(v) is not int or v < 0 for v in (floor,band,axis)) or floor < 1:
        raise ValueError('Planta, banda u ordinal inválido')
    return f'seg.{quote(str(wall),safe=chr(95))}.f{floor}.b{band}.{axis}'


def beam(level,axis):
    'IA: Identidad de viga por forjado y candidato previo a vanos/espaciado.'
    return f'beam.{level}.{axis}'
