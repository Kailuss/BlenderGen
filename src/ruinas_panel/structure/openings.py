"""structure /openings — ver docs/ARCHITECTURE.md para contratos y dependencias."""

from .. import config
from ..geometry import primitives
from ..geometry import timber
from ..services import profiling
from mathutils import Vector
import bpy
import json


def wall_point(w,x,y,z):
    'IA: Transformación local a mundo de un tramo; empareja cambios con wall_local.'
    a=w['axis']
    o=w['origin']
    return (o[0]+a[0]*x-a[1]*y,o[1]+a[1]*x+a[0]*y,z)


def wall_local(w,q):
    'IA: Inversa rígida de wall_point; no introduzcas escalas implícitas.'
    a=w['axis']
    o=w['origin']
    dx=q[0]-o[0]
    dy=q[1]-o[1]
    return (dx*a[0]+dy*a[1],-dx*a[1]+dy*a[0],q[2])


def carve_rectangle(coll,w,x0,x1,z0,z1,T,name):
    'Booleanos locales solo sobre piezas que intersectan el hueco.\n\nIA: Recorta solo piezas solapadas con BOOLEAN_SOLVER; elimina piezas contenidas; restaura la pieza si el booleano quita más que el cruce con el hueco.'
    verts=[(x0,-T,z0),(x1,-T,z0),(x1,T,z0),(x0,T,z0),(x0,-T,z1),(x1,-T,z1),(x1,T,z1),(x0,T,z1)]
    cutter=primitives.mesh_obj('Cortador · '+name,verts,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],coll,primitives.material('Temporal',(.5,.5,.5)))
    # Box sin modificadores pendientes; transformación rígida al plano de la pared.
    for v in cutter.data.vertices:
        v.co=wall_point(w,*v.co)
    cutter.data.update()
    bpy.context.view_layer.update()
    changed=[]
    for ob in list(coll.objects):
        if ob==cutter or ob.get('wall_id','front')!=w['id'] or ob.get('escombro'):
            continue
        if not ob.name.startswith(('Piedra','Mortero','Núcleo')):
            continue
        coords=[wall_local(w,v.co) for v in ob.data.vertices]
        if not coords:
            continue
        if max(q[0] for q in coords)<=x0 or min(q[0] for q in coords)>=x1 or max(q[2] for q in coords)<=z0 or min(q[2] for q in coords)>=z1:
            continue
        if max(q[1] for q in coords)<-T or min(q[1] for q in coords)>T:
            continue
        # Las piezas totalmente dentro del hueco se eliminan directamente.
        # Evita booleanos degenerados y reduce el trabajo de ventanas grandes.
        if all(x0<=q[0]<=x1 and z0<=q[2]<=z1 and -T<=q[1]<=T for q in coords):
            mesh=ob.data
            bpy.data.objects.remove(ob,do_unlink=True)
            if mesh.users==0:
                bpy.data.meshes.remove(mesh)
            continue
        import bmesh
        bm=bmesh.new()
        bm.from_mesh(ob.data)
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
        bm.to_mesh(ob.data)
        bm.free()
        ob.data.update()
        # El recorte no puede quitar más que el cruce de la caja de la pieza con el cortador.
        reach=[max(0,min(max(q[i] for q in coords),hi)-max(min(q[i] for q in coords),lo)) for i,(lo,hi) in enumerate(((x0,x1),(-T,T),(z0,z1)))]
        limit=reach[0]*reach[1]*reach[2]*1.05+.5
        before=primitives.mesh_volume(ob.data)
        backup=ob.data.copy()
        mod=ob.modifiers.new('Hueco arquitectónico','BOOLEAN')
        mod.operation='DIFFERENCE'
        mod.solver=config.BOOLEAN_SOLVER
        mod.object=cutter
        primitives.apply_modifier(ob,mod,cutter)
        if ob.data.vertices and before-primitives.mesh_volume(ob.data)>limit:
            # Booleano fallido: devolvió menos pieza de la que el hueco puede quitar. Se conserva sin recortar.
            failed=ob.data
            ob.data=backup.copy()
            bpy.data.meshes.remove(failed)
            ob['hueco_revertido']=True
        bpy.data.meshes.remove(backup)
        if not ob.data.vertices:
            mesh=ob.data
            bpy.data.objects.remove(ob,do_unlink=True)
            if mesh.users==0:
                bpy.data.meshes.remove(mesh)
        else:
            changed.append(ob)
    mesh=cutter.data
    bpy.data.objects.remove(cutter,do_unlink=True)
    bpy.data.meshes.remove(mesh)
    return changed


def wall_tree(coll,w):
    'IA: BVH de mampostería del tramo para apoyos; excluye escombros y otros muros.'
    from mathutils.bvhtree import BVHTree
    verts=[]
    faces=[]
    for ob in coll.objects:
        if ob.get('wall_id','front')==w['id'] and not ob.get('escombro') and ob.name.startswith(('Piedra','Mortero')):
            off=len(verts)
            verts.extend(tuple(v.co) for v in ob.data.vertices)
            faces.extend(tuple(off+i for i in f.vertices) for f in ob.data.polygons)
    return BVHTree.FromPolygons(verts,faces)


def wall_hit(tree,w,p,x,z):
    'IA: Consulta apoyo local atravesando el grosor; no cuentes una pared opuesta como apoyo.'
    origin=Vector(wall_point(w,x,-p.thickness-6,z))
    direction=Vector((-w['axis'][1],w['axis'][0],0))
    return tree.ray_cast(origin,direction,2*p.thickness+12)[0] is not None


def window_timber(coll,wood,w,name,a,b,width,depth,seed):
    'IA: Crea madera local y la transforma al tramo; evita intercambiar anchura y profundidad.'
    ob=timber.timber_beam(coll,wood,name,a,b,width,depth,seed)
    for v in ob.data.vertices:
        v.co=wall_point(w,*v.co)
    return ob


@profiling.timed('aberturas_y_vigas')
def architectural_openings(coll,p,walls,door,edges):
    'IA: Distribuye huecos con jambas/dinteles apoyados; aloja vigas quitando ladrillos antes de añadir madera.'
    windows=[]
    beams=[]
    wood=primitives.material('Madera · envejecida',(.29,.21,.13))
    iron=primitives.material('Hierro · forjado',(.10,.105,.11))
    for w in walls:
        if not p.windows_enabled:
            break
        ww=12 if p.build_type=='PARTITION' else 15
        wh=16
        usable=(w['start']+4,w['end']-4)
        # Reservar columnas y puerta en la fachada.
        centers=json.loads(bpy.context.scene['pilares_generados']) if w['id']=='front' else []
        floors=2 if p.height_type=='TWO' else 1
        made=0
        tree=wall_tree(coll,w)
        for floor in range(floors):
            z0=2+floor*50+14
            z1=z0+wh
            if z1+5>w['height']:
                continue
            attempts=9+p.windows_per_wall*4
            candidates=[usable[0]+ww/2+i*(usable[1]-usable[0]-ww)/(attempts-1) for i in range(attempts)]
            for cx in candidates:
                if made>=p.windows_per_wall:
                    break
                x0=cx-ww/2
                x1=cx+ww/2
                if x1>usable[1]+.01 or x0<usable[0]-.01:
                    continue
                if any(x0<c['x_mm']+c['width_mm']/2+3 and x1>c['x_mm']-c['width_mm']/2-3 for c in centers):
                    continue
                if w['id']=='front' and door and x0<door['right']+4 and x1>door['left']-4 and z0<door['top']+6:
                    continue
                if any(h['wall']==w['id'] and abs(cx-h['x'])<ww+6 and abs(z0-h['z0'])<wh+5 for h in windows):
                    continue
                # No crear marcos flotando sobre zonas derrumbadas: requieren jambas y dintel.
                supported=True
                for x,z in ((x0-1,z0+wh/2),(x1+1,z0+wh/2),(cx,z1+1),(cx,z0-1)):
                    origin=Vector(wall_point(w,x,-p.thickness-6,z))
                    direction=Vector((-w['axis'][1],w['axis'][0],0))
                    if tree.ray_cast(origin,direction,2*p.thickness+12)[0] is None:
                        supported=False
                        break
                if not supported:
                    continue
                carve_rectangle(coll,w,x0,x1,z0,z1,p.thickness+5,'Ventana')
                yy=-p.thickness/2-.25
                for x in (x0+.5,x1-.5):
                    window_timber(coll,wood,w,'Madera · jamba ventana',(x,yy,z0-.3),(x,yy,z1+.3),2,3.2,p.seed+made+141)
                for z in (z0+.45,z1-.45):
                    window_timber(coll,wood,w,'Madera · ventana travesaño',(x0-.2,yy,z),(x1+.2,yy,z),2,3.2,p.seed+made+181)
                windows.append({'wall':w['id'],'x':cx,'x0':x0,'x1':x1,'z0':z0,'z1':z1})
                made+=1
    if p.floor_beams and p.height_type=='TWO':
        z=49.5
        size=4.5
        targets=[w for w in walls if w['id']=='front'] if p.layout_mode=='ROOM' else walls
        for w in targets:
            support_tree=wall_tree(coll,w)
            count=max(1,int((w['end']-w['start'])/24))
            span=(w['end']-w['start'])/(count+1)
            for i in range(count):
                x=w['start']+(i+1)*span
                if not all(wall_hit(support_tree,w,p,sx,z-2.7) for sx in (x-2.8,x,x+2.8)):
                    continue
                if any(h['wall']==w['id'] and h['x0']-3<x<h['x1']+3 and h['z0']<z+size/2 and h['z1']>z-size/2 for h in windows):
                    continue
                # Cada viga ocupa una caja propia en la hilada de apoyo.
                rear=None
                if p.layout_mode=='ROOM':
                    rear=next(q for q in walls if q['id']=='back')
                    if not rear['start']+3<x<rear['end']-3:
                        continue
                carve_rectangle(coll,w,x-2.5,x+2.5,z-2,z+size/2,p.thickness+6,'Alojamiento de viga')
                length=p.thickness/2+4
                if p.layout_mode=='ROOM':
                    carve_rectangle(coll,rear,x-2.5,x+2.5,z-2,z+size/2,p.thickness+6,'Apoyo trasero de viga')
                    end=(x,rear['origin'][1]+length,z)
                else:
                    end=wall_point(w,x,length,z)
                ob=timber.timber_beam(coll,wood,'Madera · viga de planta',wall_point(w,x,-length,z),end,4.2,size+.2,p.seed+461+i)
                beams.append({'wall':w['id'],'x':x,'z':z,'span':list(end)})
                # Clavos en una abrazadera de frente; unidos al extremo de la viga.
                if w['id']=='front':
                    timber.metal_pin(coll,iron,'Hierro · clavo de viga',x,-length-.1,z,.4,.5)
    bpy.context.scene['ventanas_generadas']=json.dumps(windows)
    bpy.context.scene['vigas_generadas']=json.dumps(beams)
