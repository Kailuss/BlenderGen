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


def crack_frame(ob,walls,center):
    'IA: Ejes horizontales (tramo, normal exterior) de la cara que se agrieta; escombros usan −Y y cada tramo su cara exterior.'
    if ob.get('escombro'):
        return Vector((1,0,0)),Vector((0,-1,0))
    wall=walls.get(ob.get('wall_id','front'))
    axis=wall['axis'] if wall else (1,0)
    along=Vector((axis[0],axis[1],0))
    normal=Vector((axis[1],-axis[0],0))
    if len(walls)>1:
        xs=[v.co.x for v in ob.data.vertices]
        ys=[v.co.y for v in ob.data.vertices]
        middle=Vector(((min(xs)+max(xs))/2-center.x,(min(ys)+max(ys))/2-center.y,0))
        if middle.dot(normal)<0:
            normal=-normal
    return along,normal


def crack_paths(rr,p,amount,u0,u1,z0,z1):
    'IA: Trazos quebrados en el plano de la cara (u,z) con ancho y profundidad decrecientes; como mucho una rama por grieta.'
    span_u=u1-u0
    span_z=z1-z0
    mouth=(.22+.28*amount)*(1+rr.uniform(-.35,.35)*p.crack_width_var)
    deep=.5+.7*amount
    count=rr.randint(1,p.cracks_per_stone) if min(span_u,span_z)>3.5 else 1
    paths=[]
    roots=[]
    def clamp(q):
        'IA: Mantiene un punto del trazo dentro de la cara, a 0,3 mm de sus bordes.'
        return Vector((max(u0+.3,min(u1-.3,q.x)),max(z0+.3,min(z1-.3,q.y))))
    def trace(start,heading,length,width,depth,wobble):
        'IA: Polilínea en zigzag desde start; devuelve puntos, semianchos y profundidades que se afinan hasta la punta.'
        steps=max(3,round(length/.8))
        across=Vector((-heading.y,heading.x))
        phase=rr.uniform(0,math.tau)
        points=[start]
        sign=rr.choice((-1,1))
        for k in range(1,steps+1):
            t=min(1,(k+(rr.uniform(-.3,.3) if k<steps else 0))/steps)
            sign=-sign if rr.random()<.7 else sign
            zig=sign*rr.uniform(.08,.3)*wobble*(1-.5*t)
            drift=.25*wobble*math.sin(t*math.pi+phase)
            points.append(clamp(start+heading*length*t+across*(zig+drift)))
        widths=[width*(1-k/steps)**.7+.04 for k in range(steps+1)]
        depths=[depth*(.35+.65*(1-k/steps)) for k in range(steps+1)]
        return points,widths,depths
    for root_index in range(count):
        edge=rr.randrange(4)
        s=(root_index+rr.uniform(.3,.7))/count
        if edge==0:
            root,heading,span=Vector((u0+span_u*s,z1+.35)),Vector((0,-1)),span_z
        elif edge==1:
            root,heading,span=Vector((u0+span_u*s,z0-.35)),Vector((0,1)),span_z
        elif edge==2:
            root,heading,span=Vector((u0-.35,z0+span_z*s)),Vector((1,0)),span_u
        else:
            root,heading,span=Vector((u1+.35,z0+span_z*s)),Vector((-1,0)),span_u
        angle=rr.uniform(-.55,.55)*p.crack_angle_var
        heading=Vector((heading.x*math.cos(angle)-heading.y*math.sin(angle),heading.x*math.sin(angle)+heading.y*math.cos(angle)))
        length=span*rr.uniform(.55,.85)*(1+rr.uniform(-.35,.2)*p.crack_length_var)
        main=trace(root,heading,length,mouth,deep,p.crack_path_var)
        paths.append(main)
        roots.append({'edge':edge,'point':list(root),'length':length,'angle':angle})
        if len(main[0])>=5 and rr.random()<.3+.4*amount:
            k=rr.randint(len(main[0])//3,2*len(main[0])//3)
            turn=rr.choice((-1,1))*rr.uniform(.45,.85)
            branch=Vector((heading.x*math.cos(turn)-heading.y*math.sin(turn),heading.x*math.sin(turn)+heading.y*math.cos(turn)))
            paths.append(trace(main[0][k],branch,length*rr.uniform(.25,.45),main[1][k]*.75,main[2][k]*.8,p.crack_path_var*.7))
    return paths,roots,mouth


def crack_cutter(path,along,normal,top):
    'IA: Cortador cerrado con sección en V bajo la cara y punta final; devuelve vértices y caras en coordenadas de mundo.'
    points,widths,depths=path
    def world(u,z,n):
        'IA: Pasa coordenadas de la cara (u a lo largo, z altura, n hacia fuera) a mundo.'
        q=along*u+normal*n
        return (q.x,q.y,z)
    verts=[]
    count=len(points)
    for i,q in enumerate(points):
        before=(q-points[i-1]).normalized() if i>0 else None
        after=(points[i+1]-q).normalized() if i<count-1 else None
        normals=[Vector((-t.y,t.x)) for t in (before,after) if t is not None]
        side=sum(normals,Vector((0,0))).normalized()
        side=side/max(.6,side.dot(normals[0]))
        for delta,n in ((-widths[i],top),(widths[i],top),(0,top-.2-depths[i])):
            point=q+side*delta
            verts.append(world(point.x,point.y,n))
    tip=points[-1]+(points[-1]-points[-2]).normalized()*.3
    verts.append(world(tip.x,tip.y,top-.2-depths[-1]*.5))
    last=3*(count-1)
    faces=[(2,1,0)]
    for i in range(count-1):
        for j in range(3):
            faces.append((i*3+j,i*3+(j+1)%3,(i+1)*3+(j+1)%3,(i+1)*3+j))
    for j in range(3):
        faces.append((last+j,last+(j+1)%3,3*count))
    return verts,faces


@profiling.timed("grietas")
def crack_stone(ob, amount, seed, coll, mat, frame=None):
    'IA: Grietas quebradas que se afinan, talladas en la cara exterior del frame; revierte ramas que quiten más de CRACK_MAX_VOLUME_LOSS.'
    if amount<=0:
        return
    import bmesh
    rr=random.Random(seed)
    along,normal=frame or (Vector((1,0,0)),Vector((0,-1,0)))
    lo=[min(v.co[i] for v in ob.data.vertices) for i in range(3)]
    hi=[max(v.co[i] for v in ob.data.vertices) for i in range(3)]
    us=[v.co.dot(along) for v in ob.data.vertices]
    ns=[v.co.dot(normal) for v in ob.data.vertices]
    u0,u1,z0,z1=min(us),max(us),lo[2],hi[2]
    if u1-u0<1.8 or z1-z0<1.3:
        return
    paths,roots,mouth=crack_paths(rr,runtime.settings,amount,u0,u1,z0,z1)
    top=max(ns)+.2
    ob['parametros_grieta']=json.dumps({'count':len(roots),'width':mouth,'roots':roots,'paths':len(paths),
                                        'frame':[list(along),list(normal)],'bounds':[lo,hi]})
    changed=False
    reverted=0
    volume=primitives.mesh_volume(ob.data)
    for path in paths:
        verts,faces=crack_cutter(path,along,normal,top)
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
    'IA: Aplica grietas después de caché en la cara exterior de cada tramo; omite Borrador y conserva selección determinista por nombre.'
    if runtime.quality=='DRAFT' or p.cracks<=0:
        return
    stone=primitives.material('Piedra · neutro',(.52,.52,.52))
    walls={w['id']:w for w in json.loads(bpy.context.scene.get('paredes_generadas','[]'))}
    center=Vector((0,p.building_depth/2,0))
    for ob in list(coll.objects):
        if not ob.name.startswith(('Piedra','Pilar')) or ob.get('connection_face'):
            continue
        if 'núcleo' in ob.name or 'pie' in ob.name:
            continue
        key=zlib.crc32(ob.name.encode('utf8'))
        if ob.get('escombro') and random.Random(p.seed+key+34).random()>.2:
            continue
        if ob.name.startswith('Piedra parcial') or random.Random(p.seed+key).random()<p.cracks*.8:
            crack_stone(ob,p.cracks,(p.seed+key)%1000000,coll,stone,crack_frame(ob,walls,center))
