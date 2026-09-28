"""services /generation — ver docs/ARCHITECTURE.md para contratos y dependencias."""

from .. import meta
from .. import config
from .. import runtime
from ..geometry import fracture
from ..geometry import primitives
from ..geometry import batching
from ..geometry import instances
from ..services import cache
from ..structure import layout
from ..structure import walls
import time
import bpy


def metrics(context,coll,timings,cached,solid=None):
    'IA: Registra conteos/tiempos del resultado real; distingue fuente de sólido fusionado.'
    objects=[solid] if solid else list(coll.objects)
    data={'quality':runtime.quality,'objects':len(objects),'microdetail':not runtime.preview or runtime.settings.microdetail_preview,'faces':sum(len(o.data.polygons) for o in objects),
          'vertices':sum(len(o.data.vertices) for o in objects),
          'seconds':timings.get('total',0),'stages':dict(timings),'cached':cached,'solid':solid is not None}
    if not solid:
        data['expanded_faces']=instances.expanded_faces(coll)
        data['instances']=sum(len(o.data.vertices) for o in objects if o.get('ruin_instances'))
        data['variants']=sum(len(bpy.data.collections[o['ruin_library']].objects) for o in objects if o.get('ruin_instances'))
    data['detail_limited']=runtime.detail_limited
    meta.put(context.scene,'ruinas_metricas',data)


def generate(context,p,quality=None,units=True):
    'IA: Entrada principal; valida, prepara o restaura caché, aplica daño y actualiza métricas.'
    try:
        meta.drop_legacy(context.scene)
        if units:
            set_units(context.scene)
        return build(context,p,quality)
    finally:
        runtime.instance_build=False
        primitives.drop_stage()


def set_units(scene):
    'IA: Escena en milímetros (escala 0,001) para leer las medidas en mm; solo cambia la presentación, no la geometría.'
    scene.unit_settings.system='METRIC'
    scene.unit_settings.scale_length=.001
    scene.unit_settings.length_unit='MILLIMETERS'


def build(context,p,quality):
    'IA: Cuerpo de generate; la escena de taller que usa apply_modifier se borra en generate aunque esto falle.'
    runtime.quality=quality or (p.preview_quality if runtime.preview else p.export_quality)
    runtime.settings=p
    runtime.timings={}
    runtime.detail_limited=False
    runtime.instance_build=p.use_instances
    start=time.perf_counter()
    layout.apply_profiles(p)
    layout.plan_door(p)  # Validar espacio antes de reemplazar la geometría existente.
    signature=cache.cache_signature(context,p)
    entry=runtime.cache.get(cache.cache_key())
    cached=entry is not None and entry['signature']==signature
    if cached:
        coll=cache.restore_cache(context)
    else:
        phase=time.perf_counter()
        coll=walls._build_wall(context,p)
        runtime.timings['estructura_base']=time.perf_counter()-phase
        from ..structure import assembly
        phase=time.perf_counter();assembly.finish(coll,p,context.scene)
        runtime.timings['integracion']=time.perf_counter()-phase
        cache.save_cache(context,coll,signature)
    runtime.timings['preparacion']=time.perf_counter()-start
    runtime.instance_build=False
    if p.use_instances:
        instances.build(coll,p)
    else:
        fracture.apply_damage(coll,p)
    if runtime.preview and p.batch_preview:
        batching.pack_preview(coll)
    runtime.timings['total']=time.perf_counter()-start
    metrics(context,coll,runtime.timings,cached)
    meta.put(context.scene,'parametros_muro',{k:getattr(p,k) for k in config.FIELDS})
    return coll
