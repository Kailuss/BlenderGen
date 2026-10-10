"""ui /operators — ver docs/ARCHITECTURE.md para contratos y dependencias."""

from .. import config
from .. import runtime
from ..ui import preview
from bpy.props import IntProperty,StringProperty
import bpy


def ready(cls,context):
    'IA: Poll común: exige ajustes registrados y Modo Objeto; explica en la interfaz por qué el botón está inactivo.'
    if context.scene.get('ruinas_physics_lab') or context.scene.get('ruinas_replay'):
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
            configure_view(context)
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


def configure_view(context):
    'IA: Ajusta recorte a las coordenadas mm del generador o metros del laboratorio; evita pérdida de precisión del búfer de profundidad.'
    if context.screen is None:return
    from mathutils import Vector
    physical=context.scene.get('ruinas_physics_lab') or context.scene.get('ruinas_replay')
    points=[o.matrix_world@Vector(v) for o in context.scene.objects if o.type=='MESH' and not o.get('collision_floor') for v in o.bound_box]
    span=max((max(v[k] for v in points)-min(v[k] for v in points) for k in range(3)),default=.2 if physical else 200)
    span=max(span,.01 if physical else 10)
    for area in context.screen.areas:
        if area.type=='VIEW_3D':
            space=area.spaces.active
            space.clip_start=span/2000
            space.clip_end=max(span*100,space.region_3d.view_distance*4)



def frame_view(context):
    'IA: Reencuadra al cambiar entre casa en mm y ensayo en metros, evitando volver con una vista mil veces menor.'
    from mathutils import Vector
    if context.screen is None:return
    points=[o.matrix_world@Vector(v) for o in context.scene.objects if o.type=='MESH' and not o.get('collision_floor') for v in o.bound_box]
    if points:
        lo=Vector([min(v[k] for v in points) for k in range(3)]);hi=Vector([max(v[k] for v in points) for k in range(3)])
        for area in context.screen.areas:
            if area.type=='VIEW_3D':
                view=area.spaces.active.region_3d;view.view_location=(lo+hi)/2;view.view_distance=max((hi-lo).length*1.6,.001)
    configure_view(context)



class RUIN_OT_physics_return(bpy.types.Operator):
    bl_idname='ruin.physics_return'
    bl_label='Volver a la casa'
    def execute(self,context):
        'IA: Regresa a la escena original del ensayo sin borrar simulación ni modificar la casa.'
        scene=bpy.data.scenes.get(context.scene.get('source_scene',''))
        if scene is None:return {'CANCELLED'}
        context.window.scene=scene
        frame_view(context)
        return {'FINISHED'}


class RUIN_OT_physics(bpy.types.Operator):
    bl_idname='ruin.physics_lab'
    bl_label='Preparar casa diseñada / zona'
    bl_description='Prepara el edificio completo sin mortero o el ensayo antiguo de tabiques; conserva la fuente'
    bl_options={'REGISTER','UNDO'}
    poll=classmethod(ready)
    def execute(self,context):
        'IA: Actualiza la casa si hace falta y prepara sus colisiones en un proceso aislado, conservando la sesión original.'
        from ..services import physics_jobs
        preview.cancel_pending()
        try:
            if context.scene.ruin_settings.physics_target=='MASONRY':context.scene.ruin_settings.physics_target='BUILDING'
            if preview.stale_preview(context.scene):preview.update_preview(context)
            physics_jobs.start(context.scene,'PREPARE')
        except Exception as exc:return fail(self,context,exc)
        self._timer=context.window_manager.event_timer_add(.5,window=context.window)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
    def modal(self,context,event):
        'IA: Comparte vigilancia, cancelación y entrega con la simulación aislada.'
        return RUIN_OT_physics_simulate.modal(self,context,event)



class RUIN_OT_physics_release(bpy.types.Operator):
    bl_idname='ruin.physics_release'
    bl_label='Retirar apoyo seleccionado (ensayo)'
    bl_description='En el edificio completo suelta las uniones sin mover la pieza; el ensayo antiguo retira una sección de base'
    bl_options={'REGISTER','UNDO'}
    def execute(self,context):
        'IA: Solicita soltar uniones en estructura completa o retirar apoyo en el ensayo antiguo; nunca altera la generación normal.'
        from ..services import physics
        try:physics.release_support(context.scene,context.selected_objects if context.scene.get('structural_physics') else context.active_object)
        except Exception as exc:return fail(self,context,exc)
        return {'FINISHED'}


class RUIN_OT_physics_simulate(bpy.types.Operator):
    bl_idname='ruin.physics_simulate'
    bl_label='Simular derrumbe'
    def execute(self,context):
        'IA: Ejecuta Bullet en un proceso separado con límite de recursos; la interfaz solo consulta progreso.'
        from ..services import physics_jobs
        try:physics_jobs.start(context.scene)
        except Exception as exc:return fail(self,context,exc)
        self._timer=context.window_manager.event_timer_add(.5,window=context.window)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
    def modal(self,context,event):
        'IA: ESC cancela el hijo; TIMER recoge resultado o error sin evaluar física en el Blender del usuario.'
        from ..services import physics_jobs
        if event.type=='ESC':
            physics_jobs.cancel();context.window_manager.event_timer_remove(self._timer)
            return {'CANCELLED'}
        if event.type!='TIMER':return {'RUNNING_MODAL'}
        try:
            status=physics_jobs.poll()
            if 'finished' in status:
                context.window.scene=status['finished'];frame_view(context)
                context.window_manager.event_timer_remove(self._timer)
                return {'FINISHED'}
            context.scene.ruin_settings.status='%s · %s / %s'%(status.get('stage',''),status.get('frame',status.get('objects','')),status.get('total',''))
            if context.area:context.area.tag_redraw()
        except Exception as exc:
            context.window_manager.event_timer_remove(self._timer)
            return fail(self,context,exc)
        return {'RUNNING_MODAL'}



class RUIN_OT_physics_accept(bpy.types.Operator):
    bl_idname='ruin.physics_accept'
    bl_label='Aceptar para exportación'
    bl_description='Conserva las poses del ensayo sobre la geometría detallada; después usa Preparar sólido en la casa'
    bl_options={'REGISTER','UNDO'}
    def execute(self,context):
        'IA: Guarda las poses revisadas, vuelve a la casa y regenera el detalle conservando las transformaciones físicas.'
        from ..services import physics
        try:
            source=physics.accept(context.scene);context.window.scene=source
            preview.update_preview(context)
            frame_view(context)
        except Exception as exc:return fail(self,context,exc)
        return {'FINISHED'}


class RUIN_OT_physics_clear(bpy.types.Operator):
    bl_idname='ruin.physics_clear'
    bl_label='Descartar resultado físico'
    bl_options={'REGISTER','UNDO'}
    poll=classmethod(ready)
    def execute(self,context):
        'IA: Borra solo las poses aceptadas y recupera el edificio procedural; conserva escenas de ensayo.'
        from .. import meta
        meta.put(context.scene,'physics_result',{})
        try:preview.update_preview(context)
        except Exception as exc:return fail(self,context,exc)
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


class RUIN_OT_masonry_remove(bpy.types.Operator):
    bl_idname='ruin.masonry_remove'
    bl_label='Abrir hueco: retirar ladrillos seleccionados'
    bl_options={'REGISTER','UNDO'}
    def execute(self,context):
        'IA: Retira la selección múltiple de ladrillos del ensayo, nunca la fuente.'
        from ..services import masonry_physics
        try:masonry_physics.remove_selected(context.scene,context.selected_objects)
        except Exception as exc:return fail(self,context,exc)
        return {'FINISHED'}


class RUIN_OT_masonry_impact(bpy.types.Operator):
    bl_idname='ruin.masonry_impact'
    bl_label='Añadir piedra de impacto'
    bl_options={'REGISTER','UNDO'}
    def execute(self,context):
        'IA: Añade un proyectil de gravedad al laboratorio acotado.'
        from ..services import impact_physics
        try:impact_physics.launch(context.scene,context.selected_objects)
        except Exception as exc:return fail(self,context,exc)
        return {'FINISHED'}


class RUIN_OT_physics_edit(bpy.types.Operator):
    bl_idname='ruin.physics_edit'
    bl_label='Abrir laboratorio editable'
    def execute(self,context):
        'IA: Abre la escena física asociada a una reproducción horneada.'
        scene=bpy.data.scenes.get(context.scene.get('lab_scene',''))
        if scene is None:return {'CANCELLED'}
        context.window.scene=scene;scene.frame_set(1);frame_view(context)
        return {'FINISHED'}


class RUIN_OT_physics_demo(bpy.types.Operator):
    bl_idname='ruin.physics_demo'
    bl_label='Crear ejemplo aislado (no usa la casa)'
    bl_options={'REGISTER','UNDO'}
    poll=classmethod(ready)
    def execute(self,context):
        'IA: El ejemplo solo se crea con esta acción explícita; nunca sustituye una casa al prepararla.'
        from ..services import masonry_physics
        try:scene=masonry_physics.prepare(context.scene)
        except Exception as exc:return fail(self,context,exc)
        context.window.scene=scene;frame_view(context)
        return {'FINISHED'}


class RUIN_OT_physics_fracture(bpy.types.Operator):
    bl_idname='ruin.physics_fracture'
    bl_label='Preparar rotura de ladrillos seleccionados'
    bl_options={'REGISTER','UNDO'}
    def execute(self,context):
        'IA: Prefractura varias piedras del laboratorio con juntas rompibles y conserva la casa original.'
        from ..services import impact_physics
        try:impact_physics.fracture(context.scene,context.selected_objects)
        except Exception as exc:return fail(self,context,exc)
        return {'FINISHED'}


class RUIN_OT_physics_limit(bpy.types.Operator):
    bl_idname='ruin.physics_limit'
    bl_label='Simular solo la selección; resto como soporte'
    bl_options={'REGISTER','UNDO'}
    def execute(self,context):
        'IA: Acota los cuerpos móviles conservando toda la casa visible y colisionable.'
        from ..services import impact_physics
        try:impact_physics.limit_to_selection(context.scene,context.selected_objects)
        except Exception as exc:return fail(self,context,exc)
        return {'FINISHED'}


class RUIN_OT_physics_export(bpy.types.Operator):
    bl_idname='ruin.physics_export'
    bl_label='Exportar fotograma físico a STL'
    filepath: StringProperty(subtype='FILE_PATH',default='ruinas_fisica.stl')
    def invoke(self,context,event):
        'IA: Permite elegir destino del STL; la fusión se ejecutará en otro Blender.'
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    def execute(self,context):
        'IA: Exporta la reproducción calculada en proceso aislado conservando escena, laboratorio y fuente.'
        from ..services import physics_jobs
        try:physics_jobs.start(context.scene,'EXPORT',self.filepath)
        except Exception as exc:return fail(self,context,exc)
        self._timer=context.window_manager.event_timer_add(.5,window=context.window)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
    modal=RUIN_OT_physics_simulate.modal
