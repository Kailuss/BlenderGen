"""structure /walls — ver docs/ARCHITECTURE.md para contratos y dependencias."""

from .. import meta
from .. import config_masonry as masonry
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
        ob=primitives.block('Pilar trasero · sillar %s.%s'%(index,r),x-width/2,x+width/2,y-T/2-3.1,y+T/2+3.1,z0+masonry.RETURN_STONE_INSET,z1-masonry.RETURN_STONE_INSET,coll,stone)
        weather.weather_stone(ob,p.wear,p.seed+1911+r*31+index)
    terrain.earth_patch(coll,primitives.material('Tierra · arena',(.36,.31,.24)),'Tierra · pilar trasero',x,y,width/2+5,T/2+8,1.6,p.seed+890+index,p.ground_roughness)
    for ob in set(coll.objects)-before:ob['wall_id']='back'


def segment_wall(coll,p,wall_id,start,end,origin,axis,height,edges):
    'IA: Construye un tramo local con variación de juntas y proyección compartida con fachada; semillas por pared e hilada, esquinas fijas y wall_id conservado.'
    stone=primitives.material('Piedra · neutro',(.52,.52,.52))
    coremat=primitives.material('Núcleo · neutro',(.44,.44,.44))
    soil=primitives.material('Tierra · arena',(.36,.31,.24))
    before=set(coll.objects)
    length=end-start
    rh=(p.height-2)/(len(edges)-1)
    terrain.ground_strip(coll,soil,start-1,end+1,p.thickness,p.seed+len(wall_id),p.ground_roughness)
    for course in layout.return_courses(p,wall_id,start,end,height,edges):
        row,z0,z1,pieces=course['row'],course['z0'],course['z1'],course['pieces']
        for j,(a,b) in enumerate(pieces):
            # El núcleo solo entra en un pilar real; el extremo libre queda retirado.
            core_end=b+.9 if p.layout_mode=='ROOM' and j==len(pieces)-1 else b-(1.1 if j==len(pieces)-1 else -.05)
            primitives.block('Mortero · '+wall_id,a-(1.4 if j==0 else .05),core_end,-p.thickness*.32,p.thickness*.32,z0-.85,z1-.7,coll,coremat)
            rr=random.Random(p.seed+row*7919+j*31+{'left':101,'right':211,'back':307}.get(wall_id,0))
            at_end=j in (0,len(pieces)-1)
            front=p.thickness/2+p.projection*(.75 if at_end else .75+p.randomness*rr.uniform(-.15,.15))
            back=p.thickness/2+p.projection*(.75 if at_end else .75+p.randomness*rr.uniform(-.15,.15))
            ob=primitives.block('Piedra · %s.%s.%s'%(wall_id,row,j),a+masonry.RETURN_STONE_INSET,b-masonry.RETURN_STONE_INSET,-front,back,z0,z1,coll,stone)
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
    if p.thickness < 6 or p.length < 60 or p.height < 25:
        raise ValueError('Mínimos del prototipo: longitud 60, altura 25 y grosor 6 mm.')
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
    planned=layout.front_courses(p)
    courses,centers=planned['courses'],planned['centers']
    meta.put(context.scene,'puerta_generada',door)
    # Fábrica completa: las perforaciones se resuelven en assembly después de reservar apoyos.
    build_base_and_lintel(coll,stone,p,door,rh)
    audit=[]
    mortar_audit=[]
    for row,line in enumerate(courses):
        for index,(x,end) in enumerate(line):
            bounds=layout.front_stone_bounds(p,planned,row,x,end)
            z0,z1=bounds['z0'],bounds['z1']
            rr=random.Random(p.seed+row*1201+index*139)
            overlap=0 if row==rows-1 else sum(max(0,min(end,b)-max(x,a)) for a,b in courses[row+1])/(end-x)
            exposed=overlap<.05
            near_break=abs(((x+end)/2/L+.5)-p.break_position)<.32
            fractured=exposed and near_break and rr.random()<.38 and p.collapse>.05
            at_end=x<=-L/2+.01 or end>=L/2-.01
            front=T/2+p.projection*(.75 if at_end else (.75+p.randomness*rr.uniform(-.15,.15)))
            back=T/2+p.projection*(.75 if at_end else (.75+p.randomness*rr.uniform(-.15,.15)))
            bx0,bx1=bounds['x0'],bounds['x1']
            # Las juntas se unen con mortero rebajado, sin un plano inclinado interior.
            coretop=z0+.55 if fractured else bounds['core_z1']-.85
            # Solo extender mortero hacia una junta que tiene piedra al otro lado.
            # En derrumbes, huecos y extremos el núcleo queda detrás del canto,
            # incluida la pérdida superficial por desgaste.
            neighbours=[(a,b) for k,(a,b) in enumerate(line) if k!=index]
            open_left=not any(abs(b-x)<.01 for a,b in neighbours)
            open_right=not any(abs(a-end)<.01 for a,b in neighbours)
            meets_left,meets_right=bounds['meets_left'],bounds['meets_right']
            open_left=open_left and not meets_left
            open_right=open_right and not meets_right
            # Pequeño desnivel en el encuentro evita tapas coplanares superpuestas.
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
                     -reach,reach,pier_edges[j]+masonry.RETURN_STONE_INSET,pier_edges[j+1]-masonry.RETURN_STONE_INSET,
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
    if door and not door.get('gate'):
        mortar=primitives.material('Núcleo · neutro',(.44,.44,.44))
        for a,b in ((door['left']-3.5,door['left']-.1),(door['right']+.1,door['right']+3.5)):
            primitives.block('Asiento de dintel',a,b,-p.thickness*.36,p.thickness*.36,
                  door['top']-1,door['top']+1,coll,mortar)
        ob=primitives.block('Piedra dintel de puerta',door['left']-1.85,door['right']+1.85,
                 -p.thickness/2-p.projection*.75,p.thickness/2+p.projection*.75,
                 door['top'],door['lintel_top']-.2,coll,stone)
        weather.weather_stone(ob,p.wear*.4,p.seed+9540)
