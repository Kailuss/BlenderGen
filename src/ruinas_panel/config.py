"""config — ver docs/ARCHITECTURE.md para contratos y dependencias."""




COLLECTION = 'MURO · fuente procedural'


SOLID_NAME = 'MURO · sólido exportable'


# Aplicar modificadores en una escena de taller que solo contiene la pieza: el coste de cada
# operador deja de crecer con el número de objetos de la escena principal.
ISOLATE_MODIFIERS = True
STAGE_SCENE = 'RUINAS · taller'


CACHE_PREFIX = '__RUIN_CACHE__'


# Fusión del sólido exportable. MANIFOLD une las piezas con un booleano exacto y conserva todo el
# detalle (grietas, vetas, biseles); VOXEL remalla a QUALITY[calidad][1] mm y lo suaviza.
EXPORT_METHOD = 'MANIFOLD'
# Con MANIFOLD: cáscaras sueltas por debajo de este volumen (mm³) son residuos y se eliminan;
# por encima, la exportación se rechaza. Los huecos cerrados interiores se eliminan siempre.
EXPORT_DEBRIS_MM3 = 2.0


QUALITY = {'DRAFT':(1,.45,1),'WORK':(2,.32,2),'DETAIL':(3,.18,2)}


QUALITY_ITEMS=[('DRAFT','Borrador','Estructura rápida, sin grietas finas'),('WORK','Trabajo','Detalle ligero'),('DETAIL','Detalle','Más geometría para revisar y exportar')]


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


# Solver de los booleanos de grieta. MANIFOLD (Blender 4.5+) exige piezas cerradas, como las nuestras.
CRACK_SOLVER='MANIFOLD'


# Tensión 0–1 por cercanía (mm) a huecos y extremos del tramo. Probabilidades por pieza:
# grieta = cracks·(base + gain·tensión), máx. 0,95; partida = cracks·(split + split_gain·tensión).
# Los sillares de pilar cargan peso: su tensión mínima es pillar.
CRACK_STRESS={'reach':16.0,'base':.6,'gain':1.2,'split':.12,'split_gain':.6,'pillar':.4}


FIELDS=('build_type','height_type','layout_mode','building_depth','extra_side','windows_enabled','windows_per_wall','floor_beams')+('door_leaf','left_turn','right_turn','left_return_length','right_return_length')+('rubble_amount','ground_roughness','wood_frame','wood_grain')+('length','height','left_height','right_height','thickness','stone_size','stone_variation','bond_subdivisions','alternate_height','projection','pillar_count','pillar_width','hole_count','hole_size','collapse','break_position','wear','cracks','hole_damage','seed')+('preview_quality', 'export_quality', 'quick_edit', 'randomness', 'crack_length_var', 'crack_width_var', 'crack_angle_var', 'crack_path_var', 'cracks_per_stone', 'door_enabled', 'door_position', 'door_width', 'door_height', 'connection_enabled', 'connection_side')


TURN_ITEMS=[('NONE','Recto','Sin tramo perpendicular'),('LEFT','Giro izq.','Giro de 90 grados a la izquierda mirando hacia ese extremo'),('RIGHT','Giro der.','Giro de 90 grados a la derecha mirando hacia ese extremo')]


SECTIONS=(
 ('Construcción',('build_type','height_type','length')),
 ('Distribución',('layout_mode','building_depth','extra_side')),
 ('Aberturas',('door_enabled','door_leaf','windows_enabled','windows_per_wall')),
 ('Plantas',('floor_beams',)),
 ('Acabado',('collapse','wear','cracks','rubble_amount','ground_roughness')),
 ('Calidad',('preview_quality','export_quality','quick_edit')),
 ('Aparejo avanzado',('stone_variation','bond_subdivisions','alternate_height','randomness')),
 ('Grietas avanzadas',('cracks_per_stone','crack_length_var','crack_width_var','crack_angle_var','crack_path_var')),
 ('Derrumbe avanzado',('break_position','hole_count','hole_size','hole_damage')),
 ('Pilares avanzados',('pillar_count','connection_enabled','connection_side')),
 ('Puerta avanzada',('door_position','door_width','door_height','wood_frame','wood_grain')))
