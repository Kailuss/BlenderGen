"""config — ver docs/ARCHITECTURE.md para contratos y dependencias."""




COLLECTION = 'MURO · fuente procedural'


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


BUILD_TYPES={'PARTITION':(8.0,4.5,.6,10.0),'WALL':(12.0,6.25,1.0,12.0),'FORTRESS':(18.0,8.0,1.3,15.0)}


HEIGHT_TYPES={'RUIN':27.0,'ONE':52.0,'TWO':102.0}


CACHE_METADATA=('aparejo_escalonado','mortero_retranqueado','pilares_generados','huecos_generados','huecos_solicitados','puerta_generada','escombros_generados','hiladas_generadas','giros_generados','paredes_generadas','ventanas_generadas','vigas_generadas')


CRACK_FIELDS=('cracks_per_stone','cracks','crack_length_var','crack_width_var','crack_angle_var','crack_path_var')


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


TURN_ITEMS=[('NONE','Recto','Sin tramo perpendicular'),('LEFT','Giro izq.','Giro de 90 grados a la izquierda mirando hacia ese extremo'),('RIGHT','Giro der.','Giro de 90 grados a la derecha mirando hacia ese extremo')]


# Subpaneles de la barra lateral, en orden. toggle: casilla en la cabecera que activa el bloque;
# closed: empieza plegado. El botón de restablecer vuelve a los valores por defecto de fields (no del toggle).
SECTIONS=(
 {'id':'build','title':'Construcción','fields':('build_type','height_type','length','floor_beams'),'closed':False},
 {'id':'layout','title':'Distribución','fields':('layout_mode','building_depth','extra_side'),'closed':False},
 {'id':'finish','title':'Acabado','fields':('collapse','wear_level','cracks','rubble_amount','ground_roughness'),'closed':False},
 {'id':'door','title':'Puerta','toggle':'door_enabled','fields':('door_leaf','door_position','door_width','door_height','wood_frame','wood_grain'),'closed':True},
 {'id':'windows','title':'Ventanas','toggle':'windows_enabled','fields':('windows_per_wall',),'closed':True},
 {'id':'quality','title':'Calidad','fields':('preview_quality','export_quality','quick_edit'),'closed':True},
 {'id':'bond','title':'Aparejo','fields':('stone_variation','bond_subdivisions','alternate_height','randomness'),'closed':True},
 {'id':'cracks','title':'Grietas','fields':('cracks_per_stone','crack_length_var','crack_width_var','crack_angle_var','crack_path_var'),'closed':True},
 {'id':'collapse','title':'Derrumbe y agujeros','fields':('break_position','hole_count','hole_size','hole_damage'),'closed':True},
 {'id':'pillars','title':'Pilares','fields':('pillar_count','connection_enabled','connection_side'),'closed':True})


# Enums de 2-3 opciones que definen un modo: botones en fila. FULL_WIDTH: sin etiqueta y a todo lo
# ancho, porque cada botón se explica solo y con etiqueta no caben en la barra lateral.
EXPANDED_ENUMS=('extra_side','wear_level')
FULL_WIDTH_ENUMS=('build_type','height_type')
