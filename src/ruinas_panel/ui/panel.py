"""ui /panel — ver docs/ARCHITECTURE.md para contratos y dependencias."""

from .. import config
import bpy
import json


class RUIN_PT_panel(bpy.types.Panel):
    bl_label='Muro de fantasía · v0.21'
    bl_idname='RUIN_PT_panel'
    bl_space_type='VIEW_3D'
    bl_region_type='UI'
    bl_category='Ruinas'
    def draw(self,context):
        'IA: Dibuja controles y métricas; no generes ni modifiques geometría desde el panel.'
        layout=self.layout
        p=context.scene.ruin_settings
        layout.prop(p,'live_preview')
        layout.label(text=p.status)
        m=json.loads(context.scene.get('ruinas_metricas','{}'))
        layout.label(text='%s caras · %.2f s'%(format(m.get('faces',0),','),m.get('seconds',0)))
        if m.get('cached'):
            layout.label(text='Geometría previa reutilizada',icon='CHECKMARK')
        layout.prop(p,'lock_distribution')
        if p.lock_distribution:
            layout.label(text='Distribución fijada: %s'%p.distribution_seed)
        row=layout.row(align=True)
        row.prop(p,'seed')
        row.operator('ruin.next_seed',text='',icon='FILE_REFRESH')
        layout.prop(p,'show_advanced')
        for index,(title,fields) in enumerate(config.SECTIONS):
            if index>=6 and not p.show_advanced:
                continue
            box=layout.box()
            row=box.row()
            row.label(text=title)
            row.operator('ruin.reset_section',text='',icon='LOOP_BACK').section=index
            for field in fields:
                row=box.row()
                if field=='building_depth':
                    row.enabled=p.layout_mode!='NONE'
                if field=='extra_side':
                    if p.layout_mode!='ONE':
                        continue
                if field=='windows_per_wall':
                    row.enabled=p.windows_enabled
                if field=='door_leaf' or title=='Puerta avanzada':
                    row.enabled=p.door_enabled
                if field=='floor_beams':
                    row.enabled=p.height_type=='TWO'
                row.prop(p,field,slider=True)
            if title=='Construcción':
                box.label(text='Grosor %.0f mm · altura %.0f mm'%(config.BUILD_TYPES[p.build_type][0],config.HEIGHT_TYPES[p.height_type]))
            if title=='Aberturas' and p.windows_enabled:
                actual=json.loads(context.scene.get('ventanas_generadas','[]'))
                box.label(text='Ventanas generadas: %s'%len(actual))
                box.label(text='Limitadas por apoyos y espacio disponible')
        layout.operator('ruin.generate',text='Actualizar calidad elegida')
        layout.operator('ruin.solid',text='Preparar sólido para exportar',icon='MESH_DATA')
        layout.label(text='Borrador omite las grietas finas')
