"""Tolerancias heredadas del aparejo, en mm de modelo; no parámetros Bullet."""
RETURN_STONE_INSET=.18
FRONT_STONE_INSET=.22
COURSE_BOTTOM_INSET=.23
COURSE_TOP_INSET=.25
PIER_TOP_CLEARANCE=.28
PIER_SIDE_GAP=.2
BOUNDARY_EPSILON=.01
JOINT_MIN_GAP=-.05
JOINT_MAX_GAP=1.5
BEAM_SOCKET_WIDTH=5.0
SOCKET_STONE_MARGIN=.3
JOINT_MIN_STONE_WIDTH=BEAM_SOCKET_WIDTH+SOCKET_STONE_MARGIN
# Se conserva el límite histórico: el desplazamiento de cada extremo al eje
# medio no supera 0,75 mm, inferior a la semianchura del alojamiento (2,5 mm).
AXIS_MATCH_TOLERANCE=BEAM_SOCKET_WIDTH*.3
AXIS_WARNING_FRACTION=.8
FRONT_CACHE_SIZE=16
