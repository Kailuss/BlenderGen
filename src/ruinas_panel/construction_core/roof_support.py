"""0.32.31: apoyo real de cubiertas, puro y sin Blender.

Las piezas de cubierta se juzgan contra la geometría que de verdad sobrevive (cajas
de piedra y de piezas ya aceptadas), no contra el campo de derrumbe previsto. Caso de
origen: imposible.blend (semilla 17), con la terraza colgada de una viga que no tocaba
ningún muro y losas apoyadas en una franja de 2 mm de su borde.
Una caja es (lo, hi), con lo y hi como tuplas (x, y, z) en mm.
"""
BEARING_GAP_MM=.6
SEAT_GAP_MM=.6
MIN_BEARING_FRACTION=.5
MIN_BLOCK_CONTACT=.25
MIN_SLAB_CONTACT=.05
HULL_TOLERANCE_MM=.05


def overlap(a0,a1,b0,b1):
    'IA: Longitud común de dos intervalos; cero si no se tocan.'
    return max(0.0,min(a1,b1)-max(a0,b0))


def rect_overlap(foot,lo,hi):
    'IA: Rectángulo XY común entre la huella (x0,x1,y0,y1) y una caja, o None si el área es nula.'
    x0=max(foot[0],lo[0]);x1=min(foot[1],hi[0]);y0=max(foot[2],lo[1]);y1=min(foot[3],hi[1])
    if x1-x0<=0 or y1-y0<=0:return None
    return (x0,x1,y0,y1)


def bearing(foot,bottom,stones,gap=BEARING_GAP_MM,fraction=MIN_BEARING_FRACTION):
    'IA: Entrega de una cabeza de viga: piedra cuya cara superior queda como mucho `gap` mm bajo `bottom` (o la envuelve) cubre al menos `fraction` de la huella XY; devuelve (apoya, fracción cubierta).'
    area=(foot[1]-foot[0])*(foot[3]-foot[2])
    if area<=0:return False,0.0
    covered=0.0
    for lo,hi in stones:
        if hi[2]<bottom-gap or lo[2]>=bottom-gap:continue
        r=rect_overlap(foot,lo,hi)
        if r:covered+=(r[1]-r[0])*(r[3]-r[2])
    share=min(1.0,covered/area)
    return share>=fraction,share


def contacts(box,seats,gap=SEAT_GAP_MM):
    'IA: Rectángulos XY de contacto entre la base de `box` y las caras superiores de `seats` a menos de `gap` mm de altura.'
    lo,hi=box;foot=(lo[0],hi[0],lo[1],hi[1]);found=[]
    for a,b in seats:
        if abs(b[2]-lo[2])>gap:continue
        r=rect_overlap(foot,a,b)
        if r:found.append(r)
    return found


def seated(box,seats,fraction=MIN_BLOCK_CONTACT,gap=SEAT_GAP_MM):
    'IA: Apoyo sin vuelco: área de contacto ≥ `fraction` de la huella y centro XY dentro del rectángulo envolvente de los contactos; una arista o una franja de borde no bastan. Devuelve (apoya, fracción).'
    lo,hi=box;area=(hi[0]-lo[0])*(hi[1]-lo[1])
    found=contacts(box,seats,gap)
    if area<=0 or not found:return False,0.0
    share=min(1.0,sum((r[1]-r[0])*(r[3]-r[2]) for r in found)/area)
    cx=(lo[0]+hi[0])/2;cy=(lo[1]+hi[1])/2;t=HULL_TOLERANCE_MM
    inside=min(r[0] for r in found)-t<=cx<=max(r[1] for r in found)+t and min(r[2] for r in found)-t<=cy<=max(r[3] for r in found)+t
    return share>=fraction and inside,share


def landing(foot,top,surfaces):
    'IA: Reposo de una pieza que cae: (cota, índice) de la cara superior más alta entre las superficies bajo su huella XY que no superan `top` (la base de partida); (0, -1) si no hay ninguna, que es el terreno.'
    best=0.0;index=-1
    for i,(lo,hi) in enumerate(surfaces):
        if hi[2]>top or hi[2]<=best and index>=0:continue
        if rect_overlap(foot,lo,hi):best=hi[2];index=i
    return best,index
