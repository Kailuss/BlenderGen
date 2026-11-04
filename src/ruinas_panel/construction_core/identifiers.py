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


def opening(wall,floor,band,left_axis,right_axis):
    'IA: Hueco entre dos ejes de viga de un muro, en una banda de segmentos (C5-6).'
    return segment(wall,floor,band,left_axis).replace('seg.','opening.',1)+'-'+str(int(right_axis))


def lintel(wall,floor,band,left_axis,right_axis):
    'IA: Dintel que salva el hueco entre dos ejes; apoya en las jambas de esos ejes (C5-6).'
    return opening(wall,floor,band,left_axis,right_axis).replace('opening.','lintel.',1)


def layout_key(kind,course,index):
    'IA: Clave de construcción desde el aparejo (tipo, hilada, índice), independiente del nombre de Blender (C5-5).'
    if not kind or any(type(v) is not int or v < 0 for v in (course,index)):
        raise ValueError('Tipo, hilada o índice inválido')
    return f'{quote(str(kind),safe=chr(95))}.c{course}.i{index}'


def tag(ob,kind,course,index):
    'IA: Guarda en el objeto su posición de aparejo para que el registro causal no dependa del nombre.'
    ob['layout_kind']=kind;ob['layout_course']=int(course);ob['layout_index']=int(index)
    return ob


MASONRY_ROLES={'stone':'SILLAR','mortar':'NUCLEO','pier':'SILLAR','found':'CIMENTACION','step':'CIMENTACION'}


def role(kind):
    'IA: Papel de fábrica (C5-3) desde el tipo de aparejo: sillar, núcleo o cimentación; None si el tipo no es de fábrica.'
    kind=str(kind or '')
    return next((value for prefix,value in MASONRY_ROLES.items() if kind.startswith(prefix)),None)
