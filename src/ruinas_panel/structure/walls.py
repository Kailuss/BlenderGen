"""structure /walls — ver docs/ARCHITECTURE.md para contratos y dependencias."""

from .. import config
from ..geometry import fracture
from ..geometry import primitives
from ..geometry import rubble
from ..geometry import terrain
from ..geometry import timber
from ..geometry import weather
from ..structure import layout
from ..structure import openings
import bpy
import json
import math
import random


def rear_pier(coll,p,x,y,edges,index):
    'IA: Esquina trasera con suelo y hiladas compatibles con las paredes contiguas.'
    stone=primitives.material('Piedra · neutro',(.52,.52,.52))
    mortar=primitives.material('Núcleo · neutro',(.44,.44,.44))
    width=layout.corner_width(p)
    T=p.thickness
    primitives.block('Pilar trasero · pie',x-width/2-1,x+width/2+1,y-T/2-4.2,y+T/2+4.2,.6,3,coll,stone)
    primitives.block('Pilar trasero · núcleo',x-width/2+.8,x+width/2-.8,y-T/2-1.5,y+T/2+1.5,1.5,p.height-1.5,coll,mortar)
    for r,(z0,z1) in enumerate(zip(edges,edges[1:])):
        ob=primitives.block('Pilar trasero · sillar %s.%s'%(index,r),x-width/2,x+width/2,y-T/2-3.1,y+T/2+3.1,z0+.18,z1-.18,coll,stone)
    terrain.earth_patch(coll,primitives.material('Tierra · arena',(.36,.31,.24)),'Tierra · pilar trasero',x,y,width/2+5,T/2+8,1.6,p.seed+890+index,p.ground_roughness)


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
    bpy.context.scene['giros_generados']=json.dumps(walls[1:])
    bpy.context.scene['paredes_generadas']=json.dumps(walls)
    return walls


def _build_wall(context, p):
    'IA: Orquesta construcción física de la fuente; no cambies orden aleatorio ni nombres sin revisar caché y semillas.'
    if p.thickness < 8 or p.length < 60 or p.height < 25:
        raise ValueError('Mínimos del prototipo: longitud 60, altura 25 y grosor 8 mm.')
    old = bpy.data.collections.get(config.COLLECTION)
    if old:
        primitives.remove_objects(old.objects)
        bpy.data.collections.remove(old)
    coll = bpy.data.collections.new(config.COLLECTION)
    context.scene.collection.children.link(coll)
    context.scene.unit_settings.system = 'METRIC'
    context.scene.unit_settings.scale_length = .001
    context.scene.unit_settings.length_unit = 'MILLIMETERS'
    stone = primitives.material('Piedra · neutro', (.52,.52,.52))
    mortar = primitives.material('Núcleo · neutro', (.44,.44,.44))
    L,H,T = p.length,p.height,p.thickness
    dseed=layout.distribution_seed(p)
    door=layout.plan_door(p)
    rng = random.Random(p.seed)
    detail = random.Random(p.seed+91073)
    z_edges,rh=layout.course_layout(p)
    rows=len(z_edges)-1
    context.scene["hiladas_generadas"]=json.dumps(z_edges)
    # Referencias físicas de los extremos. El límite general y las hiladas mandan.
    left=min(H,p.left_height)
    right=min(H,p.right_height)
    # Una franja corta en cada extremo preserva su altura y el apoyo de sus piedras.
    edge=min(.20,max(.10,2.2*rh/L))
    center=max(.05,min(.95,(p.break_position-edge)/(1-2*edge)))
    g0=math.exp(-(center/.24)**2)
    g1=math.exp(-((1-center)/.24)**2)
    peak=max(.1,1-((1-center)*g0+center*g1))
    def requested_height(x):
        'IA: Perfil de derrumbe previo al escalonado; conserva apoyo suficiente sobre el dintel.'
        u=max(0,min(1,(x/L+.5-edge)/(1-2*edge)))
        baseline=left*(1-u)+right*u
        gaussian=math.exp(-((u-center)/.24)**2)
        loss=max(0,min(1,(gaussian-((1-u)*g0+u*g1))/peak))
        result=max(12,baseline-p.collapse*(baseline-12)*loss)
        if door and door['left']-3*rh<=x<=door['right']+3*rh:
            result=max(result,door['lintel_top'])
        return result
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
        for x,end in zip(joints,joints[1:]):
            wanted=(z_edges[row]+z_edges[row+1])/2<=requested_height((x+end)/2)
            support=1.0 if row==0 else sum(max(0,min(end,b)-max(x,a)) for a,b in courses[row-1])/(end-x)
            if wanted and support>=.62:
                kept.append((x,end))
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
    context.scene['puerta_generada']=json.dumps(door)
    # Huecos pasantes definidos por piedras omitidas: sin cavidades de resina ni tapones de mortero.
    cells=[(r,k,a,b) for r,line in enumerate(courses) for k,(a,b) in enumerate(line)]
    candidates=[((a+b)/2,(z_edges[r]+z_edges[r+1])/2) for r,k,a,b in cells if r>=1]
    random.Random(dseed+80431).shuffle(candidates)
    holes=[]
    omitted=set()
    for cx,cz in candidates:
        if len(holes)>=p.hole_count:
            break
        rx=p.hole_size/2
        rz=rx*.8
        group=[(r,k,a,b) for r,k,a,b in cells
               if (((a+b)/2-cx)/rx)**2+(((z_edges[r]+z_edges[r+1])/2-cz)/rz)**2<=1]
        if not group:
            continue
        if door and any(a<door["right"]+rh and b>door["left"]-rh for r,k,a,b in group):
            continue
        # Una selección debe formar un único hueco, no varias perforaciones separadas.
        connected={0}
        stack=[0]
        while stack:
            r,k,a,b=group[stack.pop()]
            for q,(s,j,c,d) in enumerate(group):
                adjacent=(r==s and min(b,d)-max(a,c)>=-.01) or (abs(r-s)==1 and min(b,d)-max(a,c)>1)
                if q not in connected and adjacent:
                    connected.add(q)
                    stack.append(q)
        if len(connected)!=len(group):
            continue
        x0=min(c[2] for c in group)
        x1=max(c[3] for c in group)
        z0=z_edges[min(c[0] for c in group)]
        z1=z_edges[max(c[0] for c in group)+1]
        # Mantener pie, extremos, espesor de pared sobre el hueco y separación entre huecos.
        if z0<z_edges[1]-.01 or min(x0+L/2,L/2-x1)<rh:
            continue
        if any(x0<c['x_mm']+c['width_mm']/2+2 and x1>c['x_mm']-c['width_mm']/2-2 for c in centers):
            continue
        if min(height(x0+(x1-x0)*i/12) for i in range(13))-z1<rh*1.05:
            continue
        if any(x0<h['x1']+rh and x1>h['x0']-rh and z0<h['z1']+rh and z1>h['z0']-rh for h in holes):
            continue
        if (x1-x0)>max(p.hole_size*1.65,rh*2.0):
            continue
        holes.append({'x':cx,'z':cz,'x0':x0,'x1':x1,'z0':z0,'z1':z1,
                      'removed_cells':[(r,k) for r,k,a,b in group]})
        omitted.update((r,k) for r,k,a,b in group)
    if p.hole_damage>0:
        for hindex,h in enumerate(holes):
            r,k=min(h['removed_cells'])
            a,b=courses[r][k]
            fracture.hole_fragment(coll,stone,mortar,a,b,z_edges[r]+.2,z_edges[r+1]-.25,T,p.projection,p.hole_damage,p.seed+8521+hindex,p.wear)
    context.scene['huecos_generados']=json.dumps(holes)
    context.scene['huecos_solicitados']=p.hole_count
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
    context.scene['aparejo_escalonado']=json.dumps(audit)
    context.scene['mortero_retranqueado']=json.dumps(mortar_audit)
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
    context.scene['pilares_generados']=json.dumps(centers)
    rubble.build_rubble(coll,stone,mortar,p,door,rh)
    timber.wooden_frame(coll,p,door)
    timber.wooden_door(coll,p,door)
    for ob in coll.objects:
        co=primitives.coords(ob)
        co[:,0]=co[:,0].clip(-L/2,L/2)
        primitives.set_coords(ob,co)
    terrain.pier_ground(coll,p,centers)
    walls=build_returns(coll,p,centers,z_edges)
    openings.architectural_openings(coll,p,walls,door,z_edges)
    context.scene['parametros_muro'] = json.dumps({k:getattr(p,k) for k in config.FIELDS},ensure_ascii=False)
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
