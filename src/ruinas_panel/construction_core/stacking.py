"""C5-4: apoyo pieza sobre pieza de la fábrica, puro y sin Blender.

Es la regla que `destruction.prune_support` aplicaba en línea, extraída para que el
plan prediga qué piedras y juntas caen tras una retirada sin consultar la malla final.
Los umbrales son los heredados; no son una ley resistente ni se recalibran aquí.
"""
GROUND_Z_MM=3.0
CONTACT_BELOW_MM=1.8
CONTACT_ABOVE_MM=1.2
MIN_SUPPORT_FRACTION=.12
MORTAR_MARGIN_MM=1.0


def overlap_area(lo,hi,a,b):
    'IA: Área XY común de dos cajas; cero si no se solapan.'
    return max(0,min(hi[0],b[0])-max(lo[0],a[0]))*max(0,min(hi[1],b[1])-max(lo[1],a[1]))


def touches_from_below(lo,b):
    'IA: La cara superior b[2] de otra pieza queda en la ventana de contacto bajo la base lo[2].'
    return lo[2]-CONTACT_BELOW_MM<=b[2]<=lo[2]+CONTACT_ABOVE_MM


def prune(stones,mortar):
    'IA: stones/mortar son (clave,lo,hi,anclada); devuelve (conservadas,descartadas) con el mismo orden y regla que prune_support.'
    kept=[];discard=[]
    for key,lo,hi,anchored in sorted(stones,key=lambda item:item[1][2]):
        area=(hi[0]-lo[0])*(hi[1]-lo[1])
        support=0
        if lo[2]>GROUND_Z_MM:
            for other,a,b,_ in kept:
                if not touches_from_below(lo,b):continue
                support+=overlap_area(lo,hi,a,b)
        if lo[2]<=GROUND_Z_MM or support>=area*MIN_SUPPORT_FRACTION or anchored:
            kept.append((key,lo,hi,anchored))
        else:discard.append(key)
    m=MORTAR_MARGIN_MM
    for key,lo,hi,_ in mortar:
        mid=tuple((a+b)/2 for a,b in zip(lo,hi))
        if not any(a[2]-m<=mid[2]<=b[2] and a[0]-m<=mid[0]<=b[0]+m and a[1]-m<=mid[1]<=b[1]+m for other,a,b,_ in kept):
            discard.append(key)
    return [k for k,*_ in kept],discard


def predict(stones,mortar,removed):
    'IA: Predicción desde el aparejo: quita las claves retiradas y aplica la misma regla; devuelve solo las caídas inducidas.'
    removed=set(removed)
    _,discard=prune([s for s in stones if s[0] not in removed],[q for q in mortar if q[0] not in removed])
    return discard


def support_relations(stones):
    'IA: Relaciones SUPPORTED_BY pieza sobre pieza con fracción de área; informativas, la decisión sigue siendo prune.'
    relations=[]
    for key,lo,hi,anchored in stones:
        if lo[2]<=GROUND_Z_MM or anchored:continue
        area=(hi[0]-lo[0])*(hi[1]-lo[1])
        for other,a,b,_ in stones:
            if other==key or not touches_from_below(lo,b):continue
            shared=overlap_area(lo,hi,a,b)
            if shared>0:relations.append({'source':key,'target':other,'kind':'SUPPORTED_BY','area_fraction':shared/area if area>0 else 0})
    return relations
