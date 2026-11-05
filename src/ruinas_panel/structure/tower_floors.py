"""Torreón, paso 6: forjados interiores sobre ménsulas y escalera de caracol volada (sin Blender).

Cada forjado es una capa de vigas paralelas (eje X) apoyadas en ménsulas de piedra que forman parte del aparejo
(perpiaños que atraviesan el muro y vuelan hacia dentro) y una capa de tablas (eje Y) sobre las vigas.
La escalera es una hélice continua de peldaños de piedra pegados al muro: cada peldaño monta sobre el anterior
y da una vuelta completa por planta. Las vigas que chocarían con la escalera no se ponen y las tablas se recortan,
de modo que el hueco de la escalera sale del propio choque. Tras la ruina de coronación solo queda lo que se sostiene:
viga con sus dos ménsulas vivas, tabla con dos vigas vivas y el centro entre ellas, peldaño con el anterior vivo
y muro detrás. Medidas en mm de modelo.
"""
import math
from .. import config_masonry as masonry
from ..construction_core import seat
from . import tower_plan

BEAM_W=seat.BEAM_WIDTH_MM
BEAM_H=seat.BEAM_HEIGHT_MM
BEAM_PITCH_MM=6.5
BOARD_W=3.
BOARD_T=1.
BOARD_GAP=.15
BOARD_CANTILEVER=4.5    # vuelo máximo de tabla más allá de la última viga que la sostiene
WALL_CLEAR=.15          # holgura entre madera y paramento interior
CORBEL_REACH={'ROUND':4.,'SQUARE':3.}   # vuelo de la ménsula hacia dentro
CORBEL_MARGIN=.4        # ménsula más ancha que la cabeza de viga a cada lado
MIN_SEAT_MM=1.2         # entrega mínima de viga sobre ménsula, medida en el borde más desfavorable
BEAM_SHIFTS_MM=(0.,.75,-.75,1.5,-1.5,2.25,-2.25,3.,-3.)
MAX_CORBEL_MM=9.        # ménsula más larga (en el paramento) que esto: la viga es demasiado oblicua
PARAPET_COURSES=3       # hiladas de pretil sobre la terraza
SLAB_MM=5.              # losa cuadrada de la terraza
SLAB_T=1.2
SLAB_JOINT=.15
SLAB_BEARING=.6         # fracción mínima del área de losa sobre tablas
STEP_RISE_MM=2.8
CLASH_MARGIN=.15        # holgura entre madera y peldaño al buscar choques (cubre el muestreo)
STEP_OVERLAP=.3         # fracción del paso angular con que cada peldaño monta sobre el anterior
STEP_EMBED=.1           # el peldaño entra 0,1 mm en el paramento para fundirse al exportar
WALL_BEHIND=.3          # fracción mínima del arco del peldaño con muro detrás


def geometry(shape,size,thickness):
    'IA: Medidas de planta comunes: forma, paramento exterior e interior (radio o semilado).'
    outer=size/2
    return {'shape':shape,'outer':outer,'inner':outer-thickness,'thickness':thickness}


def boundary(geo,theta,depth=0.):
    'IA: Distancia del centro al paramento interior (menos depth) en la dirección θ: círculo o cuadrado.'
    a=geo['inner']-depth
    if geo['shape']=='ROUND':return a
    return a/max(abs(math.cos(theta)),abs(math.sin(theta)))


def stair_depth(geo):
    'IA: Anchura de la escalera desde el paramento: 40 % del radio interior entre 5 y 10 mm.'
    return min(10.,max(5.,.4*geo['inner']))


def level(plan,floor,row,terrace=False):
    'IA: Un forjado con ménsulas en la hilada row-1: cotas de viga, de tablas (board_top) y de piso acabado (top, con losas si es terraza).'
    corbel=plan[row-1];base=corbel['z1']-masonry.COURSE_TOP_INSET;boards=base+BEAM_H+BOARD_T
    return {'floor':floor,'corbel_row':row-1,'corbel_z0':corbel['z0']+masonry.COURSE_BOTTOM_INSET,'beam_z0':base,
            'beam_z1':base+BEAM_H,'board_top':boards,'top':boards+(SLAB_T if terrace else 0.),'terrace':terrace}


def levels(plan,floors,terrace=False):
    'IA: Forjados que reparten en plantas iguales las hiladas bajo el pretil (PARAPET_COURSES si terrace) y, si terrace, la terraza bajo el pretil cuando la última planta tiene al menos tres hiladas.'
    rows=len(plan);usable=rows-(PARAPET_COURSES if terrace else 0);out=[]
    for f in range(1,max(1,floors)):
        out.append(level(plan,f,min(rows-2,max(2,round(f*usable/floors)))))
    last=out[-1]['corbel_row']+1 if out else 0
    if terrace and usable-last>=3 and usable>=2:out.append(level(plan,max(1,floors),usable,True))
    return out


def stair(geo,tops,arrival,turns=None):
    'IA: Hélice continua de peldaños de suelo a último piso; el tramo f gira turns[f] radianes (por defecto una vuelta, que llega de nuevo a arrival); cada peldaño monta STEP_OVERLAP sobre el anterior.'
    steps=[];depth=stair_depth(geo);start=arrival
    for flight,(z_lo,z_hi) in enumerate(zip(tops,tops[1:])):
        turn=turns[flight] if turns else 2*math.pi
        n=max(4 if turn<2*math.pi-1e-9 else 8,round((z_hi-z_lo)/STEP_RISE_MM));rise=(z_hi-z_lo)/n;pitch=turn/n
        for i in range(n):
            a0=start+i*pitch
            steps.append({'flight':flight,'index':i,'a0':a0,'a1':a0+pitch*(1+STEP_OVERLAP),
                          'z0':z_lo+i*rise,'z1':z_lo+(i+1)*rise,'depth':depth})
        start+=turn
    return steps


def flight_turns(lv,tops,arrival):
    'IA: Giro de cada tramo: vuelta completa en los pisos; en la terraza, el giro cercano al paso angular del tramo anterior que deja centrado en ±Y el arco de hélice que pasa bajo su forjado (lejos de las cabezas de viga).'
    turns=[2*math.pi]*len(lv)
    if not lv or not lv[-1]['terrace'] or len(lv)<2:return turns
    l=lv[-1];z_lo,z_hi=tops[-2],tops[-1];below=(z_hi-l['corbel_z0'])/(z_hi-z_lo)
    previous=max(8,round((tops[-2]-tops[-3])/STEP_RISE_MM));pitch=2*math.pi/previous
    wanted=max(4,round((z_hi-z_lo)/STEP_RISE_MM))*pitch;best=None
    for target in (math.pi/2,3*math.pi/2):
        for k in range(-1,3):
            angle=(target-arrival+2*math.pi*k)/(1-below/2)
            if math.pi/2<=angle<=2*math.pi and (best is None or abs(angle-wanted)<abs(best-wanted)):best=angle
    turns[-1]=best if best is not None else 2*math.pi
    return turns


def arrival_angle(geo,lv,tops):
    'IA: Ángulo de llegada a cada piso: centra en +Y (lejos de las cabezas de viga) el tramo de hélice que pasa bajo el forjado.'
    if not lv:return math.pi/2
    pairs=[(l,t,b) for l,t,b in zip(lv,tops[1:],tops) if not l['terrace']] or list(zip(lv,tops[1:],tops))
    span=max((t-l['corbel_z0'])/(t-b) for l,t,b in pairs)
    return math.pi/2+math.pi*min(1.,span)


def in_step(geo,step,x,y,margin=0.):
    'IA: Indica si el punto XY cae en la huella del peldaño (banda junto al paramento y arco del peldaño), ampliada margin mm hacia dentro y por los lados.'
    r=math.hypot(x,y)
    if r<1e-9:return False
    theta=math.atan2(y,x);pad=margin/max(r,1e-9)
    if (theta-step['a0']+pad)%(2*math.pi)>step['a1']-step['a0']+2*pad:return False
    return boundary(geo,theta,step['depth'])-margin<=r<=boundary(geo,theta)+STEP_EMBED


def step_outline(geo,step,spacing=.3):
    'IA: Puntos XY del contorno de la huella de un peldaño (dos radios y dos arcos) cada spacing mm.'
    lo,hi=step['a0'],step['a1'];pts=[]
    for theta in (lo,hi):
        r0=boundary(geo,theta,step['depth']);r1=boundary(geo,theta)+STEP_EMBED;n=max(2,math.ceil((r1-r0)/spacing)+1)
        pts+=[((r0+(r1-r0)*i/(n-1))*math.cos(theta),(r0+(r1-r0)*i/(n-1))*math.sin(theta)) for i in range(n)]
    n=max(2,math.ceil(geo['inner']*1.5*(hi-lo)/spacing)+1)
    for i in range(n):
        theta=lo+(hi-lo)*i/(n-1)
        for r in (boundary(geo,theta,step['depth']),boundary(geo,theta)+STEP_EMBED):pts.append((r*math.cos(theta),r*math.sin(theta)))
    return pts


def box_hits_steps(geo,steps,x0,x1,y0,y1,z0,z1,spacing=.6):
    'IA: Indica si una caja choca con algún peldaño: puntos de la caja dentro de la huella o contorno del peldaño dentro de la caja, con solape abierto en Z.'
    near=[s for s in steps if s['z0']<z1-1e-9 and s['z1']>z0+1e-9]
    if not near:return False
    nx=max(2,math.ceil((x1-x0)/spacing)+1);ny=max(2,math.ceil((y1-y0)/spacing)+1)
    for i in range(nx):
        x=x0+(x1-x0)*i/(nx-1)
        for j in range(ny):
            y=y0+(y1-y0)*j/(ny-1)
            if any(in_step(geo,s,x,y,CLASH_MARGIN) for s in near):return True
    for s in near:
        if any(x0<x<x1 and y0<y<y1 for x,y in step_outline(geo,s)):return True
    return False


def beam_end(geo,y0,y1):
    'IA: Abscisa de la cabeza de viga (cara cortada a escuadra) que no toca el paramento interior en ninguno de sus bordes.'
    if geo['shape']=='SQUARE':return geo['inner']-WALL_CLEAR
    far=max(abs(y0),abs(y1));r=geo['inner']-WALL_CLEAR
    return math.sqrt(max(0.,r*r-far*far))


def beam_seat(geo,y0,y1):
    'IA: Entrega de la viga sobre la ménsula en su borde más desfavorable (mm); negativa si la cabeza no llega.'
    reach=CORBEL_REACH[geo['shape']];end=beam_end(geo,y0,y1)
    if geo['shape']=='SQUARE':return reach-WALL_CLEAR
    near=min(abs(y0),abs(y1));r=geo['inner']-reach
    if near>=r:return end
    return end-math.sqrt(r*r-near*near)


def beam_positions(geo):
    'IA: Ordenadas Y de las vigas: paso cercano a BEAM_PITCH_MM dentro de la franja donde la entrega llega a MIN_SEAT_MM.'
    half=geo['inner']-WALL_CLEAR-BEAM_W/2
    if geo['shape']=='ROUND':
        y=0.
        while y+.1<=half and beam_seat(geo,y+.1-BEAM_W/2,y+.1+BEAM_W/2)>=MIN_SEAT_MM and corbel_arc(geo,y+.1)<=MAX_CORBEL_MM:y+=.1
        half=y
    n=max(2,round(2*half/BEAM_PITCH_MM)+1)
    return [-half+2*half*i/(n-1) for i in range(n)]


def corbel_arc(geo,y):
    'IA: Longitud en el paramento interior de la ménsula de una viga circular centrada en y (mm).'
    y0,y1=y-BEAM_W/2,y+BEAM_W/2;a,b=corbel_span(geo,y0,y1,beam_end(geo,y0,y1),1)
    return (b-a)*geo['inner']


def corbel_span(geo,y0,y1,end,side):
    'IA: Ménsula bajo una cabeza de viga: intervalo angular (circular) o en Y (cuadrada, sin pasar del paramento interior) que cubre la entrega con margen.'
    if geo['shape']=='SQUARE':return (max(-geo['inner'],y0-CORBEL_MARGIN),min(geo['inner'],y1+CORBEL_MARGIN))
    r=geo['inner']-CORBEL_REACH['ROUND'];angles=[]
    for y in (y0,(y0+y1)/2,y1):
        x_in=math.sqrt(max(0.,r*r-y*y))
        for x in (min(x_in,end),end):angles.append(math.atan2(y,side*x))
    if side<0:angles=[a%(2*math.pi) for a in angles]
    margin=CORBEL_MARGIN/geo['inner']
    return (min(angles)-margin,max(angles)+margin)


def corbel_supported(geo,plan,lv,span,side):
    'IA: Indica si una ménsula apoyaría al menos la mitad en la hilada inferior del plan intacto (no sobre una saetera); misma regla que la ruina.'
    below=plan[lv['corbel_row']-1]['stones']
    if geo['shape']=='ROUND':
        a,b=span
        return tower_plan._angular_support(a,b,below)>=.5*(b-a)
    reach=CORBEL_REACH['SQUARE'];x0,x1=(geo['inner']-reach,geo['outer']) if side>0 else (-geo['outer'],-geo['inner']+reach)
    y0,y1=span;area=(x1-x0)*(y1-y0)
    cover=sum(max(0.,min(x1,t['x'][1])-max(x0,t['x'][0]))*max(0.,min(y1,t['y'][1])-max(y0,t['y'][0])) for t in below)
    return cover>=.5*area


def place_beam(geo,lv,steps,plan,k,y,limit):
    'IA: Viga k centrada en y con sus ménsulas si cabe: dentro de la franja de entrega, sin chocar con peldaños y con ménsulas apoyadas; si no, None.'
    if abs(y)>limit+1e-9:return None
    y0,y1=y-BEAM_W/2,y+BEAM_W/2;end=beam_end(geo,y0,y1)
    corbels=[corbel_span(geo,y0,y1,end,s) for s in (1,-1)]
    reach=CORBEL_REACH[geo['shape']]
    boxes=[(-end,end,y0,y1,lv['beam_z0'],lv['beam_z1'])]
    boxes+=[(s*end-(reach if s>0 else 0),s*end+(0 if s>0 else reach),y0-CORBEL_MARGIN,y1+CORBEL_MARGIN,lv['corbel_z0'],lv['beam_z0']) for s in (1,-1)]
    if any(box_hits_steps(geo,steps,*b) for b in boxes):return None
    if plan is not None and not all(corbel_supported(geo,plan,lv,c,s) and corbel_in_masonry(geo,plan,lv,c,s) for c,s in zip(corbels,(1,-1))):return None
    return {'id':k,'y':(y0,y1),'x':(-end,end),'corbels':corbels}


def corbel_in_masonry(geo,plan,lv,span,side):
    'IA: Indica si la ménsula sustituye solo piedra de su hilada (no ocupa una saetera ni un hueco del aparejo).'
    course=plan[lv['corbel_row']]['stones']
    if geo['shape']=='ROUND':
        a,b=span
        return tower_plan._angular_support(a,b,course)>=(b-a)-1e-6
    x0,x1=(geo['inner'],geo['outer']) if side>0 else (-geo['outer'],-geo['inner']);y0,y1=span
    cover=sum(max(0.,min(x1,t['x'][1])-max(x0,t['x'][0]))*max(0.,min(y1,t['y'][1])-max(y0,t['y'][0])) for t in course)
    return cover>=(x1-x0)*(y1-y0)-1e-6


def frame(geo,lv,steps,plan=None):
    'IA: Vigas, ménsulas y tablas de un forjado sin chocar con la escalera ni volar sobre saeteras; las tablas se recortan contra peldaños y paramento.'
    beams=[];positions=beam_positions(geo);limit=positions[-1]
    for k,y in enumerate(positions):
        # Si la ménsula cae sobre una saetera o la viga roza la escalera, se corre la viga como haría el carpintero.
        for shift in BEAM_SHIFTS_MM:
            beam=place_beam(geo,lv,steps,plan,k,y+shift,limit)
            if beam and (not beams or beam['y'][0]-beams[-1]['y'][1]>=.5):beams.append(beam);break
    boards=[]
    if len(beams)<2:return beams,boards
    z0,z1=lv['beam_z1'],lv['board_top']
    pitch=BOARD_W+BOARD_GAP;count=int((2*(geo['inner']-WALL_CLEAR)+BOARD_GAP)//pitch)
    start=-(count*pitch-BOARD_GAP)/2
    for i in range(count):
        x0=start+i*pitch;x1=x0+BOARD_W;far=max(abs(x0),abs(x1))
        limit=geo['inner']-WALL_CLEAR if geo['shape']=='SQUARE' else math.sqrt(max(0.,(geo['inner']-WALL_CLEAR)**2-far*far))
        carriers=[b for b in beams if b['x'][0]<=x0 and b['x'][1]>=x1]
        if len(carriers)<2:continue
        y0=max(-limit,carriers[0]['y'][0]-BOARD_CANTILEVER);y1=min(limit,carriers[-1]['y'][1]+BOARD_CANTILEVER)
        while y1-y0>BOARD_W and box_hits_steps(geo,steps,x0,x1,y1-.5,y1,z0,z1):y1-=.5
        while y1-y0>BOARD_W and box_hits_steps(geo,steps,x0,x1,y0,y0+.5,z0,z1):y0+=.5
        if box_hits_steps(geo,steps,x0,x1,y0,y1,z0,z1):continue
        board={'id':i,'x':(x0,x1),'y':(y0,y1)}
        if supports(board,beams):boards.append(board)
    return beams,boards


def inside(geo,x0,x1,y0,y1):
    'IA: Indica si un rectángulo cabe dentro del paramento interior con la holgura de la madera.'
    r=geo['inner']-WALL_CLEAR
    if geo['shape']=='SQUARE':return -r<=x0 and x1<=r and -r<=y0 and y1<=r
    return all(math.hypot(x,y)<=r for x in (x0,x1) for y in (y0,y1))


def bearing(slab,boards):
    'IA: Fracción del área de una losa que descansa sobre tablas (las tablas no se solapan entre sí).'
    (x0,x1),(y0,y1)=slab['x'],slab['y'];area=(x1-x0)*(y1-y0)
    return sum(max(0.,min(x1,t['x'][1])-max(x0,t['x'][0]))*max(0.,min(y1,t['y'][1])-max(y0,t['y'][0])) for t in boards)/area


def slabs(geo,lv,boards,steps):
    'IA: Losas de la terraza a soga (medio módulo de contrapeo por fila) dentro del paramento, sin chocar con la escalera y con SLAB_BEARING de su área sobre tablas.'
    if not lv['terrace'] or not boards:return []
    out=[];r=geo['inner'];n=int(2*r//SLAB_MM)+2;k=0
    for j in range(n):
        y0=-r+j*SLAB_MM+SLAB_JOINT/2;y1=y0+SLAB_MM-SLAB_JOINT;phase=SLAB_MM/2 if j%2 else 0.
        for i in range(n+1):
            x0=-r-phase+i*SLAB_MM+SLAB_JOINT/2;x1=x0+SLAB_MM-SLAB_JOINT
            if not inside(geo,x0,x1,y0,y1):continue
            if box_hits_steps(geo,steps,x0,x1,y0,y1,lv['board_top'],lv['top']):continue
            slab={'id':k,'x':(x0,x1),'y':(y0,y1)};k+=1
            if bearing(slab,boards)>=SLAB_BEARING:out.append(slab)
    return out


def supports(board,beams):
    'IA: Vigas bajo una tabla (cruce ≥ 60 % del ancho de viga y viga que llega a toda la tabla) si son dos o más y el centro queda entre ellas; si no, lista vacía.'
    under=[b for b in beams if min(board['y'][1],b['y'][1])-max(board['y'][0],b['y'][0])>=.6*BEAM_W
           and b['x'][0]<=board['x'][0] and b['x'][1]>=board['x'][1]]
    if len(under)<2:return []
    centre=(board['y'][0]+board['y'][1])/2
    if not min(b['y'][0] for b in under)<=centre<=max(b['y'][1] for b in under):return []
    return under


def touches(x,y,period=None):
    'IA: Indica si dos cotas coinciden, también tras dar vueltas completas de period.'
    if abs(x-y)<1e-7:return True
    if not period:return False
    d=(x-y)%period
    return d<1e-7 or period-d<1e-7


def fold_remnants(pieces,holes,minimum,period=None):
    'IA: Absorbe en la ménsula vecina los restos de piedra más cortos que minimum que quedan sueltos entre huecos; devuelve piezas y huecos ajustados.'
    holes=[list(h) for h in holes];out=[]
    for a,b in pieces:
        if b-a>=minimum:out.append((a,b));continue
        for h in holes:
            if touches(h[1],a,period):h[1]=b+(h[1]-a);break
            if touches(b,h[0],period):h[0]=a+(h[0]-b);break
        else:out.append((a,b))
    return out,[tuple(h) for h in holes]


def merge_spans(spans,owners,period=None):
    'IA: Une ménsulas que se solapan (también a través de 2π si period) en una sola piedra que sirve a todas sus vigas.'
    items=[((a%period,a%period+(b-a)) if period else (a,b),o) for (a,b),o in zip(spans,owners)]
    out=[]
    for (a,b),o in sorted(items):
        if out and a<=out[-1][0][1]+1e-9:out[-1]=((out[-1][0][0],max(b,out[-1][0][1])),out[-1][1]+[o])
        else:out.append(((a,b),[o]))
    if period and len(out)>1 and out[-1][0][1]>=out[0][0][0]+period-1e-9:
        (a,b),o=out.pop();out[0]=((a,max(b,out[0][0][1]+period)),o+out[0][1])
    return out


def add_corbels(plan,geo,lv,beams):
    'IA: Inserta las ménsulas en la hilada del forjado como piedras pasantes que vuelan hacia dentro; cada una recuerda su viga.'
    course=plan[lv['corbel_row']];reach=CORBEL_REACH[geo['shape']]
    if geo['shape']=='ROUND':
        merged=merge_spans([c for b in beams for c in b['corbels']],[b['id'] for b in beams for _ in b['corbels']],2*math.pi)
        spans=[m[0] for m in merged];owners=[m[1] for m in merged]
        minimum=tower_plan.MIN_STONE_MM/(geo['inner']+geo['thickness']/2)
        stones=tower_plan.cut_holes(course['stones'],spans,minimum,2*math.pi)
        stones,spans=fold_remnants(stones,spans,minimum,2*math.pi)
        stones=[(a%(2*math.pi),a%(2*math.pi)+(b-a)) for a,b in stones];corbels={}
        for (a,b),beam in zip(spans,owners):
            key=(a%(2*math.pi),a%(2*math.pi)+(b-a));stones.append(key);corbels[key]=beam
        course['stones']=sorted(stones);course['corbels']=corbels;course['corbel_reach']=reach
        return
    outer=geo['outer'];inner=geo['inner'];stones=[]
    for wall,sign in (('right',1),('left',-1)):
        own=sorted([s for s in course['stones'] if s['wall']==wall],key=lambda s:s['y'][0])
        merged=merge_spans([b['corbels'][0 if sign>0 else 1] for b in beams],[b['id'] for b in beams])
        holes=[m[0] for m in merged]
        pieces=tower_plan.cut_holes([s['y'] for s in own],holes,tower_plan.MIN_STONE_MM)
        pieces,holes=fold_remnants(pieces,holes,tower_plan.MIN_STONE_MM)
        x=own[0]['x'] if own else ((inner,outer) if sign>0 else (-outer,-inner))
        stones+=[{'wall':wall,'x':x,'y':p} for p in pieces]
        xs=(inner-reach,outer) if sign>0 else (-outer,-inner+reach)
        stones+=[{'wall':wall,'x':xs,'y':h,'corbels':m[1]} for h,m in zip(holes,merged)]
    course['stones']=[s for s in course['stones'] if s['wall'] not in ('left','right')]+stones


def wall_behind(geo,plan,step):
    'IA: Fracción del arco del peldaño con piedra detrás, en las hiladas que cruzan su altura.'
    rows=[c for c in plan if c['z0']<step['z1'] and c['z1']>step['z0']]
    if not rows:return 0.
    n=7;hit=0
    for i in range(n):
        theta=step['a0']+(step['a1']-step['a0'])*(i+.5)/n
        if geo['shape']=='ROUND':
            t=theta%(2*math.pi)
            ok=any(a-1e-9<=t<=b+1e-9 or a-1e-9<=t+2*math.pi<=b+1e-9 for c in rows for a,b in c['stones'])
        else:
            d=boundary(geo,theta)+geo['thickness']/2;x,y=d*math.cos(theta),d*math.sin(theta)
            ok=any(s['x'][0]<=x<=s['x'][1] and s['y'][0]<=y<=s['y'][1] for c in rows for s in c['stones'])
        hit+=ok
    return hit/n


def corbel_alive(geo,course,beam_id):
    'IA: Indica si las dos ménsulas de una viga siguen en la hilada tras la ruina.'
    if geo['shape']=='ROUND':
        alive=[k for k,v in course.get('corbels',{}).items() if beam_id in v and k in course['stones']]
    else:
        alive=[s for s in course['stones'] if beam_id in s.get('corbels',())]
    return len(alive)>=2


def settle(geo,plan,lv_frames,steps):
    'IA: Tras la ruina: vigas con sus dos ménsulas, tablas con dos vigas y el centro entre ellas, peldaños con el anterior y muro detrás. Devuelve lo que queda y recuentos de lo perdido.'
    kept=[];lost={'beams':0,'boards':0,'slabs':0,'steps':0}
    for lv,beams,boards,tiles in lv_frames:
        course=plan[lv['corbel_row']]
        live=[b for b in beams if corbel_alive(geo,course,b['id'])]
        stay=[t for t in boards if supports(t,live)]
        rest=[t for t in tiles if bearing(t,stay)>=SLAB_BEARING]
        lost['beams']+=len(beams)-len(live);lost['boards']+=len(boards)-len(stay);lost['slabs']+=len(tiles)-len(rest)
        kept.append((lv,live,stay,rest))
    alive=[];previous=True
    for s in steps:
        previous=previous and wall_behind(geo,plan,s)>=WALL_BEHIND
        if previous:alive.append(s)
        else:lost['steps']+=1
    return kept,alive,lost


def interior(geo,plan,floors,terrace=False):
    'IA: Plan interior completo sobre el aparejo intacto: forjados (y terraza con losas si terrace), ménsulas insertadas en el plan y hélice; modifica plan en su sitio. Cada forjado es (nivel, vigas, tablas, losas).'
    lv=levels(plan,floors,terrace)
    if not lv:return [],[]
    tops=[0.]+[l['top'] for l in lv];arrival=arrival_angle(geo,lv,tops)
    steps=stair(geo,tops,arrival,flight_turns(lv,tops,arrival))
    frames=[]
    for l in lv:
        beams,boards=frame(geo,l,steps,plan)
        add_corbels(plan,geo,l,beams);frames.append((l,beams,boards,slabs(geo,l,boards,steps)))
    return frames,steps


FALL_LIMIT=40           # piezas caídas como máximo; el resto se da por retirado
FALL_CELL=1.            # celda del mapa de alturas (mm)
FALL_BREAK=.3           # hueco entre los trozos de una pieza partida
PILE_MAX=10.            # altura máxima del montón de escombro sobre su piso
FALL_SUPPORT=.4         # fracción mínima de la huella de una pieza caída que descansa a su cota


def central(geo):
    'IA: Medida (radio o semilado) de la zona central libre de escalera donde cae el escombro interior.'
    return geo['inner']-stair_depth(geo)-.3


def footprint(geo,cx,cy,yaw,length,width):
    'IA: Esquinas XY de un rectángulo girado yaw alrededor de su centro.'
    c,s=math.cos(yaw),math.sin(yaw);out=[]
    for u,v in ((-1,-1),(1,-1),(1,1),(-1,1)):
        x=u*length/2;y=v*width/2;out.append((cx+x*c-y*s,cy+x*s+y*c))
    return out


def in_central(geo,corners):
    'IA: Indica si todas las esquinas caen en la zona central (círculo o cuadrado).'
    r=central(geo)
    if geo['shape']=='SQUARE':return all(abs(x)<=r and abs(y)<=r for x,y in corners)
    return all(math.hypot(x,y)<=r for x,y in corners)


def cells_under(corners):
    'IA: Celdas del mapa de alturas cuyo centro cae dentro del rectángulo girado (convexo).'
    xs=[x for x,_ in corners];ys=[y for _,y in corners];out=[]
    for i in range(math.floor(min(xs)/FALL_CELL),math.ceil(max(xs)/FALL_CELL)+1):
        for j in range(math.floor(min(ys)/FALL_CELL),math.ceil(max(ys)/FALL_CELL)+1):
            px,py=(i+.5)*FALL_CELL,(j+.5)*FALL_CELL;inside=True
            for k in range(4):
                (ax,ay),(bx,by)=corners[k],corners[(k+1)%4]
                if (bx-ax)*(py-ay)-(by-ay)*(px-ax)<0:inside=False;break
            if inside:out.append((i,j))
    return out


def lost_pieces(geo,frames,kept,steps,alive):
    'IA: Piezas que perdieron apoyo, con su caja original (centro, giro, medidas, cota de base) y material, de abajo arriba.'
    out=[]
    for (lv,beams,boards,tiles),(_,live,stay,rest) in zip(frames,kept):
        ids={b['id'] for b in live}
        for b in beams:
            if b['id'] in ids:continue
            out.append({'kind':'beam','wood':True,'x':0.,'y':sum(b['y'])/2,'yaw':0.,'size':(b['x'][1]-b['x'][0],BEAM_W,BEAM_H),'z0':lv['beam_z0']})
        ids={t['id'] for t in stay}
        for t in boards:
            if t['id'] in ids:continue
            out.append({'kind':'board','wood':True,'x':sum(t['x'])/2,'y':sum(t['y'])/2,'yaw':math.pi/2,'size':(t['y'][1]-t['y'][0],BOARD_W,BOARD_T),'z0':lv['beam_z1']})
        ids={t['id'] for t in rest}
        for t in tiles:
            if t['id'] in ids:continue
            out.append({'kind':'slab','wood':False,'x':sum(t['x'])/2,'y':sum(t['y'])/2,'yaw':0.,'size':(t['x'][1]-t['x'][0],t['y'][1]-t['y'][0],SLAB_T),'z0':lv['board_top']})
    live={(s['flight'],s['index']) for s in alive}
    for s in steps:
        if (s['flight'],s['index']) in live:continue
        mid=(s['a0']+s['a1'])/2;r=boundary(geo,mid,s['depth']/2);tread=max(2.,r*(s['a1']-s['a0'])/(1+STEP_OVERLAP))
        out.append({'kind':'step','wood':False,'x':r*math.cos(mid),'y':r*math.sin(mid),'yaw':mid+math.pi/2,'size':(tread,s['depth']*.8,s['z1']-s['z0']),'z0':s['z0']})
    return sorted(out,key=lambda p:p['z0'])


def fallen(geo,frames,kept,steps,alive,seed=0):
    'IA: Deja caer en vertical lo que perdió apoyo sobre la superficie más alta por debajo (tablas o losas vivas, otro escombro o el suelo), dentro de la zona central, en el sitio más bajo de varios sembrados y sin montones de más de PILE_MAX; las piezas largas se parten. Devuelve piezas caídas y cuántas se dan por retiradas.'
    import random
    rng=random.Random(seed*6151+29);r=central(geo);tops={};pieces=[];cleared=0
    if r<3:return [],len(lost_pieces(geo,frames,kept,steps,alive))
    for lv,_,stay,rest in kept:
        for t in stay:
            for c in cells_under(footprint(geo,sum(t['x'])/2,sum(t['y'])/2,0.,t['x'][1]-t['x'][0],t['y'][1]-t['y'][0])):tops.setdefault(c,[]).append(lv['board_top'])
        for t in rest:
            for c in cells_under(footprint(geo,sum(t['x'])/2,sum(t['y'])/2,0.,t['x'][1]-t['x'][0],t['y'][1]-t['y'][0])):tops.setdefault(c,[]).append(lv['top'])
    floors={k:list(v) for k,v in tops.items()}
    ceilings=sorted(lv['beam_z0'] for lv,live,_,_ in kept if live)
    for p in lost_pieces(geo,frames,kept,steps,alive):
        length,width,height=p['size'];parts=max(1,math.ceil(length/(1.6*r)))
        part=(length-FALL_BREAK*(parts-1))/parts
        for k in range(parts):
            if len(pieces)>=FALL_LIMIT:cleared+=1;continue
            off=(k-(parts-1)/2)*(part+FALL_BREAK);c,s=math.cos(p['yaw']),math.sin(p['yaw'])
            placed=None
            # Se prueban varios sitios y se queda el más bajo: el escombro se esparce en vez de apilarse en columna.
            for attempt in range(16):
                spread=1.5+attempt*.8;yaw=p['yaw']+rng.uniform(-.6,.6)
                cx=p['x']+off*c+rng.uniform(-spread,spread);cy=p['y']+off*s+rng.uniform(-spread,spread)
                scale=r/max(r,math.hypot(cx,cy)+part/2);cx,cy=cx*scale,cy*scale
                corners=footprint(geo,cx,cy,yaw,part,width)
                if not in_central(geo,corners):continue
                # Huella inflada una celda: dos piezas que no comparten celda tampoco se tocan entre centros de celda.
                cells=cells_under(footprint(geo,cx,cy,yaw,part+FALL_CELL*1.5,width+FALL_CELL*1.5))
                if not cells:continue
                # Solo superficies estrictamente por debajo: una losa sin apoyo no se queda en su propio piso.
                z=max(max([t for t in tops.get(cell,[]) if t<p['z0']-1e-6],default=0.) for cell in cells)
                base=max(max([t for t in floors.get(cell,[]) if t<p['z0']-1e-6],default=0.) for cell in cells)
                if z-base>PILE_MAX:continue
                # Apoyo real: al menos FALL_SUPPORT de la huella sobre la superficie donde se posa (no colgando de un borde).
                level=sum(1 for cell in cells if any(abs(t-z)<.05 for t in tops.get(cell,[]) if t<p['z0']-1e-6) or (z==0. and not tops.get(cell)))
                if level<FALL_SUPPORT*len(cells):continue
                if any(z<ceiling<z+height+.2 for ceiling in ceilings):continue
                if placed is None or z<placed[3]-1e-6:placed=(cx,cy,yaw,z,cells)
            if placed is None:cleared+=1;continue
            cx,cy,yaw,z,cells=placed
            for cell in cells:tops.setdefault(cell,[]).append(z+height)
            pieces.append({'kind':p['kind'],'wood':p['wood'],'x':cx,'y':cy,'yaw':yaw,'size':(part,width,height),'z0':z,'from':p['z0']})
    return pieces,cleared
