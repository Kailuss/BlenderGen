"""services /generation — ver docs/ARCHITECTURE.md para contratos y dependencias."""

from .. import config
from .. import runtime
from ..geometry import fracture
from ..services import cache
from ..structure import layout
from ..structure import walls
import json
import time


def metrics(context,coll,timings,cached,solid=None):
    'IA: Registra conteos/tiempos del resultado real; distingue fuente de sólido fusionado.'
    objects=[solid] if solid else list(coll.objects)
    data={'quality':runtime.quality,'faces':sum(len(o.data.polygons) for o in objects),
          'vertices':sum(len(o.data.vertices) for o in objects),
          'seconds':timings.get('total',0),'stages':dict(timings),'cached':cached,'solid':solid is not None}
    context.scene['ruinas_metricas']=json.dumps(data)


def generate(context,p,quality=None):
    'IA: Entrada principal; valida, prepara o restaura caché, aplica daño y actualiza métricas.'
    runtime.quality=quality or (p.preview_quality if runtime.preview else p.export_quality)
    runtime.settings=p
    runtime.timings={}
    start=time.perf_counter()
    layout.apply_profiles(p)
    layout.plan_door(p)  # Validar espacio antes de reemplazar la geometría existente.
    signature=cache.cache_signature(context,p)
    entry=runtime.cache.get(cache.cache_key())
    cached=entry is not None and entry['signature']==signature
    if cached:
        coll=cache.restore_cache(context)
    else:
        coll=walls._build_wall(context,p)
        cache.save_cache(context,coll,signature)
    runtime.timings['preparacion']=time.perf_counter()-start
    fracture.apply_damage(coll,p)
    runtime.timings['total']=time.perf_counter()-start
    metrics(context,coll,runtime.timings,cached)
    context.scene['parametros_muro']=json.dumps({k:getattr(p,k) for k in config.FIELDS},ensure_ascii=False)
    return coll
