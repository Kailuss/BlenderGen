"""Reservas espaciales compartidas por ventanas y accesorios."""


def blocks_stair(w,a,b,z,stair,p):
    'IA: Rechaza vanos bajos cuyo espacio interior inmediato cruza la escalera o el desembarco; no modifica la escalera.'
    if not stair or 'error' in stair:return False
    top=stair['top']+(p.upper_storey_height if p.height_type=='THREE' else 0)
    if z>=top+2:return False
    from .openings import wall_point
    outward=1 if w['id'] in ('left','back') else -1
    pts=[wall_point(w,x,-outward*y,z) for x in (a-1,b+1) for y in (0,p.thickness/2+27)]
    lo=[min(q[i] for q in pts) for i in (0,1)];hi=[max(q[i] for q in pts) for i in (0,1)]
    sx0=min(stair['x0'],stair['landing'][0]);sx1=max(stair['x1'],stair['landing'][1])
    return lo[0]<sx1 and hi[0]>sx0 and lo[1]<stair['y1'] and hi[1]>stair['y0']
