"""geometry /timber — ver docs/ARCHITECTURE.md para contratos y dependencias."""

from .. import meta
from .. import runtime
from ..geometry import primitives
from mathutils import Vector
import bpy
import math
import random


def timber_beam(coll,mat,name,a,b,width,depth,seed):
    'Fibra alargada desviada por nudos; surcos interrumpidos en una malla cerrada.\n\nIA: Viga entre puntos 3D con sección cerrada; conserva el marco ortogonal para ejes X/Y/Z.'
    rr=random.Random(seed)
    axis=Vector(b)-Vector(a)
    length=axis.length
    axis.normalize()
    front=Vector((0,1,0)) if abs(axis.y)<.95 else Vector((1,0,0))
    front=(front-axis*axis.dot(front)).normalized()
    side=front.cross(axis).normalized()
    segments={'DRAFT':6,'WORK':12,'DETAIL':18}[runtime.quality]
    stations=max(5,min(60,round(length/({'DRAFT':3,'WORK':1.3,'DETAIL':.8}[runtime.quality]))))
    verts=[]
    faces=[]
    n=segments+1
    phase=rr.uniform(0,6)
    freq=rr.uniform(2.3,3.5)
    knots=[(rr.uniform(-.22,.22),rr.uniform(.22,.78),rr.uniform(.055,.09)) for _ in range(1+(length>20))]
    amount=runtime.settings.wood_grain
    for station in range(stations):
        t=station/(stations-1)
        for back in (0,1):
            for k in range(n):
                u=k/segments-.5
                warp=.04*math.sin(t*12+phase)+.02*math.sin(t*23-u*4)
                pit=0
                for ku,kt,kr in knots:
                    dt=(t-kt)/kr
                    du=(u-ku)/.17
                    influence=math.exp(-.5*dt*dt)
                    warp+=.19*math.tanh(du*2)*influence
                    pit+=.26*math.exp(-du*du*2-dt*dt*1.5)
                fiber=math.cos((u+warp)*freq*math.tau+phase)
                groove=max(0,fiber)**8
                breakup=.45+.55*(.5+.5*math.sin(t*15+u*8+phase))
                relief=amount*(-.40*groove*breakup-pit+.045*math.sin(u*27+t*41+phase))
                # Les arêtes restent solides; irrégularité douce, pas de rubans saillants.
                if k in (0,segments):
                    relief=amount*(-.05+.03*math.sin(t*17+phase))
                transverse=u*width+amount*.04*math.sin(t*9+phase)*(1-abs(2*u))
                y=(depth/2+max(-depth*.23,relief))*(1 if back else -1)
                verts.append(tuple(Vector(a)+axis*(length*t)+side*transverse+front*y))
    for station in range(stations-1):
        base=station*2*n
        nextbase=base+2*n
        for k in range(segments):
            faces.extend([(base+k,base+k+1,nextbase+k+1,nextbase+k),
                          (base+n+k,nextbase+n+k,nextbase+n+k+1,base+n+k+1)])
        faces.extend([(base,nextbase,nextbase+n,base+n),
                      (base+n-1,base+2*n-1,nextbase+2*n-1,nextbase+n-1)])
    last=(stations-1)*2*n
    for k in range(segments):
        faces.extend([(k,n+k,n+k+1,k+1),(last+k,last+k+1,last+n+k+1,last+n+k)])
    ob=primitives.mesh_obj(name,verts,faces,coll,mat)
    import bmesh
    bm=bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bm.to_mesh(ob.data)
    bm.free()
    for face in ob.data.polygons:
        face.use_smooth=True
    ob['madera']=True
    return ob


def metal_pin(coll,mat,name,x,y,z,radius,depth):
    'IA: Clavo cerrado de pocos lados; solápalo con la madera al colocarlo.'
    n=10
    verts=[]
    for side in (-1,1):
        for i in range(n):
            a=i*math.tau/n
            verts.append((x+radius*math.cos(a),y+side*depth/2,z+radius*math.sin(a)))
    faces=[tuple(range(n)),tuple(reversed(range(n,2*n)))]+[(i,i+n,(i+1)%n+n,(i+1)%n) for i in range(n)]
    return primitives.mesh_obj(name,verts,faces,coll,mat)


def wooden_door(coll,p,door):
    'IA: Hoja, refuerzos y picaporte dentro del hueco previsto; conserva grosores resistentes.'
    if not door or not p.door_leaf:
        return
    wood=primitives.material('Madera · tablones',(.33,.235,.14))
    iron=primitives.material('Hierro · forjado',(.10,.105,.11))
    left=door.get('clear_left',door['left']+.4)-.3
    right=door.get('clear_right',door['right']-.4)+.3
    top=door.get('clear_top',door['top'])+.15
    bottom=.55
    y=-p.thickness/2+1.2
    count=max(3,round((right-left)/3.2))
    pitch=(right-left)/count
    for i in range(count):
        x=left+(i+.5)*pitch
        ob=timber_beam(coll,wood,'Madera · tabla %02d'%i,(x,y,bottom),(x,y,top),pitch-.10,2.8,p.seed+730+i*17)
        ob['hoja_puerta']=True
    z1=bottom+(top-bottom)*.19
    z2=bottom+(top-bottom)*.81
    front=y-1.65
    for i,z in enumerate((z1,z2)):
        timber_beam(coll,wood,'Madera · travesaño %s'%i,(left-.05,front,z),(right+.05,front,z),1.6,1.15,p.seed+801+i)
        for x in (left+.65,(left+right)/2,right-.65):
            metal_pin(coll,iron,'Hierro · clavo',x,front-.62,z,.28,.38)
    timber_beam(coll,wood,'Madera · riostra',(left+.6,front-.03,z1+.6),(right-.6,front-.03,z2-.6),1.35,1.15,p.seed+803)
    hx=right-1.6
    hz=bottom+(top-bottom)*.51
    hy=y-2.45
    plate=primitives.block('Hierro · placa del picaporte',hx-.9,hx+.9,y-2.1,y-1.2,hz-.9,hz+1.6,coll,iron)
    metal_pin(coll,iron,'Hierro · anclaje de anilla',hx,y-2.15,hz+.85,.45,1.25)
    verts=[]
    faces=[]
    major=18
    minor=8
    radius=.85
    tube=.34
    for i in range(major):
        a=i*math.tau/major
        for j in range(minor):
            b=j*math.tau/minor
            r=radius+tube*math.cos(b)
            verts.append((hx+r*math.cos(a),hy+tube*math.sin(b),hz+r*math.sin(a)))
    for i in range(major):
        for j in range(minor):
            faces.append((i*minor+j,((i+1)%major)*minor+j,((i+1)%major)*minor+(j+1)%minor,i*minor+(j+1)%minor))
    ob=primitives.mesh_obj('Hierro · anilla del picaporte',verts,faces,coll,iron)
    import bmesh
    bm=bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bm.to_mesh(ob.data)
    bm.free()
    door['leaf']=True
    door['planks']=count
    meta.put(bpy.context.scene,'puerta_generada',door)


def wooden_frame(coll,p,door):
    'IA: Jambas y dintel apoyados en mampostería; respeta clear_left/right/top.'
    if not door or not p.wood_frame:
        return
    mat=primitives.material('Madera · envejecida',(.29,.21,.13))
    w=3.2
    depth=5.2
    y=-p.thickness/2-.3
    for side,x in enumerate((door['left']+w/2-.4,door['right']-w/2+.4)):
        timber_beam(coll,mat,'Madera · jamba %s'%side,(x,y,.6),(x,y,door['top']-.1),w,depth,p.seed+431+side)
    timber_beam(coll,mat,'Madera · cabezal',(door['left']-.9,y,door['top']-.8),
                (door['right']+.9,y,door['top']-.8),3.8,depth+.5,p.seed+620)
    door['clear_left']=door['left']+w-.4
    door['clear_right']=door['right']-w+.4
    door['clear_top']=door['top']-2.7
    meta.put(bpy.context.scene,'puerta_generada',door)
