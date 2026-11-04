"""Criterio geométrico heredado de asiento; no es una ley resistente."""
OFFSETS_MM=(-1.5,0.0,1.5)
VERTICAL_OFFSET_MM=-2.7
MINIMUM_HITS=2


def samples(x,z):
    'IA: Tres puntos en mm bajo la viga, compartidos por constructor y auditoría de ambos extremos.'
    return [(x+dx,z+VERTICAL_OFFSET_MM) for dx in OFFSETS_MM]


def supported(hits):
    'IA: Exige exactamente tres resultados y dos contactos; no sustituye área, longitud de asiento ni capacidad.'
    hits=list(hits)
    if len(hits)!=len(OFFSETS_MM):raise ValueError('Asiento requiere tres muestras')
    return sum(bool(hit) for hit in hits)>=MINIMUM_HITS
