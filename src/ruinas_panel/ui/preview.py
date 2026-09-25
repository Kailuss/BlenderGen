"""ui /preview — ver docs/ARCHITECTURE.md para contratos y dependencias."""

from .. import meta
from .. import config
from .. import runtime
from ..ui import preferences
from ..services import export
from ..services import generation
import bpy
import json
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
    first='DRAFT' if self.quick_edit else self.preview_quality
    if slow(first,'fast'):
        self.status = paused_status(first)
        return
    schedule_refresh(self.id_data)


def slow(quality,stage):
    'IA: True si la última vista previa en esa calidad superó el umbral de pausa de stage (fast o refine): preferencias o config.'
    limit=preferences.value('pause_'+stage,config.PREVIEW_PAUSE_SECONDS[stage])
    return runtime.durations.get(quality,0)>limit


def paused_status(quality):
    'IA: Texto de estado de la pausa automática, con la duración que la provocó.'
    return 'Pausa: %s tarda %.0f s · pulsa Actualizar'%(quality.lower(),runtime.durations.get(quality,0))


class ProgressCursor:
    'IA: Progreso en el cursor mientras se genera; avanza por piezas creadas frente a la generación anterior de esa calidad.'
    def __init__(self,context,quality):
        'IA: Guarda la ventana y la estimación de piezas; no dibuja nada hasta entrar.'
        self.wm=context.window_manager
        self.quality=quality
        self.expected=max(50,runtime.pieces.get(quality,300))
        self.count=0
    def tick(self):
        'IA: Cuenta una pieza y actualiza el cursor cada 10; nunca supera el 99 %.'
        self.count+=1
        if self.count%10==0:
            self.wm.progress_update(min(99,int(100*self.count/self.expected)))
    def __enter__(self):
        'IA: Activa el aviso de piezas en runtime y el progreso del cursor.'
        self.wm.progress_begin(0,100)
        runtime.progress=self.tick
        return self
    def __exit__(self,*exc):
        'IA: Retira el aviso y cierra el progreso aunque la generación falle; guarda el recuento si hubo piezas nuevas.'
        runtime.progress=None
        self.wm.progress_end()
        if self.count:
            runtime.pieces[self.quality]=self.count
        return False


def schedule_refresh(scene):
    'IA: Programa una vista previa diferida de la escena, guardada por nombre; no genera geometría aquí.'
    runtime.pending = scene.name
    runtime.deadline = time.monotonic()+.25
    if not bpy.app.timers.is_registered(refresh_timer):
        bpy.app.timers.register(refresh_timer, first_interval=.25)


def stale_preview(scene):
    'IA: True si la fuente generada no corresponde a los ajustes actuales, p. ej. tras Ctrl+Z; compara con parametros_muro.'
    p=getattr(scene,'ruin_settings',None)
    stored=meta.raw(scene,'parametros_muro')
    if p is None or not stored or not bpy.data.collections.get(config.COLLECTION):
        return False
    ignored={'export_quality','quick_edit'}
    current=json.loads(json.dumps({k:getattr(p,k) for k in config.FIELDS if k not in ignored},ensure_ascii=False))
    saved={k:v for k,v in json.loads(stored).items() if k not in ignored}
    return saved!=current


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
            if slow(p.preview_quality,'refine'):
                # Borrador sigue siendo automático; el refinado lento espera a «Actualizar».
                runtime.pending=None
                p.status=paused_status(p.preview_quality)
                return None
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
        target=quality or context.scene.ruin_settings.preview_quality
        with ProgressCursor(context,target):
            generation.generate(context,context.scene.ruin_settings,quality,preferences.value('scene_units',True))
        elapsed=time.perf_counter()-start
        runtime.durations[runtime.quality]=elapsed
        context.scene.ruin_settings.status='Vista '+(runtime.quality.lower())+' · %.2f s'%elapsed
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
        with ProgressCursor(context,context.scene.ruin_settings.export_quality):
            generation.generate(context,context.scene.ruin_settings,None,preferences.value('scene_units',True))
        result=export.make_solid(context,method=preferences.value('export_method',config.EXPORT_METHOD))
        result.hide_set(False)
        result.hide_render=False
        context.scene.ruin_settings.status='Sólido detallado actualizado'
        return result
    finally:
        runtime.busy=False
