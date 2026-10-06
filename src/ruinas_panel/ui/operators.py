"""ui /operators — ver docs/ARCHITECTURE.md para contratos y dependencias."""

from .. import config
from .. import runtime
from ..ui import preview
from bpy.props import IntProperty
import bpy


def ready(cls,context):
    'IA: Poll común: exige ajustes registrados y Modo Objeto; explica en la interfaz por qué el botón está inactivo.'
    if context.scene.get('ruinas_physics_lab'):
        cls.poll_message_set('Vuelve a la casa original para editar o exportar.')
        return False
    if getattr(context.scene,'ruin_settings',None) is None:
        cls.poll_message_set('Activa el complemento Ruinas en esta escena.')
        return False
    if context.mode!='OBJECT':
        cls.poll_message_set('Cambia a Modo Objeto para generar.')
        return False
    return True


def fail(operator,context,exc):
    'IA: Convierte una excepción en informe de Blender y estado del panel; devuelve CANCELLED sin traza al usuario.'
    message=str(exc) or type(exc).__name__
    context.scene.ruin_settings.status='Error: '+message[:100]
    operator.report({'ERROR'},message)
    return {'CANCELLED'}


class RUIN_OT_generate(bpy.types.Operator):
    bl_idname='ruin.generate'
    bl_label='Generar / actualizar muro'
    bl_description='Genera o regenera la ruina con los ajustes de la escena, en la calidad de edición'
    bl_options={'REGISTER','UNDO'}
    poll=classmethod(ready)
    def execute(self,context):
        'IA: Regenera la vista en la calidad de edición; cancela la vista diferida pendiente y avisa si falla.'
        preview.cancel_pending()
        try:
            preview.update_preview(context)
        except Exception as exc:
            return fail(self,context,exc)
        return {'FINISHED'}


class RUIN_OT_solid(bpy.types.Operator):
    bl_idname='ruin.solid'
    bl_label='Preparar sólido para exportar'
    bl_description='Genera en la calidad de exportación y une todas las piezas en un sólido cerrado listo para STL'
    bl_options={'REGISTER','UNDO'}
    poll=classmethod(ready)
    def execute(self,context):
        'IA: Genera en calidad de exportación y fusiona; si falla, informa y deja la fuente visible y editable.'
        try:
            preview.prepare_detail(context)
        except Exception as exc:
            return fail(self,context,exc)
        self.report({'INFO'},'Sólido seleccionado. Exporta STL: solo selección, escala 1, sin Scene Unit.')
        return {'FINISHED'}


class RUIN_OT_physics_return(bpy.types.Operator):
    bl_idname='ruin.physics_return'
    bl_label='Volver a la casa'
    def execute(self,context):
        'IA: Regresa a la escena original del ensayo sin borrar simulación ni modificar la casa.'
        scene=bpy.data.scenes.get(context.scene.get('source_scene',''))
        if scene is None:return {'CANCELLED'}
        context.window.scene=scene
        return {'FINISHED'}


class RUIN_OT_physics(bpy.types.Operator):
    bl_idname='ruin.physics_lab'
    bl_label='Ensayar física de tabique'
    bl_description='Abre una escena separada con cajas del primer tabique; reproduce la animación para ensayar caída libre, todavía sin uniones estructurales'
    bl_options={'REGISTER','UNDO'}
    poll=classmethod(ready)
    def execute(self,context):
        'IA: Prepara un ensayo independiente y abre su escena; conserva la casa, escala y animación originales.'
        from ..services import physics
        preview.cancel_pending()
        try:scene=physics.prepare(context.scene)
        except Exception as exc:return fail(self,context,exc)
        context.window.scene=scene
        for area in context.screen.areas:
            if area.type=='VIEW_3D':
                region=next((r for r in area.regions if r.type=='WINDOW'),None)
                if region:
                    with context.temp_override(area=area,region=region):bpy.ops.view3d.view_all(center=True)
        self.report({'INFO'},'Ensayo del primer tabique: reproduce la animación. La casa permanece en su escena original.')
        return {'FINISHED'}


class RUIN_OT_seed(bpy.types.Operator):
    bl_idname='ruin.next_seed'
    bl_label='Otra variante'
    bl_description='Avanza la semilla para obtener otra variante con los mismos ajustes'
    bl_options={'REGISTER','UNDO'}
    poll=classmethod(ready)
    def execute(self,context):
        'IA: Avanza la semilla; con vista automática el callback regenera, sin ella regenera aquí.'
        p=context.scene.ruin_settings
        p.seed=(p.seed+1)%1000000
        if not p.live_preview:
            try:
                preview.update_preview(context)
            except Exception as exc:
                return fail(self,context,exc)
        return {'FINISHED'}


class RUIN_OT_holes(bpy.types.Operator):
    bl_idname='ruin.next_holes'
    bl_label='Redistribuir agujeros'
    bl_description='Cambia solo la semilla de perforaciones; conserva el aparejo y los apoyos'
    bl_options={'REGISTER','UNDO'}
    poll=classmethod(ready)
    def execute(self,context):
        'IA: Variante independiente del bloqueo del aparejo; regenera explícitamente solo si la vista automática está apagada.'
        p=context.scene.ruin_settings;p.hole_seed=(p.hole_seed+1)%1000000
        if not p.live_preview:
            try:preview.update_preview(context)
            except Exception as exc:return fail(self,context,exc)
        return {'FINISHED'}


class RUIN_OT_reset(bpy.types.Operator):
    bl_idname='ruin.reset_section'
    bl_label='Restablecer sección'
    bl_description='Devuelve los ajustes de esta sección a sus valores por defecto'
    bl_options={'REGISTER','UNDO'}
    section: IntProperty()
    @classmethod
    def poll(cls,context):
        'IA: Solo necesita ajustes registrados; restablecer valores no crea geometría por sí mismo.'
        return getattr(context.scene,'ruin_settings',None) is not None
    def execute(self,context):
        'IA: Restablece los valores por defecto de una sección bajo busy y programa una única vista previa.'
        if not 0<=self.section<len(config.SECTIONS):
            return {'CANCELLED'}
        p=context.scene.ruin_settings
        runtime.busy=True
        try:
            for field in config.SECTIONS[self.section]['fields']:
                setattr(p,field,p.bl_rna.properties[field].default)
        finally:
            runtime.busy=False
        preview.settings_changed(p,context)
        return {'FINISHED'}
