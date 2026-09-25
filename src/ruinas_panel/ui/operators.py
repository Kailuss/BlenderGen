"""ui /operators — ver docs/ARCHITECTURE.md para contratos y dependencias."""

from .. import config
from .. import runtime
from ..ui import preview
from bpy.props import IntProperty
import bpy


class RUIN_OT_generate(bpy.types.Operator):
    bl_idname='ruin.generate'
    bl_label='Generar / actualizar muro'
    bl_options={'REGISTER','UNDO'}
    def execute(self,context):
        'IA: Operador Blender: respeta UNDO, usa servicios y devuelve un estado válido.'
        preview.cancel_pending()
        preview.update_preview(context)
        return {'FINISHED'}


class RUIN_OT_solid(bpy.types.Operator):
    bl_idname='ruin.solid'
    bl_label='Preparar sólido para exportar'
    bl_options={'REGISTER','UNDO'}
    def execute(self,context):
        'IA: Operador Blender: respeta UNDO, usa servicios y devuelve un estado válido.'
        preview.prepare_detail(context)
        self.report({'INFO'},'Sólido seleccionado. Exporta STL: solo selección, escala 1, sin Scene Unit.')
        return {'FINISHED'}


class RUIN_OT_seed(bpy.types.Operator):
    bl_idname='ruin.next_seed'
    bl_label='Otra variante'
    bl_options={'REGISTER','UNDO'}
    def execute(self,context):
        'IA: Operador Blender: respeta UNDO, usa servicios y devuelve un estado válido.'
        p=context.scene.ruin_settings
        p.seed=(p.seed+1)%1000000
        if not p.live_preview:
            preview.update_preview(context)
        return {'FINISHED'}


class RUIN_OT_reset(bpy.types.Operator):
    bl_idname='ruin.reset_section'
    bl_label='Restablecer sección'
    bl_options={'REGISTER','UNDO'}
    section: IntProperty()
    def execute(self,context):
        'IA: Operador Blender: respeta UNDO, usa servicios y devuelve un estado válido.'
        p=context.scene.ruin_settings
        runtime.busy=True
        try:
            for field in config.SECTIONS[self.section][1]:
                setattr(p,field,p.bl_rna.properties[field].default)
        finally:
            runtime.busy=False
        preview.settings_changed(p,context)
        return {'FINISHED'}
