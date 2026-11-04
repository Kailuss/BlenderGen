"""Definición única del asiento de viga en fábrica (C5-3).

Antes había tres: los rayos del constructor y la auditoría, el contacto nominal del
plan (`floor_frame.beam_skeleton`, 4,2 × 3 mm fijos) y la banda de piedra del ensayo
de daño. Todas leen ahora este módulo. Es un criterio geométrico, no una ley resistente.
"""
OFFSETS_MM=(-1.5,0.0,1.5)
VERTICAL_OFFSET_MM=-2.7
MINIMUM_HITS=2
# Sección de las vigas de planta y forjado (ancho × canto en mm de modelo).
BEAM_WIDTH_MM=4.2
BEAM_HEIGHT_MM=4.7
# Cota del eje de viga bajo la base de planta: habitación y fachada sola.
BEAM_DROP_MM={'ROOM':3.6}
FACADE_BEAM_DROP_MM=2.5
# Alojamiento tallado en la fábrica: semiancho, bajada bajo el eje y semicanto nominal.
POCKET_HALF_WIDTH_MM=2.5
POCKET_BELOW_MM=2.0
POCKET_HALF_HEIGHT_MM=2.25
# Vuelo de la cabeza de viga fuera de la cara del muro.
BEAM_OVERHANG_MM=4.0
# Banda de piedra bajo el asiento (relativa al eje) y semiancho de medida del ensayo de daño.
BEARING_BAND_MM=(-4.5,-2.7)
AUDIT_HALF_WIDTH_MM=2.6


def beam_z(base,layout_mode='ROOM'):
    'IA: Cota del eje de viga para una base de planta; única fuente de la bajada 3,6/2,5 mm que usaban constructor, forjado, escalera y ensayos.'
    return base-BEAM_DROP_MM.get(layout_mode,FACADE_BEAM_DROP_MM)


def pocket(x,z):
    'IA: Caja X/Z del alojamiento tallado alrededor del eje (x,z); misma caja en muro frontal y trasero.'
    return (x-POCKET_HALF_WIDTH_MM,x+POCKET_HALF_WIDTH_MM,z-POCKET_BELOW_MM,z+POCKET_HALF_HEIGHT_MM)


def embed_length(thickness):
    'IA: Distancia del eje del muro al extremo de la viga pasante: medio grosor más el vuelo de cabeza.'
    return thickness/2+BEAM_OVERHANG_MM


def plan_seat(thickness):
    'IA: Contacto nominal del plan derivado de la geometría construida: ancho de viga y profundidad igual al grosor que atraviesa.'
    if not thickness>0:raise ValueError('Grosor de muro inválido')
    return {'seat_width_mm':BEAM_WIDTH_MM,'seat_depth_mm':float(thickness)}


def samples(x,z):
    'IA: Tres puntos en mm bajo la viga, compartidos por constructor y auditoría de ambos extremos.'
    return [(x+dx,z+VERTICAL_OFFSET_MM) for dx in OFFSETS_MM]


def supported(hits):
    'IA: Exige exactamente tres resultados y dos contactos; no sustituye área, longitud de asiento ni capacidad.'
    hits=list(hits)
    if len(hits)!=len(OFFSETS_MM):raise ValueError('Asiento requiere tres muestras')
    return sum(bool(hit) for hit in hits)>=MINIMUM_HITS


def bearing_overlap(lo_z,hi_z,z):
    'IA: Indica si una pieza con intervalo Z [lo_z,hi_z] corta la banda de piedra bajo el asiento de eje z.'
    return lo_z<z+BEARING_BAND_MM[1] and hi_z>z+BEARING_BAND_MM[0]
