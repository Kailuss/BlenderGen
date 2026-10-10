"""structure /openings — ver docs/ARCHITECTURE.md para contratos y dependencias."""

from .. import meta
from .. import config
from ..geometry import primitives
from ..geometry import timber
from ..services import profiling
from . import layout
from mathutils import Vector
import bpy
import numpy


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


def sliver(ob,w,before):
    'IA: True si tras recortar queda una lámina: menos de 2,5 mm a lo largo del tramo, menos de 1,5 mm de alto o menos del 20 % del volumen.'
    world=primitives.coords(ob)
    a,o=w['axis'],w['origin']
    along=(world[:,0]-o[0])*a[0]+(world[:,1]-o[1])*a[1]
    tall=world[:,2].max()-world[:,2].min()
    return along.max()-along.min()<2.5 or tall<1.5 or primitives.mesh_volume(ob.data)<.2*before


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
        if ob==cutter or ob.get('wall_id','front')!=w['id'] or ob.get('escombro') or ob.get('protected_sill'):
            continue
        if not ob.name.startswith(('Piedra','Mortero','Núcleo')):
            continue
        world=primitives.coords(ob)
        if not len(world):
            continue
        a,o=w['axis'],w['origin']
        dx=world[:,0]-o[0]
        dy=world[:,1]-o[1]
        # Misma transformación que wall_local, para todos los vértices a la vez.
        local=numpy.stack((dx*a[0]+dy*a[1],-dx*a[1]+dy*a[0],world[:,2]),axis=1)
        if local[:,0].max()<=x0 or local[:,0].min()>=x1 or local[:,2].max()<=z0 or local[:,2].min()>=z1:
            continue
        if local[:,1].max()<-T or local[:,1].min()>T:
            continue
        # Las piezas totalmente dentro del hueco se eliminan directamente.
        # Evita booleanos degenerados y reduce el trabajo de ventanas grandes.
        if ((x0<=local[:,0])&(local[:,0]<=x1)&(z0<=local[:,2])&(local[:,2]<=z1)&(-T<=local[:,1])&(local[:,1]<=T)).all():
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
        reach=[max(0,min(local[:,i].max(),hi)-max(local[:,i].min(),lo)) for i,(lo,hi) in enumerate(((x0,x1),(-T,T),(z0,z1)))]
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
        if ob.data.vertices and not ob.get('hueco_revertido') and sliver(ob,w,before):
            # Una lámina junto al hueco es frágil al imprimir y se ve arrugada: se elimina como las piezas contenidas.
            primitives.remove_objects([ob])
            continue
        if not ob.data.vertices:
            mesh=ob.data
            bpy.data.objects.remove(ob,do_unlink=True)
            if mesh.users==0:
                bpy.data.meshes.remove(mesh)
        else:
            ob['ruin_box']=False
            ob['architectural_cut']=True
            changed.append(ob)
    mesh=cutter.data
    bpy.data.objects.remove(cutter,do_unlink=True)
    bpy.data.meshes.remove(mesh)
    return changed


def wall_tree(coll,w):
    'IA: BVH de mampostería del tramo para apoyos; excluye escombros y otros muros.'
    from mathutils.bvhtree import BVHTree
    verts=[]
    tris=[]
    offset=0
    for ob in coll.objects:
        is_wall=ob.get('wall_id','front')==w['id'] and ob.name.startswith(('Piedra','Mortero'))
        is_pillar=False
        if ob.name.startswith('Pilar'):
            co=primitives.coords(ob)
            local=numpy.array([wall_local(w,v) for v in co])
            # Solape real del sillar: el margen fijo de 12 mm excluía esquinas de Muralla.
            is_pillar=local[:,0].max()>=w['start']-2 and local[:,0].min()<=w['end']+2 and local[:,1].min()<=2 and local[:,1].max()>=-2
        if (is_wall or is_pillar) and not ob.get('escombro'):
            me=ob.data
            me.calc_loop_triangles()
            ids=numpy.empty(len(me.loop_triangles)*3,dtype=numpy.int32)
            me.loop_triangles.foreach_get('vertices',ids)
            verts.append(primitives.coords(ob))
            tris.append(ids.reshape(-1,3)+offset)
            offset+=len(me.vertices)
    if not verts:
        return BVHTree.FromPolygons([],[])
    return BVHTree.FromPolygons(numpy.concatenate(verts).tolist(),numpy.concatenate(tris).tolist())


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
    ob['wall_id']=w['id']
    ob['window_frame']=True
    return ob


@profiling.timed('aberturas_y_vigas')
def architectural_openings(coll,p,walls,door,edges):
    'IA: Distribuye huecos con jambas/dinteles apoyados; aloja vigas quitando ladrillos antes de añadir madera.'
    windows=[]
    from . import placement,floor_plan
    stair=placement.stair_reservation(p,walls)
    from ..geometry import balconies
    beams=[]
    wood=primitives.material('Madera · envejecida',(.29,.21,.13))
    iron=primitives.material('Hierro · forjado',(.10,.105,.11))
    for w in walls:
        if not p.windows_enabled:
            break
        ww=p.window_width
        margin=8 if p.balconies else 4
        usable=(w['start']+margin,w['end']-margin)
        # Reservar columnas y puerta en la fachada.
        centers=meta.get(bpy.context.scene,'pilares_generados',[]) if w['id']=='front' else []
        floors=2 if p.height_type=='TWO' else 1
        made=0
        tree=wall_tree(coll,w)
        for floor in (reversed(range(floors)) if p.balconies else range(floors)):
            has_balcony=p.balconies and floor>0
            wh=p.window_height+(14 if has_balcony else 0)
            z0=(layout.upper_floor(p) if floor else 2)+(0 if has_balcony else 16)
            z1=z0+wh
            if z1+5>w['height']:
                continue
            attempts=9+p.windows_per_wall*4
            candidates=[usable[0]+ww/2+i*(usable[1]-usable[0]-ww)/(attempts-1) for i in range(attempts)]
            candidates+= [usable[0]+(usable[1]-usable[0])*(i+1)/(p.windows_per_wall+1) for i in range(p.windows_per_wall)]
            feasible=[]
            for cx in candidates:
                if made>=p.windows_per_wall:
                    break
                x0=cx-ww/2
                x1=cx+ww/2
                if placement.blocks_stair(w,x0,x1,z0,stair,p):continue
                if floor==0 and floor_plan.window_blocked(meta.get(bpy.context.scene,'plano_interior',{}),w['id'],x0,x1):continue
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
                feasible.append(cx)
            selected=layout.spread_positions(feasible,p.windows_per_wall-made,*usable,ww+(12 if has_balcony else 6))
            for cx in selected:
                x0=cx-ww/2;x1=cx+ww/2
                carve_rectangle(coll,w,x0,x1,z0,z1,p.thickness+5,'Ventana')
                # El eje local +Y apunta al exterior solo en izquierda y trasera.
                direction=(1 if w['id'] in ('left','back') else -1)*(1 if p.window_facing=='OUTSIDE' else -1)
                # Cara posterior del marco a 0,35 mm dentro de la cara terminada de la piedra.
                yy=direction*(p.thickness/2+p.projection*.75+3.2/2-.35)
                # Travesaño exterior sobre la loseta; el reborde interior ocupa otro plano.
                for x in (x0+.5,x1-.5):
                    window_timber(coll,wood,w,'Madera · jamba ventana',(x,yy,z0+2.1),(x,yy,z1-1.45),2,3.2,p.seed+made+141)
                for z in (z0+2.1,z1-.45):
                    window_timber(coll,wood,w,'Madera · ventana travesaño',(x0-.2,yy,z),(x1+.2,yy,z),2,3.2,p.seed+made+181)
                balconies.sill(coll,p,w,x0,x1,z0)
                balconies.window_iron(coll,p,w,x0,x1,z0,z1,yy)
                if has_balcony:
                    balconies.balcony(coll,p,w,x0,x1,z0,p.seed+made+len(w['id'])*337)
                windows.append({'wall':w['id'],'x':cx,'x0':x0,'x1':x1,'z0':z0,'z1':z1,'frame_y':yy,'balcony':has_balcony})
                made+=1
    if p.floor_beams and p.height_type=='TWO':
        z=layout.upper_floor(p)-(3.6 if p.layout_mode=='ROOM' else 2.5)
        size=4.5
        targets=[w for w in walls if w['id']=='front'] if p.layout_mode=='ROOM' else walls
        # Congelar apoyos antes del primer alojamiento: un recorte no cambia la decisión del siguiente.
        support_trees={w['id']:wall_tree(coll,w) for w in walls}
        for w in targets:
            support_tree=support_trees[w['id']]
            count=max(1,int((w['end']-w['start'])/24))
            span=(w['end']-w['start'])/(count+1)
            for i in range(count):
                x=w['start']+(i+1)*span
                if sum(wall_hit(support_tree,w,p,sx,z-2.7) for sx in (x-1.5,x,x+1.5))<2:
                    continue
                if any(h['wall']==w['id'] and h['x0']-3<x<h['x1']+3 and h['z0']<z+size/2 and h['z1']>z-size/2 for h in windows):
                    continue
                # Cada viga ocupa una caja propia en la hilada de apoyo.
                rear=None
                if p.layout_mode=='ROOM':
                    rear=next(q for q in walls if q['id']=='back')
                    if not rear['start']+3<x<rear['end']-3:
                        continue
                    if any(h['wall']=='back' and h['x0']-3<x<h['x1']+3 and h['z0']-1<z+size/2 and h['z1']+1>z-size/2 for h in windows):
                        continue
                    if sum(wall_hit(support_trees['back'],rear,p,sx,z-2.7) for sx in (x-1.5,x,x+1.5))<2:
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
    meta.put(bpy.context.scene,'ventanas_generadas',windows)
    meta.put(bpy.context.scene,'vigas_generadas',beams)
