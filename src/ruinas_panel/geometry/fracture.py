"""geometry /fracture — ver docs/ARCHITECTURE.md para contratos y dependencias."""

from .. import meta
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
import numpy
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
        co=primitives.coords(ob)
        mid=(co.min(axis=0)+co.max(axis=0))/2
        middle=Vector((mid[0]-center.x,mid[1]-center.y,0))
        if middle.dot(normal)<0:
            normal=-normal
    return along,normal


def printable(widths,depths,fractions,tail):
    'IA: Aplica config.CRACK_PRINT: ancho en superficie y profundidad mínimos hasta el tramo final, que se afina de forma continua hasta la punta.'
    rule=config.CRACK_PRINT
    out_w=[]
    out_d=[]
    for w,d,s in zip(widths,depths,fractions):
        fade=1.0 if s<=1-tail else max(0.0,(1-s)/tail)
        d=max(d,rule['min_depth']*fade)
        # En la V, el ancho en la superficie hundida es 2w·(d−erosión)/(d+0,2).
        need=rule['min_surface_width']/2*(d+.2)/max(.05,d-rule['erosion'])
        out_w.append(max(w,need*fade))
        out_d.append(d)
    return out_w,out_d


def crack_paths(rr,p,amount,u0,u1,z0,z1,split=False):
    'IA: Trazos quebrados en la cara (u,z) que se afinan, una rama como mucho; split añade primero una grieta que parte la pieza de borde a borde.'
    span_u=u1-u0
    span_z=z1-z0
    mouth=(.22+.28*amount)*(1+rr.uniform(-.35,.35)*p.crack_width_var)
    deep=.5+.7*amount
    count=rr.randint(1,p.cracks_per_stone) if min(span_u,span_z)>3.5 else 1
    paths=[]
    roots=[]
    def clamp(q,through=None):
        'IA: Mantiene un punto dentro de la cara a 0,3 mm de sus bordes; through=u o z deja libre el otro eje para cruzar la pieza.'
        u=max(u0+.3,min(u1-.3,q.x)) if through!='z' else q.x
        z=max(z0+.3,min(z1-.3,q.y)) if through!='u' else q.y
        return Vector((u,z))
    def trace(start,heading,length,width,depth,wobble,through=None):
        'IA: Paseo gaussiano de rumbo desde start que termina al tocar un borde; se afina hasta la punta, o con through sale por el borde opuesto; None si queda corto.'
        # Paseo aleatorio de rumbo con incrementos de ruido blanco gaussiano (Tarbell, «Substrate»):
        # cada tramo gira un ángulo gaussiano y tiende a volver a la dirección inicial.
        steps=max(3,round(length/.8))
        step=length/steps
        angle=0.0
        points=[start]
        ts=[0.0]
        pos=start.copy()
        for k in range(1,steps+1):
            angle=max(-1.1,min(1.1,.55*angle+rr.gauss(0,.45)*wobble))
            turn=Vector((heading.x*math.cos(angle)-heading.y*math.sin(angle),heading.x*math.sin(angle)+heading.y*math.cos(angle)))
            wanted=pos+turn*step*max(.4,1+rr.gauss(0,.25))
            q=clamp(wanted,through)
            # Recortar contra el borde deja puntos repetidos o pliegues: el cortador se autointerseca.
            clipped=(q-wanted).length>1e-6
            if (q-points[-1]).length>=.2:
                points.append(q)
                ts.append(k/steps)
                pos=q
            if clipped:
                break
        if through and len(points)>=2:
            # Una partida sale siempre por el borde opuesto, aunque el paseo se haya quedado corto.
            last=points[-1]
            short=last.y>z0-.2 if through=='u' else last.x<u1+.2
            exit_point=Vector((last.x,z0-.4)) if through=='u' else Vector((u1+.4,last.y))
            if short and (exit_point-last).length>=.2:
                points.append(exit_point)
                ts.append(1.0)
        if len(points)<2:
            return None
        f=[t/ts[-1] for t in ts]
        if through:
            widths=[width*(1-.45*s)+.04 for s in f]
            depths=[depth*(.7+.3*(1-s)) for s in f]
        else:
            widths=[width*(1-s)**.7+.04 for s in f]
            depths=[depth*(.35+.65*(1-s)) for s in f]
        widths,depths=printable(widths,depths,f,1e-6 if through else config.CRACK_PRINT['tail'])
        return points,widths,depths
    if split:
        # Partida de borde a borde por el lado corto de la cara: la pieza queda agrietada por la mitad.
        tilt=rr.uniform(-.25,.25)*p.crack_angle_var
        if span_u>=span_z:
            root,heading,length,through=Vector((u0+span_u*rr.uniform(.3,.7),z1+.35)),Vector((math.sin(tilt),-math.cos(tilt))),span_z+.7,'u'
        else:
            root,heading,length,through=Vector((u0-.35,z0+span_z*rr.uniform(.3,.7))),Vector((math.cos(tilt),math.sin(tilt))),span_u+.7,'z'
        cut=trace(root,heading,length/max(.5,abs(heading.y if through=='u' else heading.x)),mouth*1.15,deep,p.crack_path_var,through)
        if cut:
            paths.append(cut)
        roots.append({'edge':'partida','point':list(root),'length':length,'angle':tilt})
        count-=1
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
        if not main:
            continue
        paths.append(main)
        roots.append({'edge':edge,'point':list(root),'length':length,'angle':angle})
        if len(main[0])>=5 and rr.random()<.3+.4*amount:
            k=rr.randint(len(main[0])//3,2*len(main[0])//3)
            turn=rr.choice((-1,1))*rr.uniform(.45,.85)
            branch=Vector((heading.x*math.cos(turn)-heading.y*math.sin(turn),heading.x*math.sin(turn)+heading.y*math.cos(turn)))
            twig=trace(main[0][k],branch,length*rr.uniform(.25,.45),main[1][k]*.75,main[2][k]*.8,p.crack_path_var*.7)
            if twig:
                paths.append(twig)
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
def crack_stone(ob, amount, seed, coll, mat, frame=None, split=False):
    'IA: Grietas quebradas que se afinan en la cara exterior del frame; split parte la pieza de borde a borde; revierte ramas que quiten más de CRACK_MAX_VOLUME_LOSS.'
    if amount<=0:
        return
    import bmesh
    rr=random.Random(seed)
    along,normal=frame or (Vector((1,0,0)),Vector((0,-1,0)))
    co=primitives.coords(ob)
    lo=co.min(axis=0).tolist()
    hi=co.max(axis=0).tolist()
    us=co@(along.x,along.y,along.z)
    ns=co@(normal.x,normal.y,normal.z)
    u0,u1,z0,z1=float(us.min()),float(us.max()),lo[2],hi[2]
    if u1-u0<1.8 or z1-z0<1.3:
        return
    paths,roots,mouth=crack_paths(rr,runtime.settings,amount,u0,u1,z0,z1,split)
    top=float(ns.max())+.2
    ob['parametros_grieta']=json.dumps({'count':len(roots),'width':mouth,'roots':roots,'paths':len(paths),'partida':split,
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
        backup=ob.data.copy()
        mod=ob.modifiers.new('Rama de grieta','BOOLEAN')
        mod.operation='DIFFERENCE'
        mod.solver=config.BOOLEAN_SOLVER
        mod.object=cut
        primitives.apply_modifier(ob,mod,cut)
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
    # Inclinación del fragmento con un solo factor: un valor aleatorio por vértice lo arrugaba
    # en cuanto el desgaste añadía vértices.
    co=primitives.coords(ob)
    inside=numpy.abs(co[:,1])<reach+.01
    co[inside,0]+=co[inside,1]/max(1,reach)*rr.uniform(.0,.18)*damage
    primitives.set_coords(ob,co)
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
        co=primitives.coords(ob)
        pivot=Vector(co.mean(axis=0).tolist())
        rotations=[(.18,rr.uniform(-.28,.28),angle+rr.uniform(-.25,.25)),
                   (rr.uniform(.18,.4),rr.uniform(-.22,.22),angle+rr.uniform(-.7,.7)),
                   (rr.uniform(-.35,-.12),rr.uniform(.1,.3),angle+rr.uniform(.4,1.0))]
        rotation=Euler(rotations[part]).to_matrix()
        displacement=Vector((cx+pivot.x+(part-1)*.45,cy+pivot.y+(part-1)*.3,0))
        co=(co-numpy.array(pivot))@numpy.array(rotation).T+numpy.array(displacement)
        co[:,2]+=.62-co[:,2].min()
        # Apoyo asentado: una pequeña parte del fragmento queda enterrada en el suelo.
        co[co[:,2]<.95,2]=.68
        primitives.set_coords(ob,co)


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
    co=primitives.coords(ob)
    corner=Vector(co[int((co@numpy.array(direction)).argmax())].tolist())
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


def crack_stress(ob,walls,openings):
    'IA: Tensión 0–1 por cercanía del centro de la pieza a huecos de su tramo y a los extremos del tramo, en coordenadas locales.'
    wall=walls.get(ob.get('wall_id','front')) or walls.get('front')
    if not wall:
        return 0.0
    co=primitives.coords(ob)
    mid=(co.min(axis=0)+co.max(axis=0))/2
    o,a=wall['origin'],wall['axis']
    u=float((mid[0]-o[0])*a[0]+(mid[1]-o[1])*a[1])
    z=float(mid[2])
    gap=min(abs(u-wall['start']),abs(u-wall['end']))
    for wid,x0,x1,z0,z1 in openings:
        if wid==wall['id']:
            gap=min(gap,math.hypot(max(x0-u,0,u-x1),max(z0-z,0,z-z1)))
    stress=max(0.0,1-gap/config.CRACK_STRESS['reach'])
    if '· sillar' in ob.name:
        stress=max(stress,config.CRACK_STRESS['pillar'])
    return stress


def apply_damage(coll,p):
    'IA: Aplica grietas tras la caché, más y partidas cerca de huecos y extremos; omite Borrador; la selección depende de piece_key, no del nombre visible.'
    if runtime.quality not in config.DAMAGE_QUALITIES or p.cracks<=0:
        return
    stone=primitives.material('Piedra · neutro',(.52,.52,.52))
    walls={w['id']:w for w in meta.get(bpy.context.scene,'paredes_generadas',[])}
    center=Vector((0,p.building_depth/2,0))
    scene=bpy.context.scene
    door=meta.get(scene,'puerta_generada')
    openings=[('front',door['left'],door['right'],0,door['top'])] if door else []
    openings+=[(w['wall'],w['x0'],w['x1'],w['z0'],w['z1']) for w in meta.get(scene,'ventanas_generadas',[])]
    openings+=[(h.get('wall','front'),h['x0'],h['x1'],h['z0'],h['z1']) for h in meta.get(scene,'huecos_generados',[])]
    tuning=config.CRACK_STRESS
    for ob in list(coll.objects):
        if not ob.name.startswith(('Piedra','Pilar')) or ob.get('protected_sill'):
            continue
        # Los fragmentos de agujero ya son piedra rota y miden ~3,5 mm: las ranuras los dejarían como una hoja rasgada.
        if 'núcleo' in ob.name or 'pie' in ob.name or ob.name.startswith('Piedra parcial'):
            continue
        key=zlib.crc32(primitives.piece_key(ob).encode('utf8'))
        if ob.get('escombro') and random.Random(p.seed+key+34).random()>.2:
            continue
        stress=0.0 if ob.get('escombro') else crack_stress(ob,walls,openings)
        chance=min(.95,p.cracks*(tuning['base']+tuning['gain']*stress))
        if random.Random(p.seed+key).random()<chance:
            split=not ob.get('escombro') and random.Random(p.seed+key+71).random()<p.cracks*(tuning['split']+tuning['split_gain']*stress)
            crack_stone(ob,p.cracks,(p.seed+key)%1000000,coll,stone,crack_frame(ob,walls,center),split)
