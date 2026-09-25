"""ui /settings — ver docs/ARCHITECTURE.md para contratos y dependencias."""

from .. import config
from ..ui import preview
from bpy.props import BoolProperty
from bpy.props import EnumProperty
from bpy.props import FloatProperty
from bpy.props import IntProperty
from bpy.props import StringProperty
import bpy


class RuinSettings(bpy.types.PropertyGroup):
    build_type: EnumProperty(name='Construcción',items=[('PARTITION','Tabique','8 mm de grosor'),('WALL','Pared','12 mm de grosor'),('FORTRESS','Muralla','18 mm de grosor')],default='WALL')
    height_type: EnumProperty(name='Altura',items=[('RUIN','Ruina baja','27 mm de alto'),('ONE','1 planta','52 mm de alto'),('TWO','2 plantas','102 mm de alto, nivel intermedio a 52 mm')],default='ONE')
    layout_mode: EnumProperty(name='Paredes contiguas',items=[('NONE','Ninguna','Un muro'),('ONE','1 pared','Forma de L'),('TWO','2 paredes','Forma de U'),('ROOM','Habitación','Cuatro paredes sin cubierta')],default='NONE')
    building_depth: FloatProperty(name='Fondo (mm)',default=50,min=40,max=90)
    extra_side: EnumProperty(name='Lado de la pared',items=[('LEFT','Izquierdo',''),('RIGHT','Derecho','')],default='RIGHT')
    windows_enabled: BoolProperty(name='Ventanas',default=False)
    windows_per_wall: IntProperty(name='Ventanas por pared',default=1,min=1,max=3)
    floor_beams: BoolProperty(name='Vigas de entreplanta',default=True)
    show_advanced: BoolProperty(name='Ajustes avanzados',default=False)

    door_leaf: BoolProperty(name='Hoja con picaporte',description='Añade tablones, refuerzos y anilla; cierra el paso de puerta',default=True)
    left_turn: EnumProperty(name='Extremo izquierdo',items=config.TURN_ITEMS,default='NONE')
    right_turn: EnumProperty(name='Extremo derecho',items=config.TURN_ITEMS,default='NONE')
    left_return_length: FloatProperty(name='Longitud tramo izquierdo (mm)',default=30,min=15,max=70)
    right_return_length: FloatProperty(name='Longitud tramo derecho (mm)',default=30,min=15,max=70)

    rubble_amount: FloatProperty(name='Acumulación de escombros',description='Desde pocos ladrillos hasta un cúmulo de tierra, fragmentos y grava',default=.35,min=0,max=1)
    ground_roughness: FloatProperty(name='Tierra y grava',description='Relieve de suelo y cantidad de pequeñas piedras',default=.65,min=0,max=1)
    wood_frame: BoolProperty(name='Marco de madera',default=True)
    wood_grain: FloatProperty(name='Relieve de vetas',default=.7,min=0,max=1)

    preview_quality: EnumProperty(name='Calidad de edición',items=config.QUALITY_ITEMS,default='WORK')
    export_quality: EnumProperty(name='Calidad de exportación',items=config.QUALITY_ITEMS,default='WORK')
    quick_edit: BoolProperty(name='Borrador mientras ajustas',default=True)
    lock_distribution: BoolProperty(name='Bloquear distribución',default=True,update=preview.distribution_changed)
    distribution_seed: IntProperty(default=17)
    randomness: FloatProperty(name='Intensidad de variación',default=1,min=0,max=1)
    cracks_per_stone: IntProperty(name='Máximo de grietas por piedra',default=3,min=1,max=3)
    crack_length_var: FloatProperty(name='Variabilidad de longitud',default=.7,min=0,max=1)
    crack_width_var: FloatProperty(name='Variabilidad de anchura',default=.6,min=0,max=1)
    crack_angle_var: FloatProperty(name='Variabilidad de rotación',default=.85,min=0,max=1)
    crack_path_var: FloatProperty(name='Variabilidad de recorrido',default=.7,min=0,max=1)
    door_enabled: BoolProperty(name='Tramo con puerta',default=False)
    door_position: FloatProperty(name='Posición de puerta',default=.5,min=0,max=1)
    door_width: FloatProperty(name='Anchura del hueco (mm)',default=32,min=16,max=50)
    door_height: FloatProperty(name='Altura del hueco (mm)',default=34,min=12,max=65)
    connection_enabled: BoolProperty(name='Pilares de conexión',default=False)
    connection_side: EnumProperty(name='Extremo',items=[('LEFT','Izquierdo',''),('RIGHT','Derecho',''),('BOTH','Ambos','')],default='BOTH')
    live_preview: BoolProperty(name='Vista previa automática',default=True,update=preview.settings_changed)
    status: StringProperty(default='Ajusta un deslizador para previsualizar',options={'SKIP_SAVE'})
    length: FloatProperty(name='Longitud (mm)',default=120,min=60,max=240)
    height: FloatProperty(name='Altura máxima (mm)',default=52,min=25,max=160)
    left_height: FloatProperty(name='Extremo izquierdo (mm)',default=55,min=12,max=160)
    right_height: FloatProperty(name='Extremo derecho (mm)',default=40,min=12,max=160)
    thickness: FloatProperty(name='Grosor nominal (mm)',default=12,min=8,max=22)
    stone_size: FloatProperty(name='Altura de hilada (mm)',default=6.5,min=4,max=10)
    stone_variation: FloatProperty(name='Variación de anchuras',default=.2,min=0,max=1)
    bond_subdivisions: IntProperty(name='Subdivisiones alternas',description='Piezas por módulo en las hiladas alternas; limita piezas demasiado estrechas',default=1,min=1,max=3)
    alternate_height: FloatProperty(name='Altura de hiladas alternas',description='Proporción de altura alterna; conserva la altura total y evita hiladas menores de 3 mm',default=1.0,min=.6,max=1.4)
    projection: FloatProperty(name='Saliente de piedras (mm)',default=1.2,min=0,max=3)
    pillar_count: IntProperty(name='Número de pilares',default=2,min=0,max=5)
    pillar_width: FloatProperty(name='Anchura de pilares (mm)',default=12,min=9,max=16)
    hole_count: IntProperty(name='Número de agujeros',default=2,min=0,max=6)
    hole_size: FloatProperty(name='Tamaño de agujeros (mm)',default=14,min=7,max=30)
    collapse: FloatProperty(name='Intensidad de derrumbe',default=.76,min=0,max=.95)
    break_position: FloatProperty(name='Posición del derrumbe',default=.72,min=.25,max=.85)
    wear: FloatProperty(name='Desgaste',description='Erosión física de caras y aristas: 0 intacto, 1 envejecido',default=.55,min=0,max=1)
    cracks: FloatProperty(name='Grietas y desconchados',default=.6,min=0,max=1)
    hole_damage: FloatProperty(name='Rotura en bordes',default=.7,min=0,max=1)
    seed: IntProperty(name='Semilla',default=17,min=0,max=999999)
