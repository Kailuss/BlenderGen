"""ui /preview — ver docs/ARCHITECTURE.md para contratos y dependencias."""

from .. import config
from .. import runtime
from ..services import export
from ..services import generation
import bpy
import time


def distribution_changed(self,context):
    'IA: Sincroniza semilla bloqueada y programa una sola actualización diferida.'
    if self.lock_distribution:
        self.distribution_seed=self.seed
    settings_changed(self,context)


def cancel_pending():
    'IA: Cancela el temporizador de esta versión antes de descargar o recargar módulos.'
    runtime.pending = None
    if bpy.app.timers.is_registered(refresh_timer):
        bpy.app.timers.unregister(refresh_timer)


def settings_changed(self, context):
    'IA: Callback RNA: agrupa cambios; respeta runtime.busy y no construyas geometría aquí.'
    if runtime.busy:
        return
    runtime.phase='FAST'
    self.status = 'Cambios pendientes'
    if not self.live_preview:
        return
    runtime.pending = self.id_data.name
    runtime.deadline = time.monotonic()+.25
    if not bpy.app.timers.is_registered(refresh_timer):
        bpy.app.timers.register(refresh_timer, first_interval=.25)


def refresh_timer():
    'IA: Gestiona Borrador/refinado en el hilo de Blender; conserva los retornos del temporizador.'
    if runtime.pending is None:
        return None
    if time.monotonic()<runtime.deadline:
        return max(.02,runtime.deadline-time.monotonic())
    scene=bpy.data.scenes.get(runtime.pending)
    if scene is None:
        runtime.pending=None
        return None
    if scene!=bpy.context.scene or bpy.context.mode!='OBJECT':
        return .2
    p=scene.ruin_settings
    if not p.live_preview:
        runtime.pending=None
        return None
    try:
        if runtime.phase=='FAST' and p.quick_edit and p.preview_quality!='DRAFT':
            update_preview(bpy.context,'DRAFT')
            runtime.phase='REFINE'
            runtime.deadline=time.monotonic()+.65
            return .65
        runtime.pending=None
        update_preview(bpy.context)
    except Exception as exc:
        runtime.pending=None
        p.status='Error: '+str(exc)[:100]
    return None


def update_preview(context, quality=None):
    'IA: Regenera la fuente y oculta el sólido anterior; restaura busy y preview aun si falla.'
    start=time.perf_counter()
    runtime.busy=True
    runtime.preview=True
    try:
        old=bpy.data.objects.get(config.SOLID_NAME)
        if old:
            old.hide_set(True)
            old.hide_render=True
        bpy.ops.object.select_all(action='DESELECT')
        generation.generate(context,context.scene.ruin_settings,quality)
        context.scene.ruin_settings.status='Vista '+(runtime.quality.lower())+' · %.2f s'%(time.perf_counter()-start)
        for screen in bpy.data.screens:
            for area in screen.areas:
                if area.type=='VIEW_3D':
                    area.tag_redraw()
    finally:
        runtime.preview=False
        runtime.busy=False


def prepare_detail(context):
    'IA: Genera calidad de exportación y fusiona; conserva la fuente editable.'
    cancel_pending()
    runtime.preview=False
    runtime.busy=True
    try:
        bpy.ops.object.select_all(action='DESELECT')
        generation.generate(context,context.scene.ruin_settings)
        result=export.make_solid(context)
        result.hide_set(False)
        result.hide_render=False
        context.scene.ruin_settings.status='Sólido detallado actualizado'
        return result
    finally:
        runtime.busy=False
