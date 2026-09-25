"""config — ver docs/ARCHITECTURE.md para contratos y dependencias."""




COLLECTION = 'MURO · fuente procedural'


QUALITY = {'DRAFT':(1,.45,1),'WORK':(2,.32,2),'DETAIL':(3,.18,2)}


QUALITY_ITEMS=[('DRAFT','Borrador','Estructura rápida, sin grietas finas'),('WORK','Trabajo','Detalle ligero'),('DETAIL','Detalle','Más geometría para revisar y exportar')]


BUILD_TYPES={'PARTITION':(8.0,4.5,.6,10.0),'WALL':(12.0,6.25,1.0,12.0),'FORTRESS':(18.0,8.0,1.3,15.0)}


HEIGHT_TYPES={'RUIN':27.0,'ONE':52.0,'TWO':102.0}


CACHE_METADATA=('aparejo_escalonado','mortero_retranqueado','pilares_generados','huecos_generados','huecos_solicitados','puerta_generada','escombros_generados','hiladas_generadas','giros_generados','paredes_generadas','ventanas_generadas','vigas_generadas')


CRACK_FIELDS=('cracks_per_stone','cracks','crack_length_var','crack_width_var','crack_angle_var','crack_path_var')


# Una rama de grieta retira menos del 5 % de la piedra; perder más indica un booleano fallido.
CRACK_MAX_VOLUME_LOSS=.25


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
