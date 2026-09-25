"""registration — ver docs/ARCHITECTURE.md para contratos y dependencias."""

from . import config
from . import runtime
from .services import cache
from .ui import operators
from .ui import panel
from .ui import preview
from .ui import settings
from bpy.app.handlers import persistent
from bpy.props import PointerProperty
import bpy


for _field in config.FIELDS:
    if _field not in ('export_quality','quick_edit'):
        settings.RuinSettings.__annotations__[_field].keywords['update']=preview.settings_changed


CLASSES=(settings.RuinSettings,operators.RUIN_OT_generate,operators.RUIN_OT_solid,operators.RUIN_OT_seed,operators.RUIN_OT_reset,panel.RUIN_PT_panel)


@persistent
def before_data_reload(*args):
    'IA: Antes de undo, redo o carga de archivo suelta referencias a ID guardadas en runtime; no accede a datos Blender.'
    preview.cancel_pending()
    cache.forget_cache()
    runtime.settings=None


@persistent
def after_data_reload(*args):
    'IA: Tras undo, redo o carga elimina plantillas de caché huérfanas buscándolas por nombre en los datos nuevos.'
    cache.purge_orphan_templates()


HANDLERS=(('load_pre',before_data_reload),('undo_pre',before_data_reload),('redo_pre',before_data_reload),
          ('load_post',after_data_reload),('undo_post',after_data_reload),('redo_post',after_data_reload))


def install_handlers():
    'IA: Instala handlers una sola vez; retira antes los de cualquier copia anterior del paquete.'
    remove_handlers(everywhere=True)
    for name,function in HANDLERS:
        getattr(bpy.app.handlers,name).append(function)


def remove_handlers(everywhere=False):
    'IA: Retira los handlers de esta versión; con everywhere también los de otras cargas del mismo paquete.'
    for name,function in HANDLERS:
        handlers=getattr(bpy.app.handlers,name)
        for existing in list(handlers):
            same_package=getattr(existing,'__module__','')==__name__ and getattr(existing,'__name__','')==function.__name__
            if existing is function or (everywhere and same_package):
                handlers.remove(existing)


def register():
    'IA: Registra RNA y handlers y limpia la versión previa; conserva identificadores para archivos blend existentes.'
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
    install_handlers()
    bpy.app.driver_namespace['ruinas_cleanup']=unregister


def unregister():
    'IA: Retira handlers, cancela timers y limpia caché antes de retirar clases; permite registro repetido.'
    remove_handlers()
    preview.cancel_pending()
    cache.clear_cache()
    if hasattr(bpy.types.Scene,'ruin_settings'):
        del bpy.types.Scene.ruin_settings
    for cls in reversed(CLASSES):
        if cls.is_registered:
            bpy.utils.unregister_class(cls)
    bpy.app.driver_namespace.pop('ruinas_cleanup',None)
