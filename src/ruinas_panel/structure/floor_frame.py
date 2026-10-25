"""Plan puro B1: primer camino de carga localizado, todavía sin consumidores de malla."""
import math
from ..construction_core import adapter,graph,schema,units
from .. import config_masonry as masonry


def aligned_axes(front,rear,tolerance_mm=masonry.AXIS_MATCH_TOLERANCE):
    'IA: Empareja juntas frontal/trasera una a una dentro de tolerancia explícita; devuelve ejes ordenados y todos los descartes con causa.'
    if not math.isfinite(tolerance_mm) or tolerance_mm<0:raise ValueError('Tolerancia inválida')
    candidates=sorted((abs(a-b),a,b) for a,_ in front for b,_ in rear if abs(a-b)<=tolerance_mm)
    used_front=set();used_rear=set();pairs=[]
    for delta,a,b in candidates:
        if a in used_front or b in used_rear:continue
        used_front.add(a);used_rear.add(b);pairs.append({'x_mm':(a+b)/2,'front_mm':a,'back_mm':b,'mismatch_mm':delta})
    pairs.sort(key=lambda p:p['x_mm'])
    rejected=[{'wall':wall,'x_mm':x,'reason':'NO_AVAILABLE_MATCH'} for wall,joints,used in
              (('front',front,used_front),('back',rear,used_rear)) for x,_ in joints if x not in used]
    return {'axes':[dict(p,ordinal=i,state='CANDIDATO') for i,p in enumerate(pairs)],'discarded_axes':rejected,
            'match_tolerance_mm':tolerance_mm,'warnings':[dict(p,code='NEAR_MATCH_LIMIT') for p in pairs if p['mismatch_mm']>masonry.AXIS_WARNING_FRACTION*tolerance_mm],
            'errors':[] if pairs else [{'code':'NO_COMMON_BEAM_AXIS'}]}


def filter_axes(axes,blocked_intervals,minimum_spacing_mm):
    'IA: Filtra candidatos sin renumerar: vanos/reservas con causa y espaciado posterior; conserva IDs de todos los segmentos existentes.'
    if minimum_spacing_mm<0 or not math.isfinite(minimum_spacing_mm):raise ValueError('Separación inválida')
    result=[];selected=[]
    for axis in sorted(axes,key=lambda a:a['ordinal']):
        reason=next((reason for lo,hi,reason in blocked_intervals if lo<=axis['x_mm']<=hi),None)
        if reason is None and any(abs(axis['x_mm']-x)<minimum_spacing_mm for x in selected):reason='BLOQUEADO_POR_ESPACIADO'
        if reason is None:selected.append(axis['x_mm'])
        result.append(dict(axis,state=reason or 'SELECCIONADO'))
    return result


def beam_skeleton(axis,bands,wall_y,seat_width_mm,seat_depth_mm,margin_world_mm,min_seat_world_mm,model_scale):
    'IA: Una viga y dos columnas de segmentos hasta cimentación/terreno; bandas modelo ascendentes, contactos en mundo y sin inventar capacidades ni masa geométrica.'
    values=[seat_width_mm,seat_depth_mm,model_scale,min_seat_world_mm]
    if any(not math.isfinite(v) or v<=0 for v in values) or not math.isfinite(margin_world_mm) or margin_world_mm<0:
        raise ValueError('Dimensiones de asiento inválidas')
    if not bands or any(len(b)!=2 or b[1]<=b[0] for b in bands) or any(a[1]!=b[0] for a,b in zip(bands,bands[1:])):
        raise ValueError('Bandas de segmento discontinuas o vacías')
    seat=units.to_world(seat_depth_mm,1,model_scale)
    if seat<min_seat_world_mm:raise ValueError('Asiento inferior al mínimo de mundo')
    area=units.to_world(seat_width_mm*seat_depth_mm,2,model_scale)
    half=seat_width_mm/2+margin_world_mm/model_scale;x=axis['x_mm'];ordinal=axis['ordinal']
    elements=[schema.element('ground','GROUND','GROUND'),schema.element('foundation','FOUNDATION','STONE_BLOCK')]
    relations=[]
    def contact(source,target,px,py,pz,share):
        'IA: Convierte en una sola frontera el contacto nominal de mm de modelo a magnitudes de mundo.'
        relations.append(adapter.relation(source,target,'SUPPORTED_BY',[{'point_mm':[math.copysign(units.to_world(abs(v),1,model_scale),v) for v in (px,py,pz)],'area_mm2':area,'seat_mm':seat,'load_share':share}]))
    # La cimentación representa dos zonas de contacto para esta única columna doble.
    for wall in ('front','back'):contact('foundation','ground',x,wall_y[wall],bands[0][0],.5)
    elements[1]['minimum_supports']=1
    ends=[]
    for wall in ('front','back'):
        parent='wall.'+wall;elements.append(schema.element(parent,'WALL','MASONRY_LIME'))
        below='foundation'
        for level,(z0,z1) in enumerate(bands):
            key=f'seg.{wall}.{level}.{ordinal}'
            segment=schema.element(key,'WALL_SEGMENT','MASONRY_LIME',wall=wall,interval_model_mm=[x-half,x+half],band_model_mm=[z0,z1])
            segment['minimum_supports']=1;elements.append(segment)
            relations.append(adapter.relation(key,parent,'HOSTED_BY'))
            contact(key,below,x,wall_y[wall],z0,1);below=key
        ends.append(below)
    key=f'beam.{len(bands)}.{ordinal}';beam=schema.element(key,'BEAM','TIMBER_SOFT')
    beam['support_groups']=[{'id':wall,'members':[end],'minimum':1} for wall,end in zip(('front','back'),ends)]
    elements.append(beam)
    for wall,end in zip(('front','back'),ends):contact(key,end,x,wall_y[wall],bands[-1][1],.5)
    model={'schema':schema.VERSION,'units':dict(schema.UNITS),'elements':elements,'relations':adapter.merge_relations(relations),
           'scope':'single beam skeleton; unknown volumes and capacities; no mesh integration',
           'segment_count':2*len(bands),'beam_id':key}
    schema.synchronise_supports(model)
    issues=graph.validate(model)+schema.validate(model)
    if issues:raise ValueError(issues)
    return model
