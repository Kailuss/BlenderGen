"""Identificadores de piezas y apoyos sin ambigüedad de separadores."""
from urllib.parse import quote


def piece(wall,source_key):
    'IA: Identidad por pared y clave de construcción conservada; no usa punteros ni orden de objetos.'
    return 'piece/'+quote(str(wall),safe='')+'/'+quote(str(source_key),safe='')


def segment(wall,band,axis):
    'IA: La banda inferior 0 sostiene el forjado 1; axis es el ordinal previo a filtrado.'
    return f'seg.{wall}.{band}.{axis}'


def beam(level,axis):
    'IA: Identidad de viga por forjado y candidato previo a vanos/espaciado.'
    return f'beam.{level}.{axis}'
