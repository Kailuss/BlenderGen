"""Torreón: aparejo puro de torre circular y cuadrada, unidad estructural básica (sin Blender).

Igual que el ladrillo es la unidad de la fábrica, el torreón es la unidad estructural mínima:
planta cerrada, hiladas con juntas contrapeadas, esquinas trabadas y una saetera por planta.
Medidas en mm de modelo. El constructor de mallas leerá estos planes; aquí no hay geometría.
"""
import math
import random

MIN_STONE_MM=3.2
JOINT_MM=.12
ARC_PER_COURSE=1.9      # longitud de piedra / altura de hilada
CORNER_BOND=1.0         # vuelo de la piedra esquinera sobre el muro vecino, en grosores
SLIT_WIDTH_MM=2.4
SLIT_HEIGHT_COURSES=3


def courses(height,course_mm,base=0.):
    'IA: Cotas de hiladas iguales que suman exactamente la altura; ninguna menor de 3 mm.'
    if height<=0 or course_mm<=0:raise ValueError('Altura o hilada inválida')
    rows=max(1,round(height/course_mm))
    while rows>1 and height/rows<3:rows-=1
    step=height/rows
    return [(base+i*step,base+(i+1)*step) for i in range(rows)]


def ring_count(radius_mid,course_h):
    'IA: Piedras por hilada en un anillo: par (contrapeo exacto) y con arco medio cercano a ARC_PER_COURSE·hilada.'
    n=max(6,round(2*math.pi*radius_mid/(ARC_PER_COURSE*course_h)))
    return n+n%2


def round_plan(radius,thickness,height,course_mm,seed=0,variation=.2,slits=0,floors=1):
    'IA: Torre circular: por hilada, piedras como intervalos angulares [a0,a1) contrapeados medio módulo, con variación sembrada y saeteras huecas.'
    if not 0<thickness<radius:raise ValueError('Grosor fuera del radio')
    rows=courses(height,course_mm);r_mid=radius-thickness/2;h=height/len(rows)
    n=ring_count(r_mid,h);pitch=2*math.pi/n;rng=random.Random(seed*7919+11)
    min_angle=MIN_STONE_MM/r_mid
    slit_rows=slit_courses(rows,floors) if slits else {}
    plan=[]
    for row,(z0,z1) in enumerate(rows):
        offset=pitch/2 if row%2 else 0.
        cuts=[offset+i*pitch+(rng.uniform(-1,1)*pitch*.18*variation if 0<i<n else 0) for i in range(n+1)]
        stones=[(cuts[i],cuts[i+1]) for i in range(n)]
        holes=[]
        for k in range(slits if row in slit_rows else 0):
            centre=slit_rows[row]+k*2*math.pi/slits;half=SLIT_WIDTH_MM/2/radius
            holes.append((centre-half,centre+half))
        stones=cut_holes(stones,holes,min_angle,2*math.pi)
        plan.append({'row':row,'z0':z0,'z1':z1,'stones':[(a%(2*math.pi),a%(2*math.pi)+(b-a)) for a,b in stones],
                     'r_in':radius-thickness,'r_out':radius,'slits':holes})
    return plan


def slit_courses(rows,floors):
    'IA: Hiladas con saetera: un tramo de SLIT_HEIGHT_COURSES hiladas centrado en cada planta, girado por planta para no apilar huecos.'
    per=max(1,len(rows)//max(1,floors));result={}
    for f in range(floors):
        mid=f*per+per//2;turn=f*math.pi/max(2,floors)
        for r in range(mid-SLIT_HEIGHT_COURSES//2,mid-SLIT_HEIGHT_COURSES//2+SLIT_HEIGHT_COURSES):
            if 1<=r<len(rows)-1:result[r]=turn
    return result


def cut_holes(stones,holes,minimum,period=None):
    'IA: Resta huecos a una hilada (period=2π en anillos angulares, None en tramos rectos); absorbe en la vecina los recortes más cortos que minimum.'
    out=[]
    for a,b in stones:
        parts=[(a,b)]
        for h0,h1 in holes:
            nxt=[]
            for x0,x1 in parts:
                for sh in ((0,period,-period) if period else (0,)):
                    c0,c1=h0+sh,h1+sh
                    if c1<=x0 or c0>=x1:continue
                    nxt+= [(x0,c0)] if c0>x0 else [];nxt+= [(c1,x1)] if c1<x1 else [];break
                else:nxt.append((x0,x1))
            parts=nxt
        out.extend(parts)
    out.sort()
    merged=[]
    for a,b in out:
        if merged and b-a<minimum and abs(merged[-1][1]-a)<1e-9:merged[-1]=(merged[-1][0],b);continue
        if merged and merged[-1][1]-merged[-1][0]<minimum and abs(merged[-1][1]-a)<1e-9:merged[-1]=(merged[-1][0],b);continue
        merged.append((a,b))
    return merged


def square_plan(side,thickness,height,course_mm,seed=0,variation=.2,slits=0,floors=1):
    'IA: Torre cuadrada de lado exterior side: cuatro muros con esquinas trabadas que alternan dueño por hilada; piedras como rectángulos XY.'
    if not 0<2*thickness<side:raise ValueError('Grosor imposible para el lado')
    rows=courses(height,course_mm);h=height/len(rows);rng=random.Random(seed*104729+5)
    half=side/2;inner=half-thickness;plan=[]
    slit_rows=slit_courses(rows,floors) if slits else {}
    for row,(z0,z1) in enumerate(rows):
        own_x=row%2==0  # hiladas pares: frente y trasera llegan a las esquinas; impares: los laterales
        stones=[]
        for wall in ('front','back','left','right'):
            along_x=wall in ('front','back')
            full=along_x==own_x
            a,b=(-half,half) if full else (-inner,inner)
            # Rejilla común a todo el muro con medio módulo de contrapeo por hilada: dos hiladas seguidas nunca
            # comparten juntas aunque una llegue a la esquina y la otra no.
            n=max(1,round(side/(ARC_PER_COURSE*h)));pitch=side/n;phase=pitch/2 if row%2 else 0.
            inner_cuts=[-half+phase+k*pitch for k in range(-1,n+2)]
            cuts=[a]+[c for c in inner_cuts if a+MIN_STONE_MM<=c<=b-MIN_STONE_MM]+[b]
            cuts=[cuts[0]]+[c+rng.uniform(-1,1)*pitch*.15*variation for c in cuts[1:-1]]+[cuts[-1]]
            pieces=[(cuts[i],cuts[i+1]) for i in range(len(cuts)-1)]
            if row in slit_rows and slits and wall==('front','right','back','left')[floors_index(row,slit_rows,rows,floors)%4]:
                pieces=cut_holes(pieces,[(-SLIT_WIDTH_MM/2,SLIT_WIDTH_MM/2)],MIN_STONE_MM)
            pieces=merge_short(pieces,MIN_STONE_MM)
            for p0,p1 in pieces:
                if along_x:
                    y0,y1=(-half,-inner) if wall=='front' else (inner,half)
                    stones.append({'wall':wall,'x':(p0,p1),'y':(y0,y1)})
                else:
                    x0,x1=(-half,-inner) if wall=='left' else (inner,half)
                    stones.append({'wall':wall,'x':(x0,x1),'y':(p0,p1)})
        plan.append({'row':row,'z0':z0,'z1':z1,'stones':stones,'corner_owner':'front_back' if own_x else 'sides'})
    return plan


def floors_index(row,slit_rows,rows,floors):
    'IA: Planta a la que pertenece una hilada con saetera; reparte las saeteras entre las cuatro caras.'
    per=max(1,len(rows)//max(1,floors))
    return min(floors-1,row//per)


def merge_short(pieces,minimum):
    'IA: Une piezas contiguas más cortas que minimum con su vecina más corta, conservando cobertura.'
    pieces=list(pieces);changed=True
    while changed and len(pieces)>1:
        changed=False
        for i,(a,b) in enumerate(pieces):
            if b-a>=minimum:continue
            j=i-1 if i==len(pieces)-1 or (i>0 and pieces[i-1][1]-pieces[i-1][0]<pieces[i+1][1]-pieces[i+1][0]) else i+1
            if abs(pieces[min(i,j)][1]-pieces[max(i,j)][0])>1e-9:continue
            lo,hi=min(i,j),max(i,j);pieces[lo:hi+1]=[(pieces[lo][0],pieces[hi][1])];changed=True;break
    return pieces


def crown_field(seed,amount,lobes=3):
    'IA: Altura relativa de ruina en [0,1] alrededor de la torre (θ en radianes): suma sembrada de pocos cosenos; amount=0 no rompe nada.'
    rng=random.Random(seed*31337+17)
    terms=[(rng.uniform(.5,1),k,rng.uniform(0,2*math.pi)) for k in range(1,lobes+1)]
    total=sum(w for w,_,_ in terms)
    def field(theta):
        'IA: Fracción de altura perdida en θ.'
        v=sum(w*(1+math.cos(k*theta+ph))/2 for w,k,ph in terms)/total
        return amount*v**1.5
    return field


def ruin_round(plan,height,seed=0,amount=.3,support=.5):
    'IA: Coronación arruinada de torre circular: quita piedras sobre el perfil de ruina y luego, de abajo arriba, toda piedra cuyo arco no apoye al menos support en piedras vivas de la hilada inferior. Devuelve plan nuevo y retiradas.'
    field=crown_field(seed,amount);kept=[];removed=0;below=None
    for course in plan:
        stones=[]
        for a,b in course['stones']:
            mid=(a+b)/2
            if course['z1']>height*(1-field(mid)):removed+=1;continue
            if below is not None and _angular_support(a,b,below)<support*(b-a):removed+=1;continue
            stones.append((a,b))
        kept.append(dict(course,stones=stones));below=stones
    return kept,removed


def _angular_support(a,b,below):
    'IA: Longitud angular de [a,b] cubierta por piedras de la hilada inferior, con vuelta completa.'
    total=0.
    for c,d in below:
        for sh in (0,2*math.pi,-2*math.pi):
            total+=max(0.,min(b,d+sh)-max(a,c+sh))
    return total


def ruin_square(plan,height,seed=0,amount=.3,support=.5):
    'IA: Coronación arruinada de torre cuadrada con el mismo perfil (θ desde el centro) y la regla de apoyo por área sobre la hilada inferior.'
    field=crown_field(seed,amount);kept=[];removed=0;below=None
    for course in plan:
        stones=[]
        for s in course['stones']:
            cx=(s['x'][0]+s['x'][1])/2;cy=(s['y'][0]+s['y'][1])/2
            if course['z1']>height*(1-field(math.atan2(cy,cx))):removed+=1;continue
            area=(s['x'][1]-s['x'][0])*(s['y'][1]-s['y'][0])
            if below is not None and sum(max(0.,min(s['x'][1],t['x'][1])-max(s['x'][0],t['x'][0]))*max(0.,min(s['y'][1],t['y'][1])-max(s['y'][0],t['y'][0])) for t in below)<support*area:
                removed+=1;continue
            stones.append(s)
        kept.append(dict(course,stones=stones));below=stones
    return kept,removed
