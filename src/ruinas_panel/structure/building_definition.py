"""Representación arquitectónica versionada, independiente de mallas y de Bullet."""
from . import layout


def define(p):
    'IA: Describe plantas y dimensiones nominales antes de crear mallas, preservando las semillas y cotas históricas del generador.'
    levels=[];z=2.0
    for index,height in enumerate(layout.level_spans(p)):
        levels.append({'id':'floor.%s'%index,'index':index,'base_mm':z,'top_mm':z+height});z+=height
    elevation=getattr(p,'foundation_height',0) if getattr(p,'foundation_enabled',False) and p.layout_mode=='ROOM' else 0
    return {'schema':1,'id':'building','units':'mm','coordinate_frame':'building_local','world_origin_mm':[0,0,elevation],'nominal_width_mm':p.length,'nominal_depth_mm':p.building_depth,
            'wall_thickness_mm':p.thickness,'layout':p.layout_mode,'levels':levels,'roof_type':getattr(p,'roof_type','PITCHED'),
            'seeds':{'building':p.seed,'distribution':layout.distribution_seed(p),'roof_damage':getattr(p,'roof_damage_seed',0)},
            'migration':'adapter: existing construction rules remain authoritative'}


def graph(definition,walls,rooms,windows,roof_events,roof_present,door=None,stairs=()):
    'IA: Construye relaciones nominales de planta, fachada, vano, cubierta, daño y accesos por escaleras; comprueba entidades referidas, sin sustituir contactos físicos medidos.'
    nodes=[{'id':'building','type':'BUILDING'}];edges=[]
    for level in definition['levels']:
        nodes.append(dict(level,type='FLOOR'));edges.append(['building',level['id'],'contains'])
    for wall in walls:
        key='wall.'+wall['id'];nodes.append({'id':key,'type':'WALL','facade':wall['id']});edges.append(['building',key,'contains'])
    for room in rooms.get('rooms',[]):
        key='room.'+room['id'];nodes.append(dict(room,id=key,type='ROOM'));edges.append(['floor.0',key,'contains'])
    counters={}
    for window in windows:
        level=window.get('floor',0);family='balcony' if window.get('balcony') else 'window'
        group=(window.get('wall','front'),level,family);index=counters.get(group,0);counters[group]=index+1
        key='opening.%s.%s.%s.%s'%(*group,index);nodes.append(dict(window,id=key,type='OPENING'))
        facade=window.get('wall')
        if facade:edges.append(['wall.'+facade,key,'contains'])
        edges.append(['floor.%s'%level,key,'contains'])
    if door:
        key='opening.front.0.door';nodes.append(dict(door,id=key,type='DOOR'))
        edges.extend([['wall.front',key,'contains'],['floor.0',key,'contains']])
    if roof_present:
        nodes.append({'id':'roof','type':'ROOF'})
        for wall in walls:
            if wall['id'] in ('left','right'):edges.append(['wall.'+wall['id'],'roof','nominal_support'])
        members=(('terrace_beams','roof'),('deck','terrace_beams'),('parapet','deck'),('merlons','parapet')) if definition.get('roof_type')=='TOWER' else (('rafters','roof'),('battens','rafters'),('tiles','battens'))
        for role,parent in members:
            nodes.append({'id':role,'type':role.upper()});edges.append([parent,role,'supports'])
        for event in roof_events:
            nodes.append(dict(event,type='DAMAGE_EVENT'));edges.append([event['id'],'rafters','affects'])
    for index,stair in enumerate(stairs):
        if not stair or 'error' in stair:continue
        destination='roof' if stair.get('destination')=='terrace' else 'floor.%s'%(index+1)
        key='stair.%s'%index
        nodes.append(dict(stair,id=key,type='STAIR'))
        edges.extend([['floor.%s'%index,key,'access'],[key,destination,'access']])
    identifiers={n['id'] for n in nodes}
    if any(a not in identifiers or b not in identifiers for a,b,_ in edges):raise ValueError('Dependencia arquitectónica sin entidad.')
    return {'schema':1,'nodes':nodes,'relations':edges,'scope':'nominal architecture; Bullet contacts are separate'}
