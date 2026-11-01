"""Comprobaciones geométricas puras del suelo horizontal de seguridad."""


def below_floor(body_points, floor_points, tolerance):
    'IA: Detecta un cuerpo completamente bajo la cara superior solo si sus cajas mundiales se solapan en XY; fuera de la huella no existe suelo que atravesar. Todas las magnitudes comparten escala.'
    body = tuple(body_points)
    floor = tuple(floor_points)
    if not body or not floor:
        raise ValueError('Se necesitan límites del cuerpo y del suelo.')
    for axis in (0, 1):
        if max(p[axis] for p in body) <= min(p[axis] for p in floor):
            return False
        if min(p[axis] for p in body) >= max(p[axis] for p in floor):
            return False
    return max(p[2] for p in body) < max(p[2] for p in floor) - tolerance
