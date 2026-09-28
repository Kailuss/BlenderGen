"""structure /walls — ver docs/ARCHITECTURE.md para contratos y dependencias."""

from .. import meta
from .. import config
from .. import runtime
from ..geometry import fracture
from ..geometry import primitives
from ..geometry import rubble
from ..geometry import terrain
from ..geometry import timber
from ..geometry import weather
from ..structure import layout
from ..structure import openings
import bpy
import math
import random


def rear_pier(coll,p,x,y,edges,index):
    'IA: Esquina trasera con suelo y hiladas compatibles con las paredes contiguas.'
    before=set(coll.objects)
    stone=primitives.material('Piedra · neutro',(.52,.52,.52))
    mortar=primitives.material('Núcleo · neutro',(.44,.44,.44))
    width=layout.corner_width(p)
    T=p.thickness
    primitives.block('Pilar trasero · pie',x-width/2-1,x+width/2+1,y-T/2-4.2,y+T/2+4.2,.6,3,coll,stone)
    primitives.block('Pilar trasero · núcleo',x-width/2+.8,x+width/2-.8,y-T/2-1.5,y+T/2+1.5,1.5,p.height-1.5,coll,mortar)
    for r,(z0,z1) in enumerate(zip(edges,edges[1:])):
        ob=primitives.block('Pilar trasero · sillar %s.%s'%(index,r),x-width/2,x+width/2,y-T/2-3.1,y+T/2+3.1,z0+.18,z1-.18,coll,stone)
        weather.weather_stone(ob,p.wear,p.seed+1911+r*31+index)
    terrain.earth_patch(coll,primitives.material('Tierra · arena',(.36,.31,.24)),'Tierra · pilar trasero',x,y,width/2+5,T/2+8,1.6,p.seed+890+index,p.ground_roughness)
    for ob in set(coll.objects)-before:ob['wall_id']='back'


def segment_wall(coll,p,wall_id,start,end,origin,axis,height,edges):
    'IA: Construye un tramo en coordenadas locales y luego transforma; asigna wall_id a sus piezas.'
    stone=primitives.material('Piedra · neutro',(.52,.52,.52))
    coremat=primitives.material('Núcleo · neutro',(.44,.44,.44))
    soil=primitives.material('Tierra · arena',(.36,.31,.24))
    before=set(coll.objects)
    length=end-start
    rh=(p.height-2)/(len(edges)-1)
    terrain.ground_strip(coll,soil,start-1,end+1,p.thickness,p.seed+len(wall_id),p.ground_roughness)
    bays=max(2,round(length/(rh*1.8)))
    pitch=length/bays
    for row in range(len(edges)-1):
        if edges[row]>=height-.01:
            break
        z0=edges[row]+.23
        z1=min(edges[row+1],height)-.25
        subdivisions=min(p.bond_subdivisions,max(1,int(pitch/3.2))) if row%2 else 1
        local=pitch/subdivisions
        joints=[start]
        for j in range(bays*subdivisions):
            x=start+(j+(.5 if row%2 else 1))*local
            if start+.01<x<end-.01:
                joints.append(x)
        joints.append(end)
        pieces=layout.merge_thin_stones(list(zip(joints,joints[1:])),3.2)
        for j,(a,b) in enumerate(pieces):
            # El núcleo solo entra en un pilar real; el extremo libre queda retirado.
            core_end=b+.9 if p.layout_mode=='ROOM' and j==len(pieces)-1 else b-(1.1 if j==len(pieces)-1 else -.05)
            primitives.block('Mortero · '+wall_id,a-(1.4 if j==0 else .05),core_end,-p.thickness*.32,p.thickness*.32,z0-.85,z1-.7,coll,coremat)
            ob=primitives.block('Piedra · %s.%s.%s'%(wall_id,row,j),a+.18,b-.18,-p.thickness/2-p.projection*.75,p.thickness/2+p.projection*.75,z0,z1,coll,stone)
            weather.weather_stone(ob,p.wear,p.seed+191+row*31+j+len(wall_id))
    for ob in set(coll.objects)-before:
        co=primitives.coords(ob)
        x,y=co[:,0].copy(),co[:,1].copy()
        co[:,0]=origin[0]+axis[0]*x-axis[1]*y
        co[:,1]=origin[1]+axis[1]*x+axis[0]*y
        primitives.set_coords(ob,co)
        ob['wall_id']=wall_id
    return {'id':wall_id,'start':start,'end':end,'origin':origin,'axis':axis,'height':height}


def build_returns(coll,p,centers,edges):
    'IA: Construye L/U/habitación; devuelve descriptores locales usados por ventanas y vigas.'
    walls=[{'id':'front','start':-p.length/2,'end':p.length/2,'origin':(0,0),'axis':(1,0),'height':p.height}]
    room=p.layout_mode=='ROOM'
    depth=p.building_depth+p.thickness/2+3.42
    corners=[]
    for side in (-1,1):
        if layout.turn_mode(p,side)=='NONE':
            continue
        pier=next(c for c in centers if c.get('corner')==side)
        cx=pier['x_mm']
        corners.append(cx)
        start=p.thickness/2+3.42
        end=depth-(p.thickness/2+3.42 if room else 0)
        walls.append(segment_wall(coll,p,'left' if side<0 else 'right',start,end,(cx,0),(0,1),pier['height_mm'],edges))
        if room:
            rear_pier(coll,p,cx,depth,edges,side)
    if room:
        left,right=sorted(corners)
        gap=layout.corner_width(p)/2+.25
        walls.append(segment_wall(coll,p,'back',left+gap,right-gap,(0,depth),(1,0),p.height,edges))
    meta.put(bpy.context.scene,'giros_generados',walls[1:])
    meta.put(bpy.context.scene,'paredes_generadas',walls)
    return walls


def _build_wall(context, p):
    'IA: Primera fase: fábrica base, pilares y suelo exterior; assembly añade influencias y carpintería después. Mantén nombres y semillas.'
    if p.thickness < 8 or p.length < 60 or p.height < 25:
        raise ValueError('Mínimos del prototipo: longitud 60, altura 25 y grosor 8 mm.')
    old = bpy.data.collections.get(config.COLLECTION)
    if old:
        primitives.remove_objects(old.objects)
        bpy.data.collections.remove(old)
    coll = bpy.data.collections.new(config.COLLECTION)
    context.scene.collection.children.link(coll)
    stone = primitives.material('Piedra · neutro', (.52,.52,.52))
    mortar = primitives.material('Núcleo · neutro', (.44,.44,.44))
    L,H,T = p.length,p.height,p.thickness
    dseed=layout.distribution_seed(p)
    door=layout.plan_door(p)
    rng = random.Random(p.seed)
    detail = random.Random(p.seed+91073)
    z_edges,rh=layout.course_layout(p)
    rows=len(z_edges)-1
    meta.put(context.scene,'hiladas_generadas',z_edges)
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
        return baseline,max(12,baseline-p.collapse*(baseline-12)*collapse_loss(x))
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
        level+=.25*(target-level)+cr.gauss(0,1)*rh*(.5+1.3*loss)*p.collapse
        if cr.random()<.12*loss*p.collapse:
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
    pier_rng=random.Random(dseed+48193)
    centers=[]
    for i in range(min(p.pillar_count,max(0,int(L/32)))):
        u=(i+1)/(min(p.pillar_count,max(0,int(L/32)))+1)+pier_rng.uniform(-.065,.065)
        cx=(u-.5)*L
        width=p.pillar_width*pier_rng.uniform(.92,1.08)
        top=height(cx)
        clearance=2+max(2.8,rh*.65)
        if door and cx+width/2>door['left']-clearance and cx-width/2<door['right']+clearance:
            continue
        centers.append({'x_mm':cx,'width_mm':width,'height_mm':top})
    for side in (-1,1):
        corner=layout.turn_mode(p,side)!='NONE'
        connection=p.connection_enabled and (p.connection_side=='BOTH' or (side<0 and p.connection_side=='LEFT') or (side>0 and p.connection_side=='RIGHT'))
        if corner or connection:
            width=layout.corner_width(p) if corner else 12.0
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
        courses=layout.trim_door_courses(courses,door,z_edges)
    courses=[layout.merge_thin_stones(line,max(3.2,(z_edges[r+1]-z_edges[r])*.65)) for r,line in enumerate(courses)]
    meta.put(context.scene,'puerta_generada',door)
    # Fábrica completa: las perforaciones se resuelven en assembly después de reservar apoyos.
    holes=[];omitted=set()
    build_base_and_lintel(coll,stone,p,door,rh)
    audit=[]
    mortar_audit=[]
    for row,line in enumerate(courses):
        for index,(x,end) in enumerate(line):
            if (row,index) in omitted:
                continue
            z0=z_edges[row]+.23
            z1=z_edges[row+1]-.25
            rr=random.Random(p.seed+row*1201+index*139)
            overlap=0 if row==rows-1 else sum(max(0,min(end,b)-max(x,a)) for a,b in courses[row+1])/(end-x)
            exposed=overlap<.05
            near_break=abs(((x+end)/2/L+.5)-p.break_position)<.32
            fractured=exposed and near_break and rr.random()<.38 and p.collapse>.05
            at_end=x<=-L/2+.01 or end>=L/2-.01
            front=T/2+p.projection*(.75 if at_end else (.75+p.randomness*rr.uniform(-.15,.15)))
            back=T/2+p.projection*(.75 if at_end else (.75+p.randomness*rr.uniform(-.15,.15)))
            bx0=x if x<=-L/2+.01 else x+.22
            bx1=end if end>=L/2-.01 else end-.22
            # Las juntas se unen con mortero rebajado, sin un plano inclinado interior.
            coretop=z0+.55 if fractured else z1-.85
            # Solo extender mortero hacia una junta que tiene piedra al otro lado.
            # En derrumbes, huecos y extremos el núcleo queda detrás del canto,
            # incluida la pérdida superficial por desgaste.
            neighbours=[(a,b) for k,(a,b) in enumerate(line) if k!=index and (row,k) not in omitted]
            open_left=not any(abs(b-x)<.01 for a,b in neighbours)
            open_right=not any(abs(a-end)<.01 for a,b in neighbours)
            meets_left=any(abs(x-(c['x_mm']+c['width_mm']/2+.2))<.01 and z0<c['height_mm'] for c in centers)
            meets_right=any(abs(end-(c['x_mm']-c['width_mm']/2-.2))<.01 and z0<c['height_mm'] for c in centers)
            open_left=open_left and not meets_left
            open_right=open_right and not meets_right
            # Pequeño desnivel en el encuentro evita tapas coplanares superpuestas.
            if meets_left or meets_right:
                z1-=.28
            inset=min(1.6,(bx1-bx0)*.32)
            mx0=bx0+inset if open_left else x-(1.05 if meets_left else .05)
            mx1=bx1-inset if open_right else end+(1.05 if meets_right else .05)
            mortar_audit.append({'row':row,'stone_x0':bx0,'stone_x1':bx1,
                                 'mortar_x0':mx0,'mortar_x1':mx1,
                                 'open_left':open_left,'open_right':open_right})
            core=primitives.block('Mortero · hilada %02d.%02d'%(row,index),mx0,mx1,
                  -T*.36,T*.36,max(.8,z0-1.0),coretop,coll,mortar)
            if fractured:
                ob=fracture.fractured_block('Piedra fracturada · hilada %02d.%02d'%(row,index),
                                   bx0,bx1,-front,back,z0,z1,coll,stone,p.seed+row*701+index)
                weather.weather_stone(ob,p.wear,p.seed+row*701+index)
            else:
                ob=primitives.block('Piedra entera · hilada %02d.%02d'%(row,index),bx0,bx1,
                         -front,back,z0,z1,coll,stone,detail,0 if at_end else (.025+p.wear*.08)*p.randomness)
                weather.weather_stone(ob,p.wear,p.seed+row*701+index)
            fracture.opening_damage(ob,core,holes,bx0,bx1,z0,z1,p.hole_damage,p.seed+row*811+index)
            audit.append({'row':row,'x0':x,'x1':end,'z0':z0,'z1':z1,'fractured':fractured})
    meta.put(context.scene,'aparejo_escalonado',audit)
    meta.put(context.scene,'mortero_retranqueado',mortar_audit)
    # Pilares trabados: posiciones estratificadas con variación recuperable por semilla.
    for i,pier in enumerate(centers):
        cx= pier['x_mm']
        width=pier['width_mm']
        top=pier['height_mm']
        primitives.block('Pilar %s · pie'%i,cx-width/2-1,cx+width/2+1,
              -T/2-4.2,T/2+4.2,.6,3.0,coll,stone)
        primitives.block('Pilar %s · núcleo'%i,cx-width/2+.65,cx+width/2-.65,
              -T/2-1.6,T/2+1.6,1.5,top-1.5,coll,mortar)
        pier_edges=[z for z in z_edges if z<top-.01]+[top]
        for j in range(len(pier_edges)-1):
            rr=random.Random(p.seed+6150+i*73+j)
            # Alternancia de anchura sin desplazar el eje de apoyo.
            half=width/2 if pier.get('connection') else width/2+(0.15 if j%2==0 else -.10)
            reach=T/2+3.1+rr.uniform(-.08,.08)
            ob=primitives.block('Pilar %s · sillar %02d'%(i,j),cx-half,cx+half,
                     -reach,reach,pier_edges[j]+.18,pier_edges[j+1]-.18,
                     coll,stone,None if pier.get("connection") else rr,0 if pier.get("connection") else .05)
            if not pier.get('connection'):
                weather.weather_stone(ob,p.wear,p.seed+i*19+j)
            else:
                ob['connection_face']=True
                weather.weather_stone(ob,p.wear,p.seed+i*19+j)
    meta.put(context.scene,'pilares_generados',centers)
    for ob in coll.objects:
        co=primitives.coords(ob)
        co[:,0]=co[:,0].clip(-L/2,L/2)
        primitives.set_coords(ob,co)
    build_returns(coll,p,centers,z_edges)
    return coll


def build_base_and_lintel(coll,stone,p,door,rh):
    'IA: Añade apoyos/dintel y marco; respeta las cotas calculadas por plan_door.'
    bounds=[(-p.length/2,p.length/2)] if not door else [(-p.length/2,door['left']),(door['right'],p.length/2)]
    for i,(a,b) in enumerate(bounds):
        terrain.ground_strip(coll,primitives.material('Tierra · arena',(.36,.31,.24)),a,b,p.thickness,p.seed+i,p.ground_roughness)
    if door:
        mortar=primitives.material('Núcleo · neutro',(.44,.44,.44))
        for a,b in ((door['left']-3.5,door['left']-.1),(door['right']+.1,door['right']+3.5)):
            primitives.block('Asiento de dintel',a,b,-p.thickness*.36,p.thickness*.36,
                  door['top']-1,door['top']+1,coll,mortar)
        ob=primitives.block('Piedra dintel de puerta',door['left']-1.85,door['right']+1.85,
                 -p.thickness/2-p.projection*.75,p.thickness/2+p.projection*.75,
                 door['top'],door['lintel_top']-.2,coll,stone)
        weather.weather_stone(ob,p.wear*.4,p.seed+9540)
