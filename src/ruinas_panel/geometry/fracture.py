"""geometry /fracture — ver docs/ARCHITECTURE.md para contratos y dependencias."""

from .. import config
from .. import runtime
from ..geometry import primitives
from ..geometry import weather
from ..services import profiling
from mathutils import Euler
from mathutils import Vector
import bpy
import json
import math
import random
import zlib


@profiling.timed("grietas")
def crack_stone(ob, amount, seed, coll, mat):
    'IA: Grietas ramificadas desde aristas; revierte cada rama cuyo booleano quite más de CRACK_MAX_VOLUME_LOSS del volumen.'
    if amount<=0:
        return
    import bmesh
    rr=random.Random(seed)
    lo=[min(v.co[i] for v in ob.data.vertices) for i in range(3)]
    hi=[max(v.co[i] for v in ob.data.vertices) for i in range(3)]
    if hi[0]-lo[0]<1.8 or hi[2]-lo[2]<1.3:
        return
    p=runtime.settings
    span_x=hi[0]-lo[0]
    span_z=hi[2]-lo[2]
    width=(.42+.42*amount)*(1+rr.uniform(-.4,.4)*p.crack_width_var)
    depth=.55+.8*amount
    count=rr.randint(1,p.cracks_per_stone) if min(span_x,span_z)>3.5 else 1
    paths=[]
    roots=[]
    branches=[]
    for root_index in range(count):
        edge=rr.randrange(4)
        u=(root_index+rr.uniform(.35,.65))/count
        if edge==0:
            root=Vector((lo[0]+span_x*u,hi[2]+.45))
            direction=Vector((0,-1))
            span=span_z
        elif edge==1:
            root=Vector((lo[0]+span_x*u,lo[2]-.45))
            direction=Vector((0,1))
            span=span_z
        elif edge==2:
            root=Vector((lo[0]-.45,lo[2]+span_z*u))
            direction=Vector((1,0))
            span=span_x
        else:
            root=Vector((hi[0]+.45,lo[2]+span_z*u))
            direction=Vector((-1,0))
            span=span_x
        angle=rr.uniform(-.6,.6)*p.crack_angle_var
        direction=Vector((direction.x*math.cos(angle)-direction.y*math.sin(angle),direction.x*math.sin(angle)+direction.y*math.cos(angle)))
        length=span*.66*(1+rr.uniform(-.4,.25)*p.crack_length_var)
        end=root+direction*length
        end.x=max(lo[0]+.45,min(hi[0]-.45,end.x))
        end.y=max(lo[2]+.45,min(hi[2]-.45,end.y))
        across=Vector((-direction.y,direction.x))
        main=[root]
        for t in (.33,.66):
            main.append(root.lerp(end,t)+across*rr.uniform(-.35,.35)*p.crack_path_var)
        main.append(end)
        paths.append((main,1.0))
        roots.append({'edge':edge,'point':list(root),'length':length,'angle':angle})
        for branch_index in range(1+(rr.random()<.35)):
            start=main[1+branch_index]
            turn=rr.uniform(.65,1.1)*(1 if branch_index==0 else -1)
            branch_dir=Vector((direction.x*math.cos(turn)-direction.y*math.sin(turn),direction.x*math.sin(turn)+direction.y*math.cos(turn)))
            tip=start+branch_dir*length*rr.uniform(.25,.42)
            tip.x=max(lo[0]+.35,min(hi[0]-.35,tip.x))
            tip.y=max(lo[2]+.35,min(hi[2]-.35,tip.y))
            if (tip-start).length<.45:
                continue
            paths.append(([start,start.lerp(tip,.5)+across*rr.uniform(-.12,.12),tip],.78))
            branches.append({'root':root_index,'start':list(start),'tip':list(tip)})
    ob['parametros_grieta']=json.dumps({'count':count,'width':width,'roots':roots,'branches':branches,'bounds':[lo,hi]})
    changed=False
    reverted=0
    volume=primitives.mesh_volume(ob.data)
    for path,scale in paths:
        verts=[]
        faces=[]
        for i,q in enumerate(path):
            tangent=path[min(i+1,len(path)-1)]-path[max(0,i-1)]
            tangent.normalize()
            across=Vector((tangent.y,-tangent.x))
            taper=1-.40*i/(len(path)-1)
            for delta,y in ((-width*scale*taper,lo[1]-.15),(width*scale*taper,lo[1]-.15),(0,lo[1]+depth*scale)):
                point=q+across*delta
                verts.append((point.x,y,point.y))
        last=3*(len(path)-1)
        faces.extend([(2,1,0),(last,last+1,last+2)])
        for i in range(len(path)-1):
            for j in range(3):
                faces.append((i*3+j,i*3+(j+1)%3,(i+1)*3+(j+1)%3,(i+1)*3+j))
        cut=primitives.mesh_obj('Cortador temporal',verts,faces,coll,mat)
        bm=bmesh.new()
        bm.from_mesh(cut.data)
        bmesh.ops.triangulate(bm,faces=list(bm.faces))
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
        bm.to_mesh(cut.data)
        bm.free()
        bpy.context.view_layer.objects.active=ob
        backup=ob.data.copy()
        mod=ob.modifiers.new('Rama de grieta','BOOLEAN')
        mod.operation='DIFFERENCE'
        mod.solver='EXACT'
        mod.object=cut
        bpy.ops.object.modifier_apply(modifier=mod.name)
        after=primitives.mesh_volume(ob.data) if ob.data.vertices else 0
        # El booleano EXACT puede devolver solo un fragmento: se descarta esa rama.
        if after<volume*(1-config.CRACK_MAX_VOLUME_LOSS):
            failed=ob.data
            ob.data=backup.copy()
            bpy.data.meshes.remove(failed)
            reverted+=1
        else:
            changed=True
            volume=after
        bpy.data.meshes.remove(backup)
        mesh=cut.data
        bpy.data.objects.remove(cut,do_unlink=True)
        bpy.data.meshes.remove(mesh)
    # Un desconchado puede desprender una esquirla: quitarla de la piedra,
    # sin dejar pequeños objetos flotando en el aire.
    bm=bmesh.new()
    bm.from_mesh(ob.data)
    remaining=set(bm.verts)
    parts=[]
    while remaining:
        group={remaining.pop()}
        stack=list(group)
        while stack:
            v=stack.pop()
            for e in v.link_edges:
                w=e.other_vert(v)
                if w in remaining:
                    remaining.remove(w)
                    group.add(w)
                    stack.append(w)
        parts.append(group)
    parts.sort(key=len,reverse=True)
    for group in parts[1:]:
        bmesh.ops.delete(bm,geom=list(group),context='VERTS')
    bm.to_mesh(ob.data)
    bm.free()
    ob['grieta_fisica']=changed
    ob['ramas_revertidas']=reverted


def hole_fragment(coll,mat,mortar,a,b,z0,z1,thickness,projection,damage,seed,wear):
    'IA: Fragmento junto a agujero con apoyo inferior; no crees esquirlas flotantes.'
    import bmesh
    rr=random.Random(seed)
    w=(b-a)*(.45-.15*damage)
    # Borde quebrado a lo alto de la pieza; su parte inferior conserva apoyo.
    ring=[(a+.1,z0),(a+w,z0),(a+w*rr.uniform(.62,.80),z0+(z1-z0)*.28),
          (a+w*rr.uniform(.85,.97),z0+(z1-z0)*.52),(a+w*rr.uniform(.48,.65),z0+(z1-z0)*.76),(a+w*.70,z1),(a+.1,z1)]
    mirror=seed%2
    if mirror:
        ring=[(a+b-x,z) for x,z in ring]
    reach=thickness/2+projection*.72
    n=len(ring)
    verts=[(x,y,z) for y in (-reach,reach) for x,z in ring]
    faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    ob=primitives.mesh_obj('Piedra parcial de agujero %s'%seed,verts,faces,coll,mat)
    bm=bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.triangulate(bm,faces=list(bm.faces))
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bm.to_mesh(ob.data)
    bm.free()
    primitives.bevel(ob,.12)
    weather.weather_stone(ob,min(1,wear+damage*.3),seed)
    x0,x1=(b-w*.5,b-.35) if mirror else (a+.35,a+w*.5)
    support=primitives.block('Mortero de fractura %s'%seed,x0,x1,-thickness*.26,thickness*.26,z0-.85,z0+.32,coll,mortar)
    for v in support.data.vertices:
        if v.co.z>z0:
            v.co.z-=rr.uniform(0,.35)
    for v in ob.data.vertices:
        if abs(v.co.y)<reach+.01:
            v.co.x+=v.co.y/ max(1,reach)*rr.uniform(.0,.18)*damage
    return ob


def broken_stone(coll, mat, cx, cy, angle, width, depth, height, seed, wear):
    # Tres fragmentos desiguales de un mismo ladrillo: conservan caras de fábrica,
    # con superficies de fractura oblicuas y desconchados en los bordes.
    'IA: Fragmenta y rota escombros; el asentamiento definitivo corresponde a settle_rubble.'
    import bmesh
    rr=random.Random(seed)
    w=width
    d=depth
    seam=rr.uniform(-.08,.08)*w
    rings=[
        [(-.5*w+.45,-.5*d), (seam-.12*w,-.5*d), (seam+.02*w,-.12*d),
         (seam-.07*w,.12*d), (seam+.04*w,.5*d), (-.5*w+.6,.5*d),
         (-.5*w,.5*d-.6),(-.5*w,-.5*d+.5)],
        [(seam-.12*w,-.5*d),(.5*w-.5,-.5*d),(.5*w,-.5*d+.5),
         (.5*w,.06*d),(seam+.02*w,-.12*d)],
        [(seam+.02*w,-.12*d),(.5*w,.06*d),(.5*w,.5*d-.5),
         (.5*w-.6,.5*d),(seam+.04*w,.5*d),(seam-.07*w,.12*d)]
    ]
    for part,ring in enumerate(rings):
        n=len(ring)
        vs=[]
        ph=height*(1 if part==0 else rr.uniform(.55,.85))
        for layer in range(2):
            for k,(x,y) in enumerate(ring):
                # Fractura con espesor cambiante; las caras exteriores siguen reconocibles.
                shift=layer*rr.uniform(-.35,.35)
                vs.append((x+shift,y+layer*rr.uniform(-.22,.22),
                           layer*(ph+rr.uniform(-.35,.2))))
        faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]
        faces += [(k,(k+1)%n,(k+1)%n+n,k+n) for k in range(n)]
        ob=primitives.mesh_obj('Piedra caída · fractura %s.%s'%(seed,part),vs,faces,coll,mat)
        bm=bmesh.new()
        bm.from_mesh(ob.data)
        bmesh.ops.triangulate(bm,faces=list(bm.faces))
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
        bm.to_mesh(ob.data)
        bm.free()
        primitives.bevel(ob,.13)
        weather.weather_stone(ob,wear*.7,seed+part*91)
        pivot=sum((v.co for v in ob.data.vertices),Vector())/len(ob.data.vertices)
        rotations=[(.18,rr.uniform(-.28,.28),angle+rr.uniform(-.25,.25)),
                   (rr.uniform(.18,.4),rr.uniform(-.22,.22),angle+rr.uniform(-.7,.7)),
                   (rr.uniform(-.35,-.12),rr.uniform(.1,.3),angle+rr.uniform(.4,1.0))]
        rotation=Euler(rotations[part]).to_matrix()
        displacement=Vector((cx+pivot.x+(part-1)*.45,cy+pivot.y+(part-1)*.3,0))
        for v in ob.data.vertices:
            v.co=rotation@(v.co-pivot)+displacement
        bottom=min(v.co.z for v in ob.data.vertices)
        for v in ob.data.vertices:
            v.co.z+=.62-bottom
        # Apoyo asentado: una pequeña parte del fragmento queda enterrada en el suelo.
        for v in ob.data.vertices:
            if v.co.z<.95:
                v.co.z=.68


def fractured_block(name,x0,x1,y0,y1,z0,z1,coll,mat,seed):
    # Coronación rota en múltiples facetas; la fractura queda dentro de una piedra.
    'IA: Rotura cerrada de coronación; no sustituyas el aparejo escalonado por un plano continuo.'
    rr=random.Random(seed)
    nx,ny=4,3
    verts=[]
    for layer in range(2):
        for j in range(ny):
            for i in range(nx):
                x=x0+(x1-x0)*i/(nx-1)
                y=y0+(y1-y0)*j/(ny-1)
                loss=(.18+rr.random()*.25+(i/(nx-1))*.22)*(z1-z0)
                z=z0 if layer==0 else z1-loss
                verts.append((x,y,z))
    N=nx*ny
    faces=[]
    for layer in range(2):
        for j in range(ny-1):
            for i in range(nx-1):
                a=layer*N+j*nx+i
                b=a+1
                c=a+nx+1
                d=a+nx
                tris=[(a,b,c),(a,c,d)] if (i+j)%2==0 else [(a,b,d),(b,c,d)]
                faces.extend(tris if layer else [tuple(reversed(t)) for t in tris])
    ring=[0,1,2,3,7,11,10,9,8,4]
    for k,a in enumerate(ring):
        b=ring[(k+1)%len(ring)]
        faces.append((a,b,b+N,a+N))
    ob=primitives.mesh_obj(name,verts,faces,coll,mat)
    primitives.bevel(ob,.16)
    return ob


def small_rubble(coll,mat,x,y,width,seed,wear):
    # Restos angulares en el margen libre del apoyo existente, unidos por su base.
    'IA: Esquirlas de bajo coste; conserva semilla y tamaño físico.'
    rr=random.Random(seed)
    for i,(dx,dy) in enumerate(((-.30,3.25),(.04,3.45),(.35,2.7),(-.53,.8))):
        cx=x+width*dx
        cy=y+dy*(1 if y>0 else -1)
        radius=rr.uniform(.85,1.15)
        ring=[]
        for k in range(5):
            a=2*math.pi*k/5
            r=radius*rr.uniform(.72,1.12)
            ring.append((cx+r*math.cos(a),cy+r*.70*math.sin(a)))
        verts=[(a,b,.64) for a,b in ring]
        verts += [(a+rr.uniform(-.18,.18),b+rr.uniform(-.12,.12),rr.uniform(1.45,1.95)) for a,b in ring]
        verts.append((cx+radius*.25,cy,rr.uniform(2.0,2.45)))
        faces=[(4,3,2,1,0)]
        faces += [(k,(k+1)%5,(k+1)%5+5,k+5) for k in range(5)]
        faces += [(5+k,5+(k+1)%5,10) for k in range(5)]
        ob=primitives.mesh_obj('Esquirla de suelo %s.%s'%(seed,i),verts,faces,coll,mat)
        primitives.bevel(ob,.10)
        weather.weather_stone(ob,wear*.45,seed+i)


def opening_damage(ob,core,holes,x0,x1,z0,z1,amount,seed):
    'IA: Daña ladrillo y mortero adyacentes juntos; limita diagonales y restos desconectados.'
    if not holes or amount<=0:
        return
    rr=random.Random(seed)
    cx=(x0+x1)/2
    cz=(z0+z1)/2
    near=[]
    for h in holes:
        dx=max(h['x0']-x1,x0-h['x1'],0)
        dz=max(h['z0']-z1,z0-h['z1'],0)
        if dx<.8 and dz<.8:
            near.append(h)
    if not near:
        return
    h=min(near,key=lambda h:(h['x']-cx)**2+(h['z']-cz)**2)
    direction=Vector((h['x']-cx,rr.uniform(-.22,.22),h['z']-cz))
    direction.normalize()
    direction.y=rr.uniform(-.18,.18)
    # Sesgo acotado: conservar el cuerpo de la piedra y su apoyo.
    if abs(direction.x)>.8:
        direction.z=rr.choice((-1,1))*.48
    if abs(direction.z)>.8:
        direction.x=rr.choice((-1,1))*.48
    direction.normalize()
    corner=max((v.co for v in ob.data.vertices),key=lambda q:q.dot(direction)).copy()
    loss=min(x1-x0,z1-z0)*(.16+.23*amount)*rr.uniform(.65,1.0)
    point=corner-direction*loss
    if rr.random()<.35+.6*amount:
        primitives.clip_closed(ob,point,direction)
        ob['borde_agujero']=True
        primitives.clip_closed(core,point-direction*.85,direction)
    # Retirar el núcleo expuesto por zonas, conservando el interior que da apoyo.
    for v in core.data.vertices:
        t=max(0,min(1,(v.co-point).dot(direction)+1.4))
        v.co-=direction*t*rr.uniform(.1,.65)*amount
    core.data.update()
    core['mortero_erosionado']=True
    # Restos adheridos sobre la fractura: la mayor parte queda descubierta.
    if ob.get('borde_agujero') and rr.random()<.8:
        coll=ob.users_collection[0]
        mat=core.data.materials[0]
        ob.data.update()
        for i in range(rr.randint(1,3)):
            origin=point+direction*3+Vector((0,rr.uniform(-2.8,2.8),0))
            hit,position,norm,face=ob.ray_cast(origin,-direction,distance=10)
            if not hit:
                continue
            tangent=norm.cross(Vector((0,1,0))).normalized()
            bitangent=norm.cross(tangent)
            radius=rr.uniform(.55,1.25)
            verts=[]
            for k in range(6):
                angle=k*math.tau/6
                q=position-norm*.22+radius*rr.uniform(.65,1.1)*(tangent*math.cos(angle)+bitangent*math.sin(angle))
                verts.append(tuple(q))
            verts.append(tuple(position+norm*rr.uniform(.2,.55)))
            faces=[tuple(reversed(range(6)))]+[(k,(k+1)%6,6) for k in range(6)]
            primitives.mesh_obj('Mortero · resto adherido',verts,faces,coll,mat)


def apply_damage(coll,p):
    'IA: Aplica grietas después de caché; omite Borrador y conserva selección determinista por nombre.'
    if runtime.quality=='DRAFT' or p.cracks<=0:
        return
    stone=primitives.material('Piedra · neutro',(.52,.52,.52))
    for ob in list(coll.objects):
        if not ob.name.startswith(('Piedra','Pilar')) or ob.get('connection_face'):
            continue
        if 'núcleo' in ob.name or 'pie' in ob.name:
            continue
        key=zlib.crc32(ob.name.encode('utf8'))
        if ob.get('escombro') and random.Random(p.seed+key+34).random()>.2:
            continue
        if ob.name.startswith('Piedra parcial') or random.Random(p.seed+key).random()<p.cracks*.8:
            crack_stone(ob,p.cracks,(p.seed+key)%1000000,coll,stone)
