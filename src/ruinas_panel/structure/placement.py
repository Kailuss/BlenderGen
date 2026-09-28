"""Reservas espaciales compartidas por ventanas y accesorios."""


def stair_reservation(p,walls):
    'IA: Usa exactamente el plan del forjado antes de perforar ventanas; evita que el macizo aparezca en el hueco trasero.'
    if p.layout_mode!='ROOM':return None
    from . import stairs
    w={q['id']:q for q in walls}
    return stairs.plan(p,(w['left']['origin'][0]+p.thickness/2-.6,w['right']['origin'][0]-p.thickness/2+.6,p.thickness/2-.6,w['back']['origin'][1]-p.thickness/2+.6))


def blocks_stair(w,a,b,z,stair,p):
    'IA: Rechaza vanos bajos cuyo espacio interior inmediato cruza la escalera o el desembarco; no modifica la escalera.'
    if not stair or 'error' in stair or z>=stair['top']+2:return False
    from .openings import wall_point
    outward=1 if w['id'] in ('left','back') else -1
    pts=[wall_point(w,x,-outward*y,z) for x in (a-1,b+1) for y in (0,p.thickness/2+27)]
    lo=[min(q[i] for q in pts) for i in (0,1)];hi=[max(q[i] for q in pts) for i in (0,1)]
    sx0=min(stair['x0'],stair['landing'][0]);sx1=max(stair['x1'],stair['landing'][1])
    return lo[0]<sx1 and hi[0]>sx0 and lo[1]<stair['y1'] and hi[1]>stair['y0']
