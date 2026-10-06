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


# Segundos de la última generación de vista previa por calidad; decide la pausa automática.
durations = {}


# Piezas creadas en la última generación por calidad; escala el progreso del cursor.
pieces = {}


# Progreso en curso: función sin argumentos que avisa de una pieza creada, o None.
progress = None

# Fase ligera: conserva cajas y aplaza su acabado a variantes compartidas.
instance_build = False
detail_limited = False
physics_simulations = set()
