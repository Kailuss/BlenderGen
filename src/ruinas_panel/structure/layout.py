"""structure /layout — ver docs/ARCHITECTURE.md para contratos y dependencias."""

from .. import config
from .. import runtime
from itertools import combinations
import random
import math


def masonry_intervals(p,wall,z,edges=None):
    'IA: Intervalos de piedra antes de bisel/desgaste, derivados del productor puro; incluye puerta y derrumbe de fachada, no vanos posteriores de assembly.'
    if wall['id']=='front':
        plan=front_courses(p);edges=plan['edges'];result=[]
        for row,line in enumerate(plan['courses']):
            z0=edges[row]+.23;z1=edges[row+1]-.25
            for a,b in line:
                meets=any((abs(a-(c['x_mm']+c['width_mm']/2+.2))<.01 or abs(b-(c['x_mm']-c['width_mm']/2-.2))<.01) and z0<c['height_mm'] for c in plan['centers'])
                if z0<z<z1-(.28 if meets else 0):
                    result.append((a if a<=-p.length/2+.01 else a+.22,b if b>=p.length/2-.01 else b-.22))
        return result
    edges=course_layout(p)[0] if edges is None else edges
    return [(a+.18,b-.18) for c in return_courses(p,wall['id'],wall['start'],wall['end'],wall['height'],edges)
            if c['z0']<z<c['z1'] for a,b in c['pieces']]


def masonry_joints(intervals):
    'IA: Juntas nominales entre dos piedras con anchura residual suficiente para el alojamiento histórico de 5 mm; no consulta geometría.'
    ordered=sorted(intervals)
    return [((a[1]+b[0])/2,((a[1]-a[0])+(b[1]-b[0]))/2) for a,b in zip(ordered,ordered[1:])
            if -.05<=b[0]-a[1]<=1.5 and min(a[1]-a[0],b[1]-b[0])>=5.3]


def distribution_seed(p):
    'IA: Respeta el bloqueo de distribución; no uses random global.'
    return p.distribution_seed if p.lock_distribution else p.seed


def level_spans(p):
    'IA: Alturas entre cotas en mm: conserva 27/57/112 históricos; THREE añade una segunda planta superior de igual altura.'
    if p.height_type=='RUIN':return [getattr(p,'low_wall_height',27.0)-2]
    spans=[getattr(p,'ground_storey_height',config.FLOOR_PITCH)]
    if p.height_type in ('TWO','THREE'):spans.append(getattr(p,'upper_storey_height',config.FLOOR_PITCH))
    if p.height_type=='THREE':spans.append(getattr(p,'upper_storey_height',config.FLOOR_PITCH))
    return spans


def upper_floor(p):
    'IA: Cota común de entreplanta y desembarco, independiente de la altura de la planta superior.'
    return 2+getattr(p,'ground_storey_height',config.FLOOR_PITCH)


def floor_bases(p):
    'IA: Cotas base de todas las plantas, conservando 2 mm iniciales y alturas superiores compartidas en la torre de tres niveles.'
    result=[2.0]
    for height in level_spans(p)[:-1]:result.append(result[-1]+height)
    return result


def building_height(p):
    'IA: Cota superior de los muros desde el origen del modelo; conserva dos mm de base.'
    return 2+sum(level_spans(p))


def spread_positions(candidates,count,start,end,minimum):
    'IA: Elige el mayor número posible de posiciones con separación mínima, próximas a divisiones iguales del tramo; desempate determinista.'
    values=sorted(set(candidates))
    for n in range(min(count,len(values)),0,-1):
        targets=[start+(end-start)*(i+1)/(n+1) for i in range(n)]
        choices=(xs for xs in combinations(values,n) if all(b-a>=minimum-1e-6 for a,b in zip(xs,xs[1:])))
        best=min(choices,key=lambda xs:sum((a-b)**2 for a,b in zip(xs,targets)),default=None)
        if best is not None:return list(best)
    return []


def pillar_layout(p,door,rh):
    'IA: Planifica pilares intermedios antes de borrar fuente; modo manual rechaza invasiones y modo equidistante reparte sobre candidatos libres.'
    count=min(p.pillar_count,max(0,int(p.length/32)))
    mode=getattr(p,'pillar_distribution','LEGACY');rng=random.Random(distribution_seed(p)+48193)
    clearance=2+max(2.8,rh*.65)
    def free(x,width):
        'IA: Exige separación respecto a puerta y pilares de esquina/conexión, además del borde del muro.'
        for side in (-1,1):
            corner=turn_mode(p,side)!='NONE'
            connected=p.connection_enabled and (p.connection_side=='BOTH' or p.connection_side==('LEFT' if side<0 else 'RIGHT'))
            margin=(corner_width(p) if corner else 12) if corner or connected else 2
            if side*x+width/2>p.length/2-margin-2:return False
        return not (door and x+width/2>door['left']-clearance and x-width/2<door['right']+clearance)
    if mode=='LEGACY':
        result=[]
        for i in range(count):
            x=((i+1)/(count+1)+rng.uniform(-.065,.065)-.5)*p.length;width=p.pillar_width*rng.uniform(.92,1.08)
            if not (door and x+width/2>door['left']-clearance and x-width/2<door['right']+clearance):result.append((x,width))
        return result
    if mode=='CUSTOM':
        try:
            values=[float(v.strip()) for v in p.pillar_positions.split(';') if v.strip()][:p.pillar_count]
            if len(values)!=p.pillar_count or any(not 0<=v<=100 for v in values):raise ValueError()
        except ValueError:raise ValueError('Pilares: introduce un porcentaje de 0 a 100 por pilar, separado por punto y coma.') from None
        xs=sorted((u/100-.5)*p.length for u in values)
        if any(not free(x,p.pillar_width) for x in xs) or any(b-a<p.pillar_width+2 for a,b in zip(xs,xs[1:])):
            raise ValueError('Pilares manuales: invaden una puerta, una esquina o se solapan. Revisa sus posiciones.')
    else:
        candidates=[(i/24-.5)*p.length for i in range(1,24)]
        candidates += [((i+1)/(count+1)-.5)*p.length for i in range(count)]
        xs=spread_positions([x for x in candidates if free(x,p.pillar_width)],count,-p.length/2,p.length/2,p.pillar_width+2)
    return [(x,p.pillar_width) for x in xs]


def course_layout(p):
    'IA: Calcula cotas exactas de planta y mínimo de hilada; función sin geometría de Blender.'
    edges=[2.0]
    for span in level_spans(p):
        base=edges[-1];rows=max(3,round(span/p.stone_size))
        while True:
            weights=[1 if r%2==0 else p.alternate_height for r in range(rows)]
            scale=span/sum(weights)
            if min(weights)*scale>=3 or rows<=3:break
            rows-=1
        for weight in weights:
            edges.append(edges[-1]+weight*scale)
        edges[-1]=base+span
    return edges,(edges[-1]-2)/(len(edges)-1)


def turn_mode(p,side):
    'IA: Traduce lado a giro interno; conserva compatibilidad de los valores RNA guardados.'
    return p.left_turn if side<0 else p.right_turn


def corner_width(p):
    'IA: Anchura mínima de esquina según perfil; compártela entre pilares y tramos.'
    return p.thickness+p.projection*1.5+.8


def apply_profiles(p):
    'IA: Deriva medidas de presets bajo busy; CUSTOM conserva wear; restaura el estado previo y evita recursión RNA.'
    busy=runtime.busy
    runtime.busy=True
    try:
        p.thickness,p.stone_size,p.projection,p.pillar_width=config.BUILD_TYPES[p.build_type]
        p.height=building_height(p)
        if p.wear_level in config.WEAR_LEVELS:
            p.wear=config.WEAR_LEVELS[p.wear_level]
        p.left_height=p.height
        p.right_height=p.height
        p.left_turn='RIGHT' if p.layout_mode in ('TWO','ROOM') or (p.layout_mode=='ONE' and p.extra_side=='LEFT') else 'NONE'
        p.right_turn='LEFT' if p.layout_mode in ('TWO','ROOM') or (p.layout_mode=='ONE' and p.extra_side=='RIGHT') else 'NONE'
        p.left_return_length=p.building_depth
        p.right_return_length=p.building_depth
    finally:
        runtime.busy=busy


def filtered_noise(rng,samples,passes):
    'IA: Ruido blanco gaussiano suavizado (filtro 1-2-1 repetido) y normalizado a desviación 1; devuelve una función de u en [0,1].'
    values=[rng.gauss(0,1) for _ in range(samples)]
    for _ in range(passes):
        values=[(values[max(0,i-1)]+2*values[i]+values[min(samples-1,i+1)])/4 for i in range(samples)]
    mean=sum(values)/samples
    spread=(sum((v-mean)**2 for v in values)/samples)**.5 or 1
    values=[(v-mean)/spread for v in values]
    def at(u):
        'IA: Interpolación lineal del ruido suavizado en u (0-1).'
        f=max(0,min(1,u))*(samples-1)
        i=min(samples-2,int(f))
        return values[i]+(values[i+1]-values[i])*(f-i)
    return at


def merge_thin_stones(line,minimum):
    # Absorber un recorte estrecho en una piedra contigua, sin cubrir huecos.
    'IA: Fusiona intervalos demasiado estrechos; conserva cobertura y orden sin solapamientos.'
    line=list(line)
    changed=True
    while changed:
        changed=False
        for i,(a,b) in enumerate(line):
            if b-a>=minimum:
                continue
            neighbours=[]
            if i>0 and abs(line[i-1][1]-a)<.01:
                neighbours.append(i-1)
            if i+1<len(line) and abs(line[i+1][0]-b)<.01:
                neighbours.append(i+1)
            if not neighbours:
                continue
            j=min(neighbours,key=lambda k:line[k][1]-line[k][0])
            start=min(i,j)
            end=max(i,j)
            line[start:end+1]=[(min(a,line[j][0]),max(b,line[j][1]))]
            changed=True
            break
    return line


def plan_door(p):
    'IA: Valida antes de borrar fuente; con habitaciones reserva 35 mm libres tras jambas sin modificar el ajuste guardado.'
    if not p.door_enabled:
        return None
    edges,rh=course_layout(p)
    rows=len(edges)-1
    def margin(side):
        'IA: Calcula reserva lateral según pilar de conexión; no permitas puertas que invadan esquinas.'
        turned=turn_mode(p,side)!='NONE'
        connected=p.connection_enabled and (p.connection_side=='BOTH' or (side<0 and p.connection_side=='LEFT') or (side>0 and p.connection_side=='RIGHT'))
        return ((corner_width(p) if turned else 12)+2.5+max(2.8,rh*.65)) if (turned or connected) else 5
    left_margin=margin(-1)
    right_margin=margin(1)
    available=p.length-left_margin-right_margin
    if available<10:
        raise ValueError('No cabe la puerta entre los pilares: aumenta la longitud o reduce el grosor.')
    requested=p.door_width
    if p.layout_mode=='ROOM' and getattr(p,'interior_layout','OPEN')!='OPEN':
        requested=max(requested,config.INTERIOR_PASSAGE+(5.6 if p.wood_frame else 0))
        if available<requested:raise ValueError('No cabe una entrada con 35 mm libres: aumenta la longitud.')
    width=min(requested,available)
    center=(p.door_position-.5)*p.length
    center=max(-p.length/2+left_margin+width/2,min(p.length/2-right_margin-width/2,center))
    style=getattr(p,'door_style','AUTO')
    gate=style in ('WOOD_GATE','IRON_GATE') or (style=='AUTO' and (p.build_type=='PARTITION' or p.door_height+5>p.height))
    if gate:
        return {'left':center-width/2,'right':center+width/2,'top':p.door_height,'lintel_top':max(p.height,p.door_height)+1,'gate':True,'gate_material':'IRON' if style=='IRON_GATE' else 'WOOD'}
    if p.door_height+3>p.height:raise ValueError('La puerta cerrada no cabe en altura: aumenta la planta o elige una cancela.')
    index=next((i for i in range(1,rows) if edges[i]>=p.door_height-.00001),rows-1)
    return {'left':center-width/2,'right':center+width/2,'top':edges[index],'lintel_top':edges[index+1]}


def trim_door_courses(courses,door,rh):
    # Third argument is the shared elevation table (signature retained).
    'IA: Recorta hiladas por puerta; evita generar tiras residuales demasiado estrechas.'
    edges=rh
    result=[]
    for row,line in enumerate(courses):
        z=edges[row]
        if z>=door['lintel_top']-.01:
            result.append(line)
            continue
        extra=2 if z>=door['top']-.01 else 0
        left=door['left']-extra
        right=door['right']+extra
        kept=[]
        for a,b in line:
            if b<=left or a>=right:
                kept.append((a,b))
            else:
                if left-a>1.3:
                    kept.append((a,left))
                if b-right>1.3:
                    kept.append((right,b))
        result.append(kept)
    return result



def front_courses(p):
    'IA: Calcula hiladas, derrumbe, puerta y pilares sin mallas; conserva el orden de RNG y devuelve intervalos nominales en mm.'
    L,H,T=p.length,p.height,p.thickness
    dseed=distribution_seed(p);door=plan_door(p)
    z_edges,rh=course_layout(p);rows=len(z_edges)-1
    # Referencias físicas de los extremos. El límite general y las hiladas mandan.
    left=min(H,p.left_height)
    right=min(H,p.right_height)
    # Una franja corta en cada extremo preserva su altura y el apoyo de sus piedras.
    edge=min(.20,max(.10,2.2*rh/L))
    center=max(.05,min(.95,(p.break_position-edge)/(1-2*edge)))
    # Irregularidad del derrumbe, fijada por la semilla de distribución: laderas asimétricas,
    # a veces una muesca secundaria y una silueta que sigue el perfil con un paseo aleatorio gaussiano.
    cr=random.Random(dseed+61717)
    wide=(.24*cr.uniform(.7,1.35),.24*cr.uniform(.7,1.35))
    notch=(center+cr.choice((-1,1))*cr.uniform(.15,.3),cr.uniform(.08,.14),cr.uniform(.25,.5)) if cr.random()<.5 else None
    def bell(u):
        'IA: Campana del derrumbe con ancho distinto a cada lado del centro, más la muesca secundaria si la hay.'
        value=math.exp(-((u-center)/wide[0 if u<center else 1])**2)
        if notch:
            value=max(value,notch[2]*math.exp(-((u-notch[0])/notch[1])**2))
        return value
    g0=bell(0)
    g1=bell(1)
    peak=max(.1,max(bell(center),1)-((1-center)*g0+center*g1))
    def collapse_loss(x):
        'IA: Pérdida 0-1 del perfil de derrumbe en x; 0 en las franjas extremas que conservan su altura.'
        u=max(0,min(1,(x/L+.5-edge)/(1-2*edge)))
        return max(0,min(1,(bell(u)-((1-u)*g0+u*g1))/peak))
    def smooth_height(x):
        'IA: Perfil continuo del derrumbe (sin irregularidad), entre la altura de los extremos y 12 mm.'
        u=max(0,min(1,(x/L+.5-edge)/(1-2*edge)))
        baseline=left*(1-u)+right*u
        return baseline,max(12,baseline-p.collapse**1.6*(baseline-12)*collapse_loss(x))
    # Silueta: paseo aleatorio gaussiano cada media piedra que vuelve hacia el perfil (reversión 0,25);
    # el ruido crece con la pérdida local, y caídas bruscas ocasionales dejan cortes casi verticales.
    step=max(2.0,L/max(3,round(L/(rh*1.8)))/2)
    samples=int(L/step)+1
    outline=[]
    level=smooth_height(-L/2)[1]
    for i in range(samples):
        x=-L/2+i*step
        baseline,target=smooth_height(x)
        loss=collapse_loss(x)
        level+=.25*(target-level)+cr.gauss(0,1)*rh*(.5+1.3*loss)*p.collapse**1.6
        if cr.random()<.12*loss*p.collapse**1.6:
            level-=rh*cr.uniform(1.5,3)
        level=max(12,min(baseline,level))
        outline.append(level)
    def requested_height(x):
        'IA: Silueta irregular del derrumbe previa al escalonado; conserva apoyo suficiente sobre el dintel.'
        f=max(0,min(samples-1,(x+L/2)/step))
        i=min(samples-2,int(f))
        result=outline[i]+(outline[i+1]-outline[i])*(f-i)
        if door and door['left']-3*rh<=x<=door['right']+3*rh:
            result=max(result,door['lintel_top'])
        return result
    def erode_edges(line,rng,z):
        'IA: Quita al azar piedras del borde de un hueco según la pérdida local; las de encima caen por la regla de apoyo.'
        result=[]
        for i,(a,b) in enumerate(line):
            mid=(a+b)/2
            open_left=i==0 or abs(line[i-1][1]-a)>.01
            open_right=i==len(line)-1 or abs(line[i+1][0]-b)>.01
            wall_end=a<=-L/2+.01 or b>=L/2-.01
            exposed=(open_left and a>-L/2+.01) or (open_right and b<L/2-.01)
            if exposed and not wall_end and not near_door(mid,z) and rng.random()<p.collapse*(.1+.45*collapse_loss(mid)):
                continue
            result.append((a,b))
        return result
    def near_door(x,z):
        'IA: Protege el entorno del dintel hasta una hilada por encima; más arriba el derrumbe varía como el resto.'
        return door and door['left']-3*rh<=x<=door['right']+3*rh and z<=door['lintel_top']+rh
    # Aparejo a media pieza: ambos extremos terminan en piezas enteras o medias,
    # nunca en lascas residuales por acumular anchuras aleatorias.
    bays=max(3,round(L/(rh*1.8)))
    pitch=L/bays
    courses=[]
    for row in range(rows):
        jr=random.Random(dseed+row*3701)
        subdivisions=min(p.bond_subdivisions,max(1,int(pitch/3.2))) if row%2 else 1
        local_pitch=pitch/subdivisions
        offset=.5 if row%2 else 1.0
        joints=[-L/2]
        for i in range(bays*subdivisions):
            x=-L/2+(i+offset)*local_pitch
            if x<L/2-.01:
                jitter=.12 if subdivisions==1 else .08
                joints.append(x+jr.uniform(-1,1)*local_pitch*jitter*p.stone_variation)
        joints.append(L/2)
        kept=[]
        kr=random.Random(dseed+row*7919+5)
        for x,end in zip(joints,joints[1:]):
            mid=(x+end)/2
            # Variación gaussiana por piedra: escalones desiguales en vez de una piedra menos por hilada.
            zmid=(z_edges[row]+z_edges[row+1])/2
            spread=0 if near_door(mid,zmid) else kr.gauss(0,1)*rh*(.15+1.0*collapse_loss(mid))*p.collapse
            wanted=(z_edges[row]+z_edges[row+1])/2<=requested_height(mid)+spread
            support=1.0 if row==0 else sum(max(0,min(end,b)-max(x,a)) for a,b in courses[row-1])/(end-x)
            # Umbral de apoyo variable por piedra: con hiladas a media piedra, un umbral fijo del 62 %
            # quitaba siempre la piedra del borde (50 % de apoyo) y dejaba una escalera perfecta de 45°.
            need=.62 if near_door(mid,zmid) else kr.uniform(.35,.72)
            if support<need:
                continue
            # Diente: a veces sobrevive una piedra apoyada por encima del perfil.
            tooth=not near_door(mid,zmid) and kr.random()<.12*p.collapse*collapse_loss(mid)
            if wanted or tooth:
                kept.append((x,end))
        if row>0:
            kept=erode_edges(kept,kr,(z_edges[row]+z_edges[row+1])/2)
        courses.append(kept)
    def height(x):
        'IA: Consulta altura real de hiladas conservadas, no el perfil continuo del derrumbe.'
        return max([z_edges[r+1] for r,line in enumerate(courses) for a,b in line if a<=x<=b] or [z_edges[1]])
    # Planificar refuerzos antes de huecos para mantenerlos íntegros.
    centers=[]
    for cx,width in pillar_layout(p,door,rh):
        top=height(cx)
        clearance=2+max(2.8,rh*.65)
        if door and cx+width/2>door['left']-clearance and cx-width/2<door['right']+clearance:
            continue
        centers.append({'x_mm':cx,'width_mm':width,'height_mm':top})
    for side in (-1,1):
        corner=turn_mode(p,side)!='NONE'
        connection=p.connection_enabled and (p.connection_side=='BOTH' or (side<0 and p.connection_side=='LEFT') or (side>0 and p.connection_side=='RIGHT'))
        if corner or connection:
            width=corner_width(p) if corner else 12.0
            cx=side*(L/2-width/2)
            centers=[c for c in centers if abs(c['x_mm']-cx)>width+2]
            centers.append({'x_mm':cx,'width_mm':width,'height_mm':height(cx),'connection':True,'corner':side if corner else 0})
    # El pilar sustituye al aparejo en su franja: no hay dos tapas coplanares.
    trimmed=[]
    for row_index,line in enumerate(courses):
        fragments=[]
        for a,b in line:
            pieces=[(a,b)]
            for pier in centers:
                if z_edges[row_index]>=pier['height_mm']-.01:
                    continue
                left=pier['x_mm']-pier['width_mm']/2-.2
                right=pier['x_mm']+pier['width_mm']/2+.2
                remaining=[]
                for x,y in pieces:
                    if y<=left or x>=right:
                        remaining.append((x,y))
                    else:
                        if left-x>1.8:
                            remaining.append((x,left))
                        if y-right>1.8:
                            remaining.append((right,y))
                pieces=remaining
            fragments.extend(pieces)
        trimmed.append(fragments)
    courses=trimmed
    if door:
        courses=trim_door_courses(courses,door,z_edges)
    courses=[merge_thin_stones(line,max(3.2,(z_edges[r+1]-z_edges[r])*.65)) for r,line in enumerate(courses)]
    return {'courses':courses,'centers':centers,'door':door,'edges':z_edges,'row_height':rh}


def return_courses(p,wall_id,start,end,height,edges):
    'IA: Aparejo puro de retornos y trasera; intervalos nominales y cotas previos al bisel, con semillas históricas por pared.'
    length=end-start;rh=(p.height-2)/(len(edges)-1);result=[]
    bays=max(2,round(length/(rh*1.8)))
    pitch=length/bays
    for row in range(len(edges)-1):
        if edges[row]>=height-.01:
            break
        z0=edges[row]+.23
        z1=min(edges[row+1],height)-.25
        subdivisions=min(p.bond_subdivisions,max(1,int(pitch/3.2))) if row%2 else 1
        local=pitch/subdivisions
        jr=random.Random(distribution_seed(p)+row*3701+{'left':101,'right':211,'back':307}.get(wall_id,0))
        joints=[start]
        for j in range(bays*subdivisions):
            x=start+(j+(.5 if row%2 else 1))*local
            if start+.01<x<end-.01:
                jitter=.12 if subdivisions==1 else .08
                joints.append(x+jr.uniform(-1,1)*local*jitter*p.stone_variation)
        joints.append(end)
        pieces=merge_thin_stones(list(zip(joints,joints[1:])),3.2)
        result.append({'row':row,'z0':z0,'z1':z1,'pieces':pieces})
    return result
