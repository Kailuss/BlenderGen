"""Planos interiores puros, anteriores a los vanos y a la geometría."""
from .. import config


def plan(p,bounds,door=None,stair=None):
    'IA: Solo subdivide recintos mayores de 80×80 mm si caben cuartos útiles de 60×60, tabiques y circulación de 35 mm; no fuerza distribuciones.'
    mode=getattr(p,'interior_layout','OPEN')
    if mode=='OPEN' or p.layout_mode!='ROOM':return {}
    x0,x1,y0,y1=bounds;w=x1-x0;d=y1-y0;half=config.INTERIOR_THICKNESS/2
    size=config.INTERIOR_ROOM_MIN;passage=config.INTERIOR_PASSAGE
    failure={'error':'No se subdivide: requiere recinto mayor de 80 × 80 mm, cuartos útiles de 60 × 60 mm y pasos de 35 mm.'}
    if w<=80 or d<=80 or p.height<45:return failure
    stair=stair if stair and 'error' not in stair else None
    rear_limit=stair['y0']-2 if stair else y1
    midpoint=(x0+x1)/2
    if mode=='TWO' and rear_limit-y0>=2*size+2*half:
        split=(y0+rear_limit)/2
        rooms=[{'id':'front','bounds':[x0,x1,y0,split-half],'kind':'room'}, {'id':'rear','bounds':[x0,x1,split+half,rear_limit],'kind':'room'}]
        parts=[{'axis':'x','fixed':split,'start':x0,'end':x1,'doors':[(x0+x1)/2]}]
        links=[['front','rear']];entry='front';stair_room='rear'
    else:
        if w<2*size+2*half:return failure
        if door and door['left']-half-1<midpoint<door['right']+half+1:
            choices=[door['left']-half-1,door['right']+half+1]
            valid=[x for x in choices if min(x-x0,x1-x)-half>=size]
            if not valid:return failure
            midpoint=min(valid,key=lambda x:abs(x-midpoint))
        split=rear_limit-passage-half if mode=='THREE' or stair else y1+half
        if split-half-y0<size:return failure
        rooms=[{'id':'left','bounds':[x0,midpoint-half,y0,split-half],'kind':'room'}, {'id':'right','bounds':[midpoint+half,x1,y0,split-half],'kind':'room'}]
        if mode=='THREE' or stair:
            if mode=='TWO':return failure
            rooms.append({'id':'rear','bounds':[x0,x1,split+half,rear_limit],'kind':'corridor'})
            parts=[{'axis':'x','fixed':split,'start':x0,'end':x1,'doors':[(x0+midpoint-half)/2,(midpoint+half+x1)/2]}, {'axis':'y','fixed':midpoint,'start':y0,'end':split,'doors':[]}]
            links=[['left','rear'],['right','rear']];stair_room='rear'
        else:
            parts=[{'axis':'y','fixed':midpoint,'start':y0,'end':y1,'doors':[(y0+y1)/2]}]
            links=[['left','right']];stair_room=None
        entry='left' if not door or (door['left']+door['right'])/2<midpoint else 'right'
    return {'rooms':rooms,'partitions':parts,'connections':links,'entry_room':entry,'door_width':passage,'floor':0,'stair_room':stair_room if stair else None,'minimum_room_mm':size}


def window_blocked(plan,wall,a,b):
    'IA: Reserva encuentros de tabiques, incluidos los dos extremos de una partición longitudinal.'
    for part in plan.get('partitions',[]):
        if (part['axis']=='x' and wall in ('left','right')) or (part['axis']=='y' and wall in ('front','back')):
            if a-3<part['fixed']<b+3:return True
    return False
