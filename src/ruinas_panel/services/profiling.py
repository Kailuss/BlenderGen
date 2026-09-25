"""services /profiling — ver docs/ARCHITECTURE.md para contratos y dependencias."""

from .. import runtime
from functools import wraps
import time


def timed(name):
    'IA: Acumula tiempo por etapa en runtime.timings; no reinicies métricas dentro del decorador.'
    def decorate(fn):
        'IA: Conserva el nombre y metadatos de la función medida mediante wraps.'
        @wraps(fn)
        def run(*args,**kwargs):
            'IA: Usa finally para medir también errores; propaga la excepción original.'
            start=time.perf_counter()
            try:
                return fn(*args,**kwargs)
            finally:
                runtime.timings[name]=runtime.timings.get(name,0)+time.perf_counter()-start
        return run
    return decorate
