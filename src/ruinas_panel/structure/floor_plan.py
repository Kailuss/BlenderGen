"""Planos interiores puros, anteriores a los vanos y a la geometría."""


def plan(p,bounds,door=None,stair=None):
    'IA: Dos estancias o dos cuartos y distribuidor trasero; pasos de 25 mm, acceso exterior y reserva completa de escalera.'
    mode=getattr(p,'interior_layout','OPEN')
    if mode=='OPEN' or p.layout_mode!='ROOM':return {}
    x0,x1,y0,y1=bounds;w=x1-x0;d=y1-y0
    if w<70 or d<64 or p.height<45:return {'error':'Las habitaciones necesitan al menos 70 × 64 mm interiores y una planta completa.'}
    split=y0+d*.5
    if stair and 'error' not in stair:split=min(split,stair['y0']-4)
    if split-y0<30:return {'error':'No queda espacio para habitaciones delante de la escalera.'}
    midpoint=(x0+x1)/2
    if mode=='THREE' and door and door['left']-3<midpoint<door['right']+3:
        choices=[door['left']-4,door['right']+4]
        valid=[x for x in choices if min(x-x0,x1-x)>=32]
        if not valid:return {'error':'Tres estancias: aumenta anchura o desplaza la puerta para conservar acceso y cuartos de 32 mm.'}
        midpoint=min(valid,key=lambda x:abs(x-midpoint))
    doors=[(x0+x1)/2] if mode=='TWO' else [(x0+midpoint)/2,(midpoint+x1)/2]
    partitions=[{'axis':'x','fixed':split,'start':x0,'end':x1,'doors':doors}]
    rooms=[{'id':'front','bounds':[x0,x1,y0,split]},{'id':'rear','bounds':[x0,x1,split,y1]}]
    links=[['front','rear']]
    entry='front'
    if mode=='THREE':
        partitions.append({'axis':'y','fixed':midpoint,'start':y0,'end':split,'doors':[]})
        rooms=[{'id':'left','bounds':[x0,midpoint,y0,split]},{'id':'right','bounds':[midpoint,x1,y0,split]},{'id':'rear','bounds':[x0,x1,split,y1]}]
        links=[['left','rear'],['right','rear']]
        entry='left' if not door or (door['left']+door['right'])/2<midpoint else 'right'
    return {'rooms':rooms,'partitions':partitions,'connections':links,'entry_room':entry,'door_width':25,'floor':0,'stair_room':'rear' if stair and 'error' not in stair else None}


def window_blocked(plan,wall,a,b):
    'IA: Reserva extremos de tabiques para que una ventana exterior no quede dividida por su encuentro.'
    for part in plan.get('partitions',[]):
        if (part['axis']=='x' and wall in ('left','right')) or (part['axis']=='y' and wall=='front'):
            if a-3<part['fixed']<b+3:return True
    return False
