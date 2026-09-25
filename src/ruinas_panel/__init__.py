"""Complemento Ruinas; API pública pequeña, geometría en módulos especializados."""

bl_info = {
    'name': 'Ruinas — Muro de fantasía',
    'author': 'Codex',
    'version': (0, 21, 0),
    'blender': (5, 0, 0),
    'location': 'Vista 3D > N > Ruinas',
    'category': 'Add Mesh',
}

__all__ = ['register', 'unregister', 'generate', 'make_solid']


def register():
    """IA: importa integración Blender solo al activarse; mantiene importables los cálculos puros."""
    from .registration import register as activate
    return activate()


def unregister():
    """IA: delega limpieza RNA, caché y timers en el mismo módulo que registró el addon."""
    from .registration import unregister as deactivate
    return deactivate()


def generate(context, settings, quality=None):
    """IA: entrada pública estable; lógica y estado permanecen en services/generation.py."""
    from .services.generation import generate as build
    return build(context, settings, quality)


def make_solid(context, voxel=None):
    """IA: exporta mediante el servicio; no implementes otra ruta de fusión en esta fachada."""
    from .services.export import make_solid as fuse
    return fuse(context, voxel)
