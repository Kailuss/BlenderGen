"""Activación del daño sin modificar los valores guardados del usuario."""

DISABLED_VALUES = {
    'collapse': 0, 'hole_count': 0, 'hole_damage': 0,
    'floor_damage': 0, 'roof_damage': 0, 'wood_damage': 0,
    'wear': 0, 'cracks': 0, 'rubble_amount': 0, 'iron_mode': 'TWIST', 'iron_damage': '0',
}


class IntactSettings:
    """IA: Vista de lectura sin daño; conserva dimensiones, semillas y ajustes RNA originales."""

    def __init__(self, source):
        """IA: Mantiene referencia al ajuste original; no escribe propiedades RNA."""
        self.source = source

    def __getattr__(self, name):
        """IA: Neutraliza exclusivamente controles de daño y delega el resto."""
        if name in DISABLED_VALUES:
            return DISABLED_VALUES[name]
        return getattr(self.source, name)


def effective_settings(settings):
    """IA: Archivos anteriores mantienen daño activo; apagarlo no borra sus intensidades."""
    return settings if getattr(settings, 'damage_enabled', True) else IntactSettings(settings)
