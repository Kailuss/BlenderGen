"""geometry /terrain — ver docs/ARCHITECTURE.md para contratos y dependencias."""

from .. import runtime
from ..geometry import primitives
from mathutils import Vector
from mathutils import noise
import json
import math
import random


def height_sampler(verts,topfaces):
    'IA: Altura de los triángulos superiores por rayo vertical sobre un BVH (C); fuera del montículo devuelve la cota base.'
    from mathutils.bvhtree import BVHTree
    tree=BVHTree.FromPolygons(verts,topfaces)
    down=Vector((0,0,-1))
    def surface(x,y):
        'IA: Primera cara superior bajo (x,y); 0,25 si el punto queda fuera del terreno.'
        hit=tree.ray_cast(Vector((x,y,1000.0)),down)[0]
        return hit.z if hit is not None else .25
    return surface


def height_sampler_scan(verts,topfaces):
    'IA: Versión anterior por recorrido lineal de triángulos; se conserva solo como referencia de comparación.'
    triangles=[]
    for ids in topfaces:
        a,b,c=[verts[i] for i in ids]
        den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
        if abs(den)<1e-8:
            continue
        triangles.append((min(a[0],b[0],c[0]),max(a[0],b[0],c[0]),min(a[1],b[1],c[1]),max(a[1],b[1],c[1]),
                          c[0],c[1],(b[1]-c[1])/den,(c[0]-b[0])/den,(c[1]-a[1])/den,(a[0]-c[0])/den,a[2],b[2],c[2]))
    def surface(x,y):
        'IA: Interpola altura baricéntrica de triángulos superiores; fuera del montículo devuelve cota base.'
        for xmin,xmax,ymin,ymax,cx,cy,ux,uy,vx,vy,az,bz,cz in triangles:
            if x<xmin-.00001 or x>xmax+.00001 or y<ymin-.00001 or y>ymax+.00001:
                continue
            u=ux*(x-cx)+uy*(y-cy)
            v=vx*(x-cx)+vy*(y-cy)
            if u>=-1e-6 and v>=-1e-6 and u+v<=1.000001:
                return u*az+v*bz+(1-u-v)*cz
        return .25
    return surface


def earth_patch(coll,mat,name,cx,cy,rx,ry,height,seed,roughness):
    'IA: Montículo cerrado irregular; devuelve el muestreador usado para asentar escombros.'
    rr=random.Random(seed)
    n={'DRAFT':18,'WORK':28,'DETAIL':36}[runtime.quality]
    nr={'DRAFT':4,'WORK':7,'DETAIL':10}[runtime.quality]
    phase=rr.random()*math.tau
    def elevation(x,y,r):
        'IA: Combina lóbulos y ruido en cotas positivas; conserva el borde bajo para conectar con la peana.'
        broad=noise.noise(Vector((x*.21+seed,y*.21,seed*.13)))
        grain=noise.noise(Vector((x*1.5,y*1.5,seed*.3)))
        lobes=.5*math.sin(x*.38+phase)+.5*math.cos(y*.48-phase)
        return max(.34,.42+(height-.42)*(1-r)**1.3+roughness*(1-.65*r)*(.8*broad+.28*grain+height*.14*lobes))
    verts=[(cx,cy,elevation(cx,cy,0))]
    faces=[]
    radial=[1+.11*math.sin(k*math.tau/n*3+phase)+rr.uniform(-.05,.05) for k in range(n)]
    for ring in range(1,nr+1):
        r=ring/nr
        for k in range(n):
            a=k*math.tau/n
            jitter=rr.uniform(-.18,.18)/nr if ring<nr else 0
            x=cx+rx*(r+jitter)*radial[k]*math.cos(a)
            y=cy+ry*(r+jitter)*radial[k]*math.sin(a)
            verts.append((x,y,elevation(x,y,r)))
    for k in range(n):
        faces.append((0,1+k,1+(k+1)%n))
    for j in range(nr-1):
        a=1+j*n
        b=a+n
        for k in range(n):
            q=(k+1)%n
            if (j+k)%2:
                faces.extend([(a+k,b+k,a+q),(a+q,b+k,b+q)])
            else:
                faces.extend([(a+k,b+k,b+q),(a+k,b+q,a+q)])
    topfaces=list(faces)
    base=len(verts)
    outer=1+(nr-1)*n
    for k in range(n):
        x,y,z=verts[outer+k]
        verts.append((x,y,.03))
    for k in range(n):
        q=(k+1)%n
        faces.append((outer+k,base+k,base+q,outer+q))
    faces.append(tuple(reversed(range(base,base+n))))
    ob=primitives.mesh_obj(name,verts,faces,coll,mat)
    surface=height_sampler(verts,topfaces)
    if roughness>.01:
        gravel_batch(coll,mat,'Tierra · grumos',cx,cy,rx*.84,ry*.84,surface,
                     round((30 if runtime.quality=='DRAFT' else 90)*roughness),seed+717,.55)
    return ob,surface


def ground_strip(coll,mat,a,b,thickness,seed,roughness):
    'IA: Peana irregular bajo el tramo; conserva conexión entre suelo y mampostería.'
    rr=random.Random(seed)
    nx=max(4,round((b-a)/(3 if runtime.quality=='DRAFT' else 1.8)))
    ny=4 if runtime.quality=='DRAFT' else 8
    verts=[]
    faces=[]
    for i in range(nx+1):
        x=a+(b-a)*i/nx
        half=thickness/2+3.2+roughness*(.45*math.sin(x*.7+seed)+rr.uniform(-.35,.35))
        for j in range(ny+1):
            y=(2*j/ny-1)*half
            z=1.48+roughness*(.42*noise.noise(Vector((x*.8,y*.8,seed)))+.28*math.sin(x*.34+y*.63))
            verts.append((x,y,z))
    for i in range(nx):
        for j in range(ny):
            k=i*(ny+1)+j
            q=k+ny+1
            faces.extend([(k,q,q+1),(k,q+1,k+1)])
    topfaces=list(faces)
    ring=[i*(ny+1) for i in range(nx+1)]+[nx*(ny+1)+j for j in range(1,ny+1)]+[i*(ny+1)+ny for i in range(nx-1,-1,-1)]+list(range(ny-1,0,-1))
    base=len(verts)
    for idx in ring:
        x,y,z=verts[idx]
        verts.append((x,y,.03))
    for k,idx in enumerate(ring):
        q=(k+1)%len(ring)
        faces.append((idx,base+k,base+q,ring[q]))
    faces.append(tuple(reversed(range(base,len(verts)))))
    ob=primitives.mesh_obj('Tierra · peana',verts,faces,coll,mat)
    surface=height_sampler(verts,topfaces)
    for side in (-1,1):
        gravel_batch(coll,mat,'Tierra · granos de margen',(a+b)/2,side*(thickness/2+1.0),(b-a)*.48,1.6,
                     surface,round((b-a)*roughness*.8),seed+side,.65)
    return ob


def gravel_batch(coll,mat,name,cx,cy,rx,ry,surface,count,seed,radius_scale=1):
    'IA: Agrupa grava en una malla para limitar objetos; cada piedra debe tocar la superficie.'
    rr=random.Random(seed)
    verts=[]
    faces=[]
    for i in range(count):
        a=rr.random()*math.tau
        r=math.sqrt(rr.random())*.92
        x=cx+rx*r*math.cos(a)
        y=cy+ry*r*math.sin(a)
        size=rr.uniform(.32,1.12)*radius_scale
        n=6
        base=len(verts)
        z=min(surface(x+size*math.cos(k*math.tau/n),y+size*.8*math.sin(k*math.tau/n)) for k in range(n))-.4
        top=max(z+.2,surface(x,y)+size*.65)
        for layer in (0,1):
            for k in range(n):
                angle=k*math.tau/n
                radius=size*rr.uniform(.7,1.1)*(1 if layer==0 else .58)
                verts.append((x+radius*math.cos(angle),y+radius*.8*math.sin(angle),top if layer else z))
        faces.append(tuple(base+k for k in reversed(range(n))))
        faces.append(tuple(base+n+k for k in range(n)))
        for k in range(n):
            q=(k+1)%n
            faces.append((base+k,base+q,base+n+q,base+n+k))
    ob=primitives.mesh_obj(name,verts,faces,coll,mat)
    ob['granos']=count
    return ob


def pier_ground(coll,p,centers):
    'IA: Extiende la peana bajo pilares; no dejes apoyos fuera de la base.'
    soil=primitives.material('Tierra · arena',(.36,.31,.24))
    for i,c in enumerate(centers):
        rx=c['width_mm']/2+5
        ry=p.thickness/2+8
        earth_patch(coll,soil,'Tierra · bajo pilar %s'%i,c['x_mm'],0,rx,ry,1.6,p.seed+976+i,p.ground_roughness)


def settle_rubble(ob,surface):
    'Asiento ancho: enterrar una fracción de la cara inferior, no un solo vértice.\n\nIA: Asienta por percentil y huella de apoyo XY; conserva la auditoría apoyo_escombro.'
    heights=[surface(v.co.x,v.co.y) for v in ob.data.vertices]
    samples=sorted(v.co.z-h for v,h in zip(ob.data.vertices,heights))
    shift=samples[int(len(samples)*.18)]+.35
    for v in ob.data.vertices:
        v.co.z-=shift
    full=[max(v.co[i] for v in ob.data.vertices)-min(v.co[i] for v in ob.data.vertices) for i in (0,1)]
    for _ in range(8):
        supported=[v.co for v,h in zip(ob.data.vertices,heights) if v.co.z<=h+.1]
        spans=[(max(q[i] for q in supported)-min(q[i] for q in supported))/max(.1,full[i]) for i in (0,1)] if supported else [0,0]
        if min(spans)>=.4:
            break
        for v in ob.data.vertices:
            v.co.z-=.25
    for v in ob.data.vertices:
        v.co.z=max(.04,v.co.z)
    ob['apoyo_escombro']=json.dumps({'vertices_apoyados':len(supported),'total':len(ob.data.vertices),'anchura_relativa':spans})
