"""runtime — ver docs/ARCHITECTURE.md para contratos y dependencias."""




preview = False


# Nombre de la escena pendiente; nunca guardes aquí referencias a datos Blender (undo las invalida).
pending = None


deadline = 0


busy = False


phase = 'FAST'


quality = 'WORK'


settings = None


cache = {}


timings = {}
