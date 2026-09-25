"""ui /preferences — ver docs/ARCHITECTURE.md para contratos y dependencias."""

from .. import config
from bpy.props import BoolProperty
from bpy.props import EnumProperty
from bpy.props import FloatProperty
import bpy


class RuinPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__.split('.')[0]
    pause_refine: FloatProperty(name='Pausar refinado a partir de (s)', default=config.PREVIEW_PAUSE_SECONDS['refine'], min=1, max=120,
                                description='Si el último refinado tardó más, la vista automática espera a «Actualizar»')
    pause_fast: FloatProperty(name='Pausar vista rápida a partir de (s)', default=config.PREVIEW_PAUSE_SECONDS['fast'], min=2, max=300,
                              description='Si la última vista rápida tardó más, la vista automática queda en pausa')
    scene_units: BoolProperty(name='Escena en milímetros', default=True,
                              description='Al generar, pone las unidades de la escena en mm (escala 0,001) para leer las medidas en mm')
    export_method: EnumProperty(name='Fusión del sólido', default=config.EXPORT_METHOD,
                                items=[('MANIFOLD', 'Unión exacta', 'Conserva todo el detalle (grietas, vetas, biseles); recomendado para resina'),
                                       ('VOXEL', 'Vóxel', 'Remallado por vóxeles; suaviza y pierde el detalle fino')])

    def draw(self, context):
        'IA: Dibuja solo propiedades de preferencias, con separación de etiquetas como en Blender.'
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        col = layout.column(heading='Vista automática')
        col.prop(self, 'pause_refine')
        col.prop(self, 'pause_fast')
        col = layout.column(heading='Generación')
        col.prop(self, 'scene_units')
        layout.prop(self, 'export_method', expand=True)


def get():
    'IA: Preferencias del complemento, o None si se cargó como script de desarrollo y no está activado en Preferencias.'
    addon = bpy.context.preferences.addons.get(RuinPreferences.bl_idname)
    return addon.preferences if addon else None


def value(name, fallback):
    'IA: Lee una preferencia con valor por defecto cuando no hay preferencias registradas (carga de desarrollo o pruebas).'
    prefs = get()
    return getattr(prefs, name) if prefs else fallback
