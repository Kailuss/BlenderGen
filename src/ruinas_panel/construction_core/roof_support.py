"""Apoyo real de cubiertas tras el derrumbe: vigas, losas y bloques sobre lo que de verdad queda.

Sustituye la pérdida *prevista* por la geometría superviviente (caso «imposible.blend»: una viga
de terraza a 8–16 mm por encima de la piedra que quedaba sostenía losas, parapeto y almenas).
Cajas alineadas a ejes en mm; puro y sin Blender. Se itera hasta punto fijo de abajo arriba.
"""
SEAT_GAP_MM=.3
MIN_CONTACT_MM2=.5
BLOCK_MIN_AREA_FRACTION=.25


def _overlap(a0,a1,b0,b1):
    'IA: Longitud común de dos intervalos; cero si no se solapan.'
    return max(0.,min(a1,b1)-max(a0,b0))


def _rests_on(lo,b_lo,b_hi,gap,same_level=False):
    'IA: La cara superior del apoyo está a menos de gap por debajo de la base, o lo atraviesa sin quedar por encima de ella; same_level admite apoyos que arrancan a la misma cota (vigas que se cruzan, cabeza embebida en el muro).'
    return b_hi[2]>=lo[2]-gap and (b_lo[2]<lo[2]+gap if same_level else b_lo[2]<lo[2])


def _covered(intervals,a,b):
    'IA: Longitud de [a,b] cubierta por la unión de intervalos.'
    total=0.;end=a
    for x0,x1 in sorted(intervals):
        x0=max(x0,end);x1=min(x1,b)
        if x1>x0:total+=x1-x0;end=x1
    return total


def beam_seated(lo,hi,axis,masonry,seat_mm,gap=SEAT_GAP_MM):
    'IA: Una viga necesita asiento real en sus dos cabezas: en cada tramo final de seat_mm, al menos la mitad cubierta por fábrica a menos de gap bajo su base.'
    other=1-axis
    if hi[axis]-lo[axis]<2*seat_mm:return False
    for a,b in ((lo[axis],lo[axis]+seat_mm),(hi[axis]-seat_mm,hi[axis])):
        spans=[(m_lo[axis],m_hi[axis]) for m_lo,m_hi in masonry
               if _rests_on(lo,m_lo,m_hi,gap,same_level=True) and _overlap(lo[other],hi[other],m_lo[other],m_hi[other])>0]
        if _covered(spans,a,b)<.5*seat_mm:return False
    return True


def rests_balanced(lo,hi,supports,min_fraction=0.,gap=SEAT_GAP_MM):
    'IA: Apoyo por contactos: área mínima, fracción mínima de huella y centro de la pieza dentro de la caja de los contactos (no vuelca).'
    contacts=[]
    for b_lo,b_hi in supports:
        if not _rests_on(lo,b_lo,b_hi,gap):continue
        x=(max(lo[0],b_lo[0]),min(hi[0],b_hi[0]));y=(max(lo[1],b_lo[1]),min(hi[1],b_hi[1]))
        if x[1]>x[0] and y[1]>y[0]:contacts.append((x,y))
    area=sum((x[1]-x[0])*(y[1]-y[0]) for x,y in contacts)
    footprint=(hi[0]-lo[0])*(hi[1]-lo[1])
    if area<MIN_CONTACT_MM2 or area<min_fraction*footprint:return False
    cx=(lo[0]+hi[0])/2;cy=(lo[1]+hi[1])/2
    return min(x[0] for x,_ in contacts)<=cx<=max(x[1] for x,_ in contacts) and min(y[0] for _,y in contacts)<=cy<=max(y[1] for _,y in contacts)


def unsupported(pieces,masonry,seat_mm):
    'IA: pieces = {clave: (tipo, lo, hi, eje)} con tipo beam/slab/block; devuelve las claves sin apoyo real, iterando hasta punto fijo.'
    alive=dict(pieces);removed=[]
    while True:
        drop=[]
        for key,(kind,lo,hi,axis) in alive.items():
            # Un brochal (otro eje) apoya también en las vigas vivas que cruza.
            if kind=='beam':ok=beam_seated(lo,hi,axis,list(masonry)+[(l,h) for k,(t,l,h,ax) in alive.items() if t=='beam' and ax!=axis],seat_mm)
            elif kind=='slab':ok=rests_balanced(lo,hi,[(l,h) for k,(t,l,h,_) in alive.items() if t=='beam'])
            else:ok=rests_balanced(lo,hi,[(l,h) for k,(t,l,h,_) in alive.items() if t in ('slab','block') and k!=key],BLOCK_MIN_AREA_FRACTION)
            if not ok:drop.append(key)
        if not drop:return removed
        for key in drop:alive.pop(key)
        removed.extend(sorted(drop))
