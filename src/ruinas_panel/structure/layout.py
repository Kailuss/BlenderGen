"""structure /layout — ver docs/ARCHITECTURE.md para contratos y dependencias."""

from .. import config
from .. import runtime
from itertools import combinations
import random


def distribution_seed(p):
    'IA: Respeta el bloqueo de distribución; no uses random global.'
    return p.distribution_seed if p.lock_distribution else p.seed


def level_spans(p):
    'IA: Alturas entre cotas de planta en mm; valores por defecto preservan 27/57/112 mm de las casas guardadas.'
    if p.height_type=='RUIN':return [getattr(p,'low_wall_height',27.0)-2]
    spans=[getattr(p,'ground_storey_height',config.FLOOR_PITCH)]
    if p.height_type=='TWO':spans.append(getattr(p,'upper_storey_height',config.FLOOR_PITCH))
    return spans


def upper_floor(p):
    'IA: Cota común de entreplanta y desembarco, independiente de la altura de la planta superior.'
    return 2+getattr(p,'ground_storey_height',config.FLOOR_PITCH)


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
