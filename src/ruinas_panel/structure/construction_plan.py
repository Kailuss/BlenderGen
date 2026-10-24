"""Reservas previas compartidas por los consumidores geométricos."""
from .. import meta


def prepare(p,walls,scene):
    'IA: Calcula una reserva local por tramo antes de vanos, forjados y cubierta; conserva cotas históricas sin crear mallas.'
    from . import stairs
    lookup={w['id']:w for w in walls};result={'schema':1,'stairs':{},'bounds':None}
    if p.layout_mode=='ROOM' and all(k in lookup for k in ('left','right','back')):
        bounds=(lookup['left']['origin'][0]+p.thickness/2-.6,lookup['right']['origin'][0]-p.thickness/2+.6,p.thickness/2-.6,lookup['back']['origin'][1]-p.thickness/2+.6)
        result['bounds']=list(bounds);result['stairs']['1']=stairs.plan(p,bounds)
        if p.height_type=='THREE':result['stairs']['2']=stairs.upper_plan(p,bounds)[1]
        if p.roof_type=='TOWER':result['stairs']['terrace']=stairs.terrace_plan(p,bounds)[1]
    meta.put(scene,'construction_reservations',result)
    return result


def stair(scene,level):
    'IA: Lee la reserva autoritativa; distingue ausencia de plan de una escalera desactivada.'
    plan=meta.get(scene,'construction_reservations')
    if plan is None:raise ValueError('Falta plan previo de reservas constructivas')
    return plan['stairs'].get(str(level))
