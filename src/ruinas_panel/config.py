"""config — ver docs/ARCHITECTURE.md para contratos y dependencias."""




COLLECTION = 'MURO · fuente procedural'
BUILD_ID = '0.32.30'
FACADE_ACCESSORY_CLEARANCE_MM = 18.0
FACADE_CANOPY_HALF_OVERHANG_MM = 4.3
ROOF_DAMAGE_SAMPLE_MM = 1.0


SOLID_NAME = 'MURO · sólido exportable'


# Aplicar modificadores en una escena de taller que solo contiene la pieza: el coste de cada
# operador deja de crecer con el número de objetos de la escena principal.
# Pausa de la vista automática según lo que tardó la última generación de cada calidad:
# el refinado espera a «Actualizar» por encima de 'refine' s; la vista rápida, por encima de 'fast' s.
PREVIEW_PAUSE_SECONDS = {'refine': 4.0, 'fast': 10.0}


ISOLATE_MODIFIERS = True
STAGE_SCENE = 'RUINAS · taller'


CACHE_PREFIX = '__RUIN_CACHE__'


# Fusión del sólido exportable. MANIFOLD une las piezas con un booleano exacto y conserva todo el
# detalle (grietas, vetas, biseles); VOXEL remalla a QUALITY[calidad][1] mm y lo suaviza.
EXPORT_METHOD = 'MANIFOLD'
# Con MANIFOLD: cáscaras sueltas por debajo de este volumen (mm³) son residuos y se eliminan;
# por encima, la exportación se rechaza. Los huecos cerrados interiores se eliminan siempre.
EXPORT_DEBRIS_MM3 = 2.0
INTERIOR_THICKNESS = 3.0
INTERIOR_ROOM_MIN = 60.0
INTERIOR_PASSAGE = 35.0
PARTITION_SECTION_WIDTH = 6.0
# Las tablas recorren toda la altura: no se fracturan en hiladas de bloques.
PARTITION_SECTION_HEIGHT = 60.0
PARTITION_JOINT_OVERLAP = .02
# Blender limita masas a 1 g; factor común para conservar mejor sus proporciones
# a escala de maqueta. Los umbrales de unión usan las mismas masas normalizadas.
PHYSICS_MASS_SCALE = 10000.0
PHYSICS_DENSITIES = {'wood':600,'stone':2200,'tile':1800,'metal':7800,'ground':1800}


QUALITY = {'DRAFT':(1,.45,1),'WORK':(2,.32,2),'DETAIL':(2,.18,2)}


# Detalle fino para resina por calidad: las caras visibles (frente, dorso y techo) se subdividen
# hasta 'edge' mm. Poros: valles de ruido blanco gaussiano difundido pit_iterations veces (bajo
# -pit_threshold desviaciones), hasta 'pits' mm de hondo; grano: ruido casi sin filtrar, hasta
# 'grain' mm. Semilla por pieza; todo hacia dentro: no cambia hiladas ni juntas.
FINE_DETAIL={'DETAIL':{'edge':.22,'pits':.12,'pit_iterations':3,'pit_threshold':.9,'grain':.04,'grain_iterations':1}}


# Desgaste principal: ruido blanco gaussiano por vértice difundido entre vecinos; más pasadas,
# rasgos más grandes (abolladuras amplias, manchas, grano). scale ajusta la amplitud al perfil anterior.
WEAR_NOISE={'broad':12,'patch':20,'grain':2,'scale':.3}


# Calidades que generan desgaste, grietas y escombros. Borrador y Trabajo muestran solo la
# estructura para editar rápido; todo el daño aparece en Detalle.
DAMAGE_QUALITIES=('DETAIL',)


# Tres niveles de desgaste (valor interno de wear, 0-1).
WEAR_LEVELS={'LIGHT':.3,'MEDIUM':.55,'HEAVY':.85}


QUALITY_ITEMS=[('DRAFT','Borrador','Estructura rápida con biseles mínimos'),('WORK','Trabajo','Estructura con biseles y aberturas; sin desgaste, grietas ni escombros'),('DETAIL','Detalle','Todo: desgaste, grietas, escombros y relieve fino para resina; más lento')]


BUILD_TYPES={'PARTITION':(6.0,4.5,.6,8.0),'WALL':(9.0,6.25,1.0,10.0),'FORTRESS':(15.0,8.0,1.3,13.0)}


FLOOR_PITCH=55.0
PHYSICS_ROOF_MIN_STRENGTH=.65
PHYSICS_TIMBER_FRACTURE_GAP_MM=3.0
PHYSICS_FRAGILE_LIMIT=256
PHYSICS_FRAGILE_STRENGTH={'plaster':.15,'chimney':.6}
UPPER_FLOOR=2.0+FLOOR_PITCH
BEAM_LEVEL=UPPER_FLOOR-3.6
HEIGHT_TYPES={'RUIN':27.0,'ONE':UPPER_FLOOR,'TWO':2.0+2*FLOOR_PITCH,'THREE':2.0+3*FLOOR_PITCH}


CACHE_METADATA=('aparejo_escalonado','mortero_retranqueado','pilares_generados','huecos_generados','huecos_solicitados','puerta_generada','escombros_generados','hiladas_generadas','giros_generados','paredes_generadas','ventanas_generadas','vigas_generadas')


CRACK_FIELDS=('cracks_per_stone','cracks','crack_length_var','crack_width_var','crack_angle_var','crack_path_var')

CACHE_METADATA=CACHE_METADATA+('derrumbe_global','suelos_generados','cubierta_generada')


# Una rama de grieta retira menos del 5 % de la piedra; perder más indica un booleano fallido.
CRACK_MAX_VOLUME_LOSS=.25


# Mínimos de impresión en resina (Anycubic Photon P1 Max, píxel XY de 24,8 µm; escala 28–35 mm).
# Las grietas más estrechas se cierran al curar o bajo la imprimación. Hasta el tramo final (tail),
# cada grieta conserva min_surface_width (mm) de ancho en una superficie hundida erosion mm por el
# desgaste, y min_depth mm de profundidad; en el tramo final se afina hasta la punta.
# Valores provisionales hasta calibrarlos con una impresión de prueba.
CRACK_PRINT={'min_surface_width':.15,'min_depth':.5,'erosion':.25,'tail':.15}


# Solver de los booleanos de pieza (grietas, ventanas y alojamientos de viga). MANIFOLD (Blender 4.5+)
# exige piezas cerradas, como las nuestras; EXACT fallaba en silencio con piedras desgastadas o densas.
BOOLEAN_SOLVER='MANIFOLD'


# Tensión 0–1 por cercanía (mm) a huecos y extremos del tramo. Probabilidades por pieza:
# grieta = cracks·(base + gain·tensión), máx. 0,95; partida = cracks·(split + split_gain·tensión).
# Los sillares de pilar cargan peso: su tensión mínima es pillar.
CRACK_STRESS={'reach':16.0,'base':.6,'gain':1.2,'split':.12,'split_gain':.6,'pillar':.4}


FIELDS=('build_type','height_type','layout_mode','building_depth','extra_side','windows_enabled','windows_per_wall','floor_beams')+('door_leaf','left_turn','right_turn','left_return_length','right_return_length')+('rubble_amount','ground_roughness','wood_frame','wood_grain')+('length','height','left_height','right_height','thickness','stone_size','stone_variation','bond_subdivisions','alternate_height','projection','pillar_count','pillar_width','hole_count','hole_size','collapse','break_position','wear','cracks','hole_damage','seed','wear_level')+('preview_quality', 'export_quality', 'quick_edit', 'randomness', 'crack_length_var', 'crack_width_var', 'crack_angle_var', 'crack_path_var', 'cracks_per_stone', 'door_enabled', 'door_position', 'door_width', 'door_height', 'connection_enabled', 'connection_side')


FIELDS=FIELDS+('batch_preview','microdetail_preview','use_instances','export_density','window_width','window_height','balconies','iron_mode','iron_damage')
FIELDS=FIELDS+('balcony_width','balcony_height','balcony_depth','balconies_per_wall','balcony_gate','balcony_open_angle','balcony_canopy')
FIELDS=FIELDS+('window_leaves','window_open_angle','window_canopies','door_canopy','window_projection','window_bay_join','window_bay_gap','facade_damage')
CACHE_METADATA=CACHE_METADATA+('fachadas_detalles',)
CACHE_METADATA=CACHE_METADATA+('vanos_limitaciones','escaleras_generadas')
FIELDS=FIELDS+('window_facing','ground_floor','upper_floor','floor_damage')
FIELDS=FIELDS+('wood_damage','roof_frame')
FIELDS=FIELDS+('roof_curve','roof_tiles','stair_type','stair_side','stair_tread','stair_riser')
FIELDS=FIELDS+('roof_sweep','roof_sweep_bias','roof_asymmetry')
FIELDS=FIELDS+('roof_gables','roof_type')
FIELDS=FIELDS+('hole_seed','roof_damage','roof_damage_seed','chimneys','brass_pipes','damage_enabled','interior_layout')
FIELDS=FIELDS+('ground_storey_height','upper_storey_height','low_wall_height','door_style','pillar_distribution','pillar_positions')
FIELDS=FIELDS+('foundation_enabled','foundation_height','entrance_tread','patio_enabled','patio_margin','patio_fence','fence_height')
CACHE_METADATA=CACHE_METADATA+('cimiento_generado',)
CACHE_METADATA=CACHE_METADATA+('relaciones_estructura','architectural_graph')
CACHE_METADATA=CACHE_METADATA+('escalera_generada','cubierta_detalles','plano_interior')

# Límites previos a operaciones costosas, no garantía de RAM en cualquier equipo.
DETAIL_VERTEX_LIMIT=2400
EXPORT_FACE_LIMIT=4000000

TURN_ITEMS=[('NONE','Recto','Sin tramo perpendicular'),('LEFT','Giro izq.','Giro de 90 grados a la izquierda mirando hacia ese extremo'),('RIGHT','Giro der.','Giro de 90 grados a la derecha mirando hacia ese extremo')]


# Subpaneles de la barra lateral, en orden. toggle: casilla en la cabecera que activa el bloque;
# closed: empieza plegado. El botón de restablecer vuelve a los valores por defecto de fields (no del toggle).
# Escalas de juego: denominador λ (1:λ) que convierte el modelo en mundo para física y
# definición del edificio. Valores habituales del mercado de miniaturas, confianza C.
GAME_SCALES={'H28':(56,'28 mm heroica','Mordheim y escaramuzas de 28 mm · 1:56'),
             'S32':(50,'32 mm','Miniaturas de 32 mm · 1:50'),
             'S20':(72,'20 mm','Escala 1:72'),
             'S15':(100,'15 mm','Escala 1:100')}

# Orden del panel = orden de construcción: volumen, fábrica, interior, huecos, cubierta,
# entorno, daño, calidad y física. Cada campo visible aparece en una sola sección
# (tests/test_api_layout.py lo comprueba).
SECTIONS=(
 {'id':'volume','title':'Volumen','fields':('game_scale','build_type','height_type','ground_storey_height','upper_storey_height','low_wall_height','length','layout_mode','building_depth','extra_side'),'closed':False},
 {'id':'masonry','title':'Muros y aparejo','fields':('stone_variation','bond_subdivisions','alternate_height','randomness'),'closed':True},
 {'id':'pillars','title':'Pilares','fields':('pillar_count','pillar_distribution','pillar_positions','connection_enabled','connection_side'),'closed':True},
 {'id':'interior','title':'Interior','fields':('interior_layout','floor_beams','ground_floor','upper_floor'),'closed':False},
 {'id':'stairs','title':'Escaleras','fields':('stair_type','stair_side','stair_tread','stair_riser'),'closed':True},
 {'id':'door','title':'Puerta','toggle':'door_enabled','fields':('door_style','door_leaf','door_position','door_width','door_height','wood_frame','door_canopy'),'closed':True},
 {'id':'windows','title':'Ventanas','toggle':'windows_enabled','fields':('window_facing','windows_per_wall','window_width','window_height','window_leaves','window_open_angle','window_canopies','window_projection','window_bay_join','window_bay_gap'),'closed':True},
 {'id':'balconies','title':'Balcones','toggle':'balconies','fields':('balconies_per_wall','balcony_width','balcony_height','balcony_depth','balcony_gate','balcony_open_angle','balcony_canopy'),'closed':True},
 {'id':'roof','title':'Cubierta','toggle':'roof_frame','fields':('roof_type','roof_curve','roof_sweep','roof_sweep_bias','roof_asymmetry','roof_tiles','roof_gables','chimneys','brass_pipes'),'closed':True},
 {'id':'foundation','title':'Cimientos y patio','fields':('foundation_enabled','foundation_height','entrance_tread','patio_enabled','patio_margin','patio_fence','fence_height'),'closed':True},
 {'id':'damage','title':'Daño','toggle':'damage_enabled','fields':('collapse','break_position','hole_count','hole_size','hole_seed','hole_damage','wear_level','wear','cracks','rubble_amount','ground_roughness','wood_damage','floor_damage','roof_damage','roof_damage_seed','facade_damage','iron_mode','iron_damage'),'closed':False},
 {'id':'cracks','title':'Grietas','fields':('cracks_per_stone','crack_length_var','crack_width_var','crack_angle_var','crack_path_var'),'closed':True},
 {'id':'quality','title':'Calidad y exportación','fields':('preview_quality','export_quality','export_density','use_instances','quick_edit','batch_preview','microdetail_preview','wood_grain'),'closed':True},
 {'id':'physics','title':'Física','fields':('physics_frames','physics_memory_mb','physics_timeout_seconds','physics_strength','physics_fragile_size','physics_brick_limit','physics_masonry_shape'),'closed':True})


# Ajustes guardados que el panel no muestra a propósito, con su motivo. Un campo nuevo
# debe estar en una sección, dibujarse en panel.py o declararse aquí.
HIDDEN_FIELDS={
 'status':'Mensaje de estado; se escribe desde el código',
 'distribution_seed':'Semilla interna del aparejo bloqueado',
 'height':'Muro suelto heredado: lo calcula el perfil de construcción',
 'left_height':'Muro suelto heredado', 'right_height':'Muro suelto heredado',
 'left_turn':'Muro suelto heredado', 'right_turn':'Muro suelto heredado',
 'left_return_length':'Muro suelto heredado', 'right_return_length':'Muro suelto heredado',
 'thickness':'Lo fija build_type (config.BUILD_TYPES)',
 'stone_size':'Altura de hilada del perfil de construcción',
 'projection':'Saliente de piedra del perfil de construcción',
 'pillar_width':'Anchura de pilar del perfil de construcción'}

# Enums de 2-3 opciones que definen un modo: botones en fila. FULL_WIDTH: sin etiqueta y a todo lo
# ancho, porque cada botón se explica solo y con etiqueta no caben en la barra lateral.
EXPANDED_ENUMS=('extra_side','window_facing')
FULL_WIDTH_ENUMS=('build_type','height_type')

CACHE_METADATA=CACHE_METADATA+('cubierta_roturas','chimeneas_generadas','bajantes_generadas','escombros_cubierta')

# Solo residuos posteriores a recortes físicos: no filtra piezas originales.
PHYSICS_RESIDUE_MAX_VOLUME=1.0
PHYSICS_RESIDUE_MAX_THICKNESS=.01

PHYSICS_JOB_MEMORY_MB=4096
PHYSICS_JOB_SECONDS=1200
PHYSICS_SOLVER_SCALE=100.0
# Límites de la precisión «Por régimen»: subpasos mínimos y máximos del cálculo aislado.
REGIME_SUBSTEPS=(40,400)
# Los umbrales de rotura se calibran como impulso de un fotograma con 40 subpasos (BALANCED).
# Bullet compara el umbral con el impulso de cada subpaso: con más subpasos, el mismo umbral
# equivale a una unión más fuerte (×10 a 400). El trabajador lo escala por 40/subpasos.
THRESHOLD_REFERENCE_SUBSTEPS=40
# Reposo de Bullet en el laboratorio (unidades reales, antes de PHYSICS_SOLVER_SCALE). Una escena
# puede sustituirlos con 'lab_sleep_linear_m_s' y 'lab_sleep_angular_rad_s' para ensayos.
PHYSICS_SLEEP_LINEAR_M_S=.002
PHYSICS_SLEEP_ANGULAR_RAD_S=.1
PHYSICS_MIN_CUT_FRAGMENT_MM=.2
# Un fragmento recortado más fino que un píxel de la impresora (24,8 µm) no es imprimible ni estable en Bullet:
# una tabla de 0,27 × 0,03 × 0,003 mm atravesaba el suelo de seguridad (4-11-2026).
PHYSICS_MIN_CUT_THICKNESS_MM=.025
# Piezas que empiezan solapadas más de esto (hierros del balcón, hasta 0,48 mm) no colisionan entre sí: Bullet
# las separaba con energía que crece con los subpasos ("hierros bailarines"). Con 0,02 mm, en la zona del 32.28:
# η 0,20 → 0,015 y ninguna pieza por encima de 1,5 veces la bola (Equilibrada, 4-11-2026).
PHYSICS_OVERLAP_DISABLE_MM=.02
# Solapes mayores son de diseño (piezas embebidas, hasta 12 mm en la casa 32.28) o con el terreno: conservan la colisión.
PHYSICS_OVERLAP_MAX_MM=1.0

CACHE_METADATA=CACHE_METADATA+('construction_reservations','removal_ledger')
