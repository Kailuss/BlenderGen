"""Alféizares y balcones: piezas cerradas, apoyos embebidos y hierro repetitivo lowpoly."""
import math
import random
from mathutils import Vector
from . import primitives


def place(ob,w):
    'IA: Transforma geometría local al tramo; asigna wall_id para agrupación sin alterar normales.'
    co=primitives.coords(ob);x,y=co[:,0].copy(),co[:,1].copy()
    ox,oy=w['origin'];ax,ay=w['axis']
    co[:,0]=ox+ax*x-ay*y;co[:,1]=oy+ay*x+ax*y
    primitives.set_coords(ob,co);ob['wall_id']=w['id']
    return ob


def sill(coll,p,w,x0,x1,z):
    'IA: Loseta pasante y labio interior solapados físicamente; cubre la junta inferior del hueco sin caras coplanares.'
    mat=primitives.material('Piedra · neutro',(.52,.52,.52))
    outward=1 if w['id'] in ('left','back') else -1
    ob=primitives.block('Piedra · alféizar interior',x0-.8,x1+.8,-p.thickness/2-2,p.thickness/2+2,z-.85,z+.7,coll,mat)
    ob['protected_sill']=True
    place(ob,w)
    edge=-outward*(p.thickness/2+1.35)
    ob=primitives.block('Piedra · reborde de alféizar',x0-.6,x1+.6,edge-.55,edge+.55,z+.45,z+1.4,coll,mat)
    ob['protected_sill']=True
    place(ob,w)


def rod(coll,mat,w,name,points,radius=.45):
    'IA: Tubo hexagonal cerrado sobre una polilínea; une anillos, nunca segmentos sueltos o puntas infinitas.'
    points=[Vector(v) for v in points];verts=[];faces=[]
    for i,point in enumerate(points):
        tangent=(points[min(len(points)-1,i+1)]-points[max(0,i-1)]).normalized()
        reference=Vector((0,1,0)) if abs(tangent.y)<.9 else Vector((1,0,0))
        u=tangent.cross(reference).normalized();v=tangent.cross(u)
        for j in range(6):
            q=point+radius*(math.cos(j*math.tau/6)*u+math.sin(j*math.tau/6)*v)
            verts.append(tuple(q))
    faces.append(tuple(reversed(range(6))))
    for i in range(len(points)-1):
        for j in range(6):
            a=i*6+j;b=i*6+(j+1)%6
            faces.append((a,b,b+6,a+6))
    faces.append(tuple(range(len(verts)-6,len(verts))))
    return place(primitives.mesh_obj(name,verts,faces,coll,mat),w)


def arrow(coll,mat,w,x,y,z):
    'IA: Remate de flecha romo, con cabeza ensanchada y extremo truncado de 0,4 mm.'
    verts=[]
    for height,width in ((0,.32),(.6,.95),(1.9,.2)):
        for dx,dy in ((-1,-1),(1,-1),(1,1),(-1,1)):
            verts.append((x+dx*width,y+dy*.3,z+height))
    faces=[(3,2,1,0),(8,9,10,11)]
    for k in (0,4):
        faces.extend((k+j,k+(j+1)%4,k+(j+1)%4+4,k+j+4) for j in range(4))
    place(primitives.mesh_obj('Hierro · flecha roma',verts,faces,coll,mat),w)


def balcony(coll,p,w,x0,x1,z,seed):
    'IA: Plataforma apoyada en el muro; barandilla en U, travesaños y motivos repetidos con tres grados de torsión o rotura.'
    stone=primitives.material('Piedra · neutro',(.52,.52,.52))
    iron=primitives.material('Hierro · forjado',(.10,.105,.11))
    side=1 if w['id'] in ('left','back') else -1
    rear=side*(p.thickness/2-1.2);front=side*(p.thickness/2+14)
    left,right=x0-2,x1+2
    ob=primitives.block('Piedra · plataforma balcón',left,right,min(rear,front)-.6,max(rear,front)+.6,z-2.3,z+.1,coll,stone)
    place(ob,w)
    # Dos ménsulas penetran en el muro y bajo la plataforma.
    for x in (left+2,right-2):
        ob=primitives.block('Piedra · ménsula balcón',x-1.1,x+1.1,min(rear,front*.75),max(rear,front*.75),z-6,z-1.9,coll,stone)
        place(ob,w)
    rng=random.Random(seed);grade=int(p.iron_damage)
    for height in (5,12):
        rod(coll,iron,w,'Hierro · travesaño balcón',[(left,rear,z+height),(left,front,z+height),(right,front,z+height),(right,rear,z+height)],.6)
    count=max(3,round((right-left)/4))
    for i in range(count+1):
        x=left+(right-left)*i/count
        broken=p.iron_mode=='BROKEN' and 0<i<count and rng.random()<grade*.24
        sway=rng.uniform(-1,1)*grade*.45
        if broken:
            rod(coll,iron,w,'Hierro · barrote roto inferior',[(x,front,z),(x,front,z+5.2),(x+sway,front+side*.7,z+6.5)],.48)
            rod(coll,iron,w,'Hierro · barrote roto superior',[(x-sway,front+side*.5,z+9),(x,front,z+12),(x,front,z+14)],.48)
        else:
            rod(coll,iron,w,'Hierro · barrote torcido',[(x,front,z),(x+sway,front+side*abs(sway),z+3),(x,front,z+5),(x-sway,front,z+8),(x,front,z+12),(x,front,z+14)],.48)
        arrow(coll,iron,w,x,front,z+13.7)
        # Rombo repetido engarzado al travesaño inferior y al barrote.
        if i<count and not broken:
            cx=x+(right-left)/count/2
            rod(coll,iron,w,'Hierro · filigrana rombo',[(cx,front,z+5),(cx+1.1,front,z+6.7),(cx,front,z+8.4),(cx-1.1,front,z+6.7),(cx,front,z+4.9)],.32)
    for x in (left,right):
        rod(coll,iron,w,'Hierro · retorno anclado',[(x,rear,z),(x,rear,z+12.2)],.55)


def window_iron(coll,p,w,x0,x1,z0,z1,y):
    'IA: Dos pletinas sobre las jambas y pequeñas volutas ancladas; el quicio y el vano quedan libres.'
    mat=primitives.material('Hierro · forjado',(.10,.105,.11))
    side=1 if y>0 else -1;front=y+side*1.7
    for x in (x0+.5,x1-.5):
        for z in (z0+5,z1-4):
            rod(coll,mat,w,'Hierro · pletina ventana',[(x,front,z-1.2),(x,front,z+1.2)],.36)
            rod(coll,mat,w,'Hierro · voluta ventana',[(x,front,z),(x+.8,front,z+.4),(x+.9,front,z+1),(x+.35,front,z+1.35),(x,front,z+1)],.23)
