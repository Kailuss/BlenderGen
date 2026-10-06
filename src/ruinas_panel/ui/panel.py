"""ui /panel — ver docs/ARCHITECTURE.md para contratos y dependencias."""

from .. import meta
from .. import config
from ..structure import damage
import bpy
import json


CATEGORY = 'Ruinas'
_parsed = {}


def parsed(text, default):
    'IA: Decodifica JSON de la escena una sola vez por valor distinto; draw() solo lee, nunca recalcula.'
    if text not in _parsed:
        if len(_parsed) > 16:
            _parsed.clear()
        try:
            _parsed[text] = json.loads(text)
        except ValueError:
            _parsed[text] = default
    return _parsed[text]


def status_icon(status):
    'IA: Icono nativo coherente con el estado: pausa, error o información.'
    if status.startswith('Pausa'):
        return 'PAUSE'
    if status.startswith('Error'):
        return 'ERROR'
    return 'INFO'


class RUIN_PT_panel(bpy.types.Panel):
    bl_label = 'Ruinas · v0.32.3'
    bl_idname = 'RUIN_PT_panel'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = CATEGORY

    @classmethod
    def poll(cls, context):
        'IA: Solo con los ajustes registrados en la escena.'
        return getattr(context.scene, 'ruin_settings', None) is not None

    def draw(self, context):
        'IA: Acciones, estado y semilla arriba; no generes ni modifiques geometría desde el panel.'
        layout = self.layout
        if context.scene.get('ruinas_physics_lab'):
            layout.label(text='Ensayo: piezas sueltas del primer tabique')
            layout.label(text='Reproduce la animación (120 fotogramas)')
            layout.label(text='Sin uniones estructurales todavía')
            layout.operator('ruin.physics_return',icon='BACK')
            return
        p = context.scene.ruin_settings
        row = layout.row(align=True)
        row.scale_y = 1.3
        row.operator('ruin.generate', text='Actualizar', icon='FILE_REFRESH')
        row.operator('ruin.solid', text='Preparar sólido', icon='EXPORT')
        layout.prop(p, 'live_preview')
        box = layout.box()
        col = box.column(align=True)
        col.label(text=p.status, icon=status_icon(p.status))
        m = parsed(meta.raw(context.scene, 'ruinas_metricas') or '{}', {})
        col.label(text='%s caras%s' % (format(m.get('faces', 0), ','), ' · geometría en caché' if m.get('cached') else ''))
        col.label(text='%s objetos · %.2f s' % (m.get('objects',0),m.get('seconds',0)))
        if m.get('instances'):
            col.label(text='%s instancias · %s variantes'%(m['instances'],m['variants']))
            col.label(text='%s caras al convertir'%format(m['expanded_faces'],','))
        if m.get('detail_limited'):
            col.label(text='Detalle limitado por presupuesto',icon='INFO')
        if p.preview_quality=='DETAIL' and not p.microdetail_preview:
            col.label(text='Poros finos al preparar Detalle')
        row = layout.row(align=True)
        row.prop(p, 'seed')
        row.operator('ruin.next_seed', text='', icon='RNDCURVE')
        row.prop(p, 'lock_distribution', text='', icon='LOCKED' if p.lock_distribution else 'UNLOCKED')


def enabled(p, field):
    'IA: Controles que no aplican se atenúan en lugar de ocultarse.'
    if field=='interior_layout':return p.layout_mode=='ROOM' and p.height_type!='RUIN'
    if not p.damage_enabled and field in set(damage.DISABLED_VALUES)|{'wear_level','hole_size','hole_seed','break_position'}:return False
    if field=='wear':return p.wear_level=='CUSTOM'
    if field in ('roof_curve','roof_tiles','roof_gables','chimneys','brass_pipes','roof_damage'):return p.layout_mode=='ROOM' and p.roof_frame
    if field=='stair_side' and p.stair_type=='NONE':return False
    if field in ('stair_type','stair_side'):return p.layout_mode=='ROOM' and p.height_type=='TWO' and p.upper_floor and p.floor_beams
    if field=='roof_frame':return p.layout_mode=='ROOM'
    if field=='upper_floor':return p.layout_mode=='ROOM' and p.height_type=='TWO' and p.floor_beams
    if field=='floor_damage':return p.layout_mode=='ROOM' and (p.ground_floor or (p.upper_floor and p.floor_beams and p.height_type=='TWO'))
    if field=='ground_floor':return p.layout_mode=='ROOM'
    if field=='balconies':return p.height_type=='TWO'
    if field in ('iron_mode','iron_damage'):return p.balconies and p.height_type=='TWO'
    if field == 'building_depth':
        return p.layout_mode != 'NONE'
    if field == 'extra_side':
        return p.layout_mode == 'ONE'
    if field == 'floor_beams':
        return p.height_type == 'TWO'
    if field == 'connection_side':
        return p.connection_enabled
    return True


def section_panel(index, section):
    'IA: Crea un subpanel para una entrada de config.SECTIONS: casilla en cabecera si hay toggle, restablecer a la derecha.'

    def poll(cls,context):
        'IA: Los controles de generación pertenecen a la casa, no a la escena aislada de ensayo físico.'
        return not context.scene.get('ruinas_physics_lab',False)

    def draw_header(self, context):
        'IA: Casilla que activa el bloque, dibujada en la cabecera del subpanel.'
        self.layout.prop(context.scene.ruin_settings, section['toggle'], text='')

    def draw_header_preset(self, context):
        'IA: Botón de restablecer los valores por defecto de la sección, alineado a la derecha.'
        self.layout.operator('ruin.reset_section', text='', icon='LOOP_BACK', emboss=False).section = index

    def draw(self, context):
        'IA: Propiedades de la sección con separación de etiquetas; atenúa lo que no aplica.'
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        p = context.scene.ruin_settings
        col = layout.column()
        if 'toggle' in section:
            col.enabled = getattr(p, section['toggle'])
        for field in section['fields']:
            if field in config.FULL_WIDTH_ENUMS:
                row = col.row(align=True)
                row.use_property_split = False
                row.enabled = enabled(p, field)
                row.prop(p, field, expand=True)
                continue
            row = col.row()
            row.enabled = enabled(p, field)
            row.prop(p, field, expand=field in config.EXPANDED_ENUMS, slider=True)
        if section['id'] in ('finish', 'cracks') and p.preview_quality not in config.DAMAGE_QUALITIES:
            col.label(text='Desgaste, grietas y escombros se ven en Detalle', icon='INFO')
        if section['id'] == 'build':
            col.label(text='Grosor %.0f mm · altura %.0f mm' % (config.BUILD_TYPES[p.build_type][0], config.HEIGHT_TYPES[p.height_type]))
        if section['id']=='layout':
            col.operator('ruin.physics_lab',icon='PHYSICS')
            if p.layout_mode!='ROOM':col.label(text='Habitaciones: requiere cuatro paredes',icon='INFO')
            elif p.height_type=='RUIN':col.label(text='Habitaciones: requiere al menos una planta',icon='INFO')
            plan=parsed(meta.raw(context.scene,'plano_interior') or '{}',{})
            if plan.get('error'):col.label(text=plan['error'],icon='INFO')
        if section['id']=='floors':
            col.label(text='Requiere Habitación; entreplanta sobre vigas')
        if section['id']=='stairs':
            col.label(text='Habitación · 2 plantas · entreplanta y vigas')
            stair=parsed(meta.raw(context.scene,'escalera_generada') or '{}',{})
            if stair.get('error'):col.label(text=stair['error'],icon='INFO')
            elif stair:
                col.label(text='%s peldaños · huella útil 20 × 20 mm'%stair['steps'])
                col.label(text='Acceso libre: 35 mm')
        if section['id']=='collapse':
            col.operator('ruin.next_holes',icon='FILE_REFRESH')
            holes=parsed(meta.raw(context.scene,'huecos_generados') or '[]',[])
            col.label(text='Huecos generados: %s · respetan anclajes'%len(holes))
        if section['id'] == 'windows' and p.windows_enabled:
            windows = parsed(meta.raw(context.scene, 'ventanas_generadas') or '[]', [])
            col.label(text='Generadas: %s · limitadas por apoyos y espacio' % len(windows))

    attrs = {
        'bl_label': section['title'],
        'bl_idname': 'RUIN_PT_' + section['id'],
        'bl_space_type': 'VIEW_3D',
        'bl_region_type': 'UI',
        'bl_category': CATEGORY,
        'bl_parent_id': RUIN_PT_panel.bl_idname,
        'bl_options': {'DEFAULT_CLOSED'} if section['closed'] else set(),
        'draw': draw,
        'poll': classmethod(poll),
        'draw_header_preset': draw_header_preset,
    }
    if 'toggle' in section:
        attrs['draw_header'] = draw_header
    return type('RUIN_PT_' + section['id'], (bpy.types.Panel,), attrs)


SUBPANELS = tuple(section_panel(index, section) for index, section in enumerate(config.SECTIONS))


def menu_add(self, context):
    'IA: Entrada «Ruina» en Añadir > Malla; genera con los ajustes actuales de la escena.'
    self.layout.operator('ruin.generate', text='Ruina', icon='MOD_BUILD')
