"""Ejecuta este archivo desde el editor de texto de Blender para desarrollar."""
from pathlib import Path
import importlib
import sys

import bpy


def load():
    """IA: descarga callbacks antiguos antes de recargar; conserva propiedades RNA de la escena."""
    source = Path(__file__).resolve().parents[1] / 'src'
    if not (source / 'ruinas_panel' / '__init__.py').is_file():
        raise RuntimeError('Abre tools/load_in_blender.py desde la carpeta completa del proyecto.')
    if str(source) not in sys.path:
        sys.path.insert(0, str(source))
    previous = bpy.app.driver_namespace.get('ruinas_cleanup')
    if previous:
        previous()
    for name in tuple(sys.modules):
        if name == 'ruinas_panel' or name.startswith('ruinas_panel.'):
            del sys.modules[name]
    importlib.invalidate_caches()
    addon = importlib.import_module('ruinas_panel')
    addon.register()
    print('RUINAS_LOADED', addon.bl_info['version'])
    return addon


if __name__ == '__main__':
    load()
