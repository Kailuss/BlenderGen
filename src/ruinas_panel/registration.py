"""registration — ver docs/ARCHITECTURE.md para contratos y dependencias."""

from . import config
from .services import cache
from .ui import operators
from .ui import panel
from .ui import preview
from .ui import settings
from bpy.props import PointerProperty
import bpy


for _field in config.FIELDS:
    if _field not in ('export_quality','quick_edit'):
        settings.RuinSettings.__annotations__[_field].keywords['update']=preview.settings_changed


CLASSES=(settings.RuinSettings,operators.RUIN_OT_generate,operators.RUIN_OT_solid,operators.RUIN_OT_seed,operators.RUIN_OT_reset,panel.RUIN_PT_panel)


def register():
    'IA: Registra RNA y limpia la versión previa; conserva identificadores para archivos blend existentes.'
    previous=bpy.app.driver_namespace.get('ruinas_cleanup')
    if previous:
        previous()
    else:
        # Permite activar este panel tras ejecutar las versiones 0.1–0.3.
        if hasattr(bpy.types.Scene,'ruin_settings'):
            del bpy.types.Scene.ruin_settings
        for cls in reversed(CLASSES):
            existing=getattr(bpy.types,cls.__name__,None)
            if existing:
                bpy.utils.unregister_class(existing)
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Scene.ruin_settings=PointerProperty(type=settings.RuinSettings)
    bpy.app.driver_namespace['ruinas_cleanup']=unregister


def unregister():
    'IA: Cancela timers y limpia caché antes de retirar clases; permite registro repetido.'
    preview.cancel_pending()
    cache.clear_cache()
    if hasattr(bpy.types.Scene,'ruin_settings'):
        del bpy.types.Scene.ruin_settings
    for cls in reversed(CLASSES):
        if cls.is_registered:
            bpy.utils.unregister_class(cls)
    bpy.app.driver_namespace.pop('ruinas_cleanup',None)
