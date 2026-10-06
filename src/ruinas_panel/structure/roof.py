"""Cubierta cóncava: entramado de hastial, pares curvos y tejas de media caña."""
import math
import random
import bmesh
from .. import meta
from ..geometry import primitives,timber,plaster
from . import openings,spatial,roof_damage,roof_accessories


def envelope(coll,p,walls):
    'IA: Mide mampostería exterior real, incluidos pilares; excluye escombros, peana y accesorios. Añade vuelo de 4 mm.'
    lo=[-p.length/2,-p.thickness/2];hi=[p.length/2,walls['back']['origin'][1]+p.thickness/2]
    for ob in coll.objects:
        key=primitives.piece_key(ob)
        if not key.startswith(('Piedra','Pilar')) or ob.get('escombro') or ob.get('stair') or ob.get('protected_sill') or 'balcón' in key or 'pie' in key:continue
        co=primitives.coords(ob)
        if not len(co):continue
        for axis in (0,1):lo[axis]=min(lo[axis],float(co[:,axis].min()));hi[axis]=max(hi[axis],float(co[:,axis].max()))
    return {'walls':[lo[0],hi[0],lo[1],hi[1]],'cover':[lo[0]-4,hi[0]+4,lo[1]-4,hi[1]+4]}


def roof_segments(a,b,fixed,patches,axis,chimney=None,clearance=2):
    'IA: Conserva el daño elíptico, pero reserva el paso rectangular de chimenea con holgura para la sección de las vigas.'
    ranges=roof_damage.segments(a,b,fixed,patches,axis)
    if not chimney:return ranges
    center=chimney[axis];cross=chimney['x' if axis=='y' else 'y'];radius=chimney['radius']+clearance
    if abs(fixed-cross)>=radius:return ranges
    result=[]
    for lo,hi in ranges:
        if hi<=center-radius or lo>=center+radius:result.append((lo,hi));continue
        if center-radius-lo>2:result.append((lo,center-radius))
        if hi-center-radius>2:result.append((center+radius,hi))
    return result


def gable(coll,p,wood,xa,xb,xm,y,z,rise,index,chimney=None):
    'IA: Hastial de cal rugosa con relieve real de .28 mm, retranqueado tras entramado; contorno de pares y reserva de chimenea cerrados sin booleanos.'
    mat=primitives.material('Revoco · cal',(.66,.60,.47))
    # Paño retranqueado respecto a la cara de madera, siguiendo exactamente su curva.
    left,right=xa+4,xb-4
    outward=-1 if index==0 else 1
    thickness=max(3.2,min(5,p.thickness*.6))
    outer=y-outward*.45;inner=outer-outward*thickness
    # Si el conducto toca cualquier profundidad del relleno, se reserva el tramo
    # completo; las dos piezas resultantes siguen teniendo tapas y espesor real.
    cuts=chimney if chimney and min(outer,inner)-chimney['radius']<chimney['y']<max(outer,inner)+chimney['radius'] else None
    cut_y=chimney['y'] if cuts else y
    verts=[];faces=[]
    for lo,hi in roof_segments(left,right,cut_y,(),'x',cuts,.35):
        count=max(2,math.ceil((hi-lo)/4))
        samples=sorted({lo,hi,*([xm] if lo<xm<hi else []),*[lo+(hi-lo)*i/count for i in range(1,count)]})
        tops=[]
        for x in samples:
            t=(x-xa)/(xm-xa) if x<=xm else (xb-x)/(xb-xm)
            tops.append(spatial.roof_height(t,z,rise,p.roof_curve)-1.85)
        vv,ff=plaster.panel(samples,p.height-.3,tops,min(outer,inner),max(outer,inner),p.seed+9400+index)
        start=len(verts);verts.extend(vv);faces.extend(tuple(start+i for i in face) for face in ff)
    ob=primitives.mesh_obj('Revoco · hastial %s'%index,verts,faces,coll,mat)
    bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
    ob['roof_gable']=True;ob['gable_depth_mm']=thickness
    # La cercha existente proporciona solera, pendolón y pares. Los rellenos quedan
    # detrás de su cara exterior; montantes y tornapuntas tienen apoyos reales.
    spans=max(2,math.ceil((right-left)/18));xs=[left+(right-left)*i/spans for i in range(spans+1)]
    base=p.height+2.0
    for i,x in enumerate(xs[1:-1],1):
        if abs(x-xm)<3:continue
        if chimney and abs(x-chimney['x'])<chimney['radius']+1.5 and abs(y-chimney['y'])<chimney['radius']+1.5:continue
        t=(x-xa)/(xm-xa) if x<=xm else (xb-x)/(xb-xm)
        top=spatial.roof_height(t,z,rise,p.roof_curve)-1.3
        if top-base<3:continue
        beam=timber.timber_beam(coll,wood,'Madera · montante hastial',(x,y,base),(x,y,top),2.5,2.5,p.seed+9510+index*41+i,coarse=True)
        beam['roof_timber']=True;beam['roof_gable_frame']=True
    for i,(a,b) in enumerate(zip(xs,xs[1:])):
        low,high=(a,b) if (a+b)/2<xm else (b,a)
        t=(high-xa)/(xm-xa) if high<=xm else (xb-high)/(xb-xm)
        top=min(base+18,spatial.roof_height(t,z,rise,p.roof_curve)-3.5)
        if top-base<5:continue
        for lo,hi in roof_segments(low,high,y,(),'x',chimney):
            za=base+(top-base)*(lo-low)/(high-low);zb=base+(top-base)*(hi-low)/(high-low)
            beam=timber.timber_beam(coll,wood,'Madera · riostra hastial',(lo,y,za),(hi,y,zb),1.9,2.4,p.seed+9710+index*41+i,coarse=True)
            beam['roof_timber']=True;beam['roof_gable_frame']=True
    return ob


def curved_tile(verts,faces,start,end,width,height,thickness=.58,taper=.90,chip=0):
    'IA: Media caña cerrada de ocho gajos; sección perpendicular al eje 3D y normal superior, sin cizallar la cerámica según la pendiente.'
    dx=end[0]-start[0];dy=end[1]-start[1];length=math.hypot(dx,dy)
    dz=end[2]-start[2];spatial_length=math.hypot(length,dz)
    cross=(-dy/length,dx/length);normal=(-dx*dz/(length*spatial_length),-dy*dz/(length*spatial_length),length/spatial_length)
    count=9;offset=len(verts)
    # Dos arcos concéntricos hacen visible el hueco real del extremo del alero.
    for station,center in enumerate((start,end)):
        scale=1 if station==0 else taper
        for layer in (0,1):
            radius=width*.5*scale-layer*thickness
            crown=height*scale-layer*thickness
            for k in range(count):
                angle=k*math.pi/(count-1)
                transverse=radius*math.cos(angle)
                axial=chip*(1-k/(count-1))**5 if station==0 else 0
                elevation=crown*math.sin(angle)
                verts.append((center[0]+cross[0]*transverse+dx*axial+normal[0]*elevation,
                              center[1]+cross[1]*transverse+dy*axial+normal[1]*elevation,
                              center[2]+normal[2]*elevation+dz*axial))
    for layer in (0,1):
        for k in range(count-1):
            a=offset+layer*count+k;b=a+2*count
            faces.append((a,a+1,b+1,b))
    for station in (0,1):
        for k in range(count-1):
            a=offset+station*2*count+k
            faces.append((a,a+count,a+count+1,a+1))
    for k in (0,count-1):
        a=offset+k;faces.append((a,a+2*count,a+3*count,a+count))


def ceramic_mesh(coll,mat,name,verts,faces,count):
    'IA: Agrupa medias cañas cerradas; una variante por pieza y cantidad explícita; no crea objetos vacíos si el daño suprime el paño.'
    if not count:return None
    ob=primitives.mesh_obj(name,verts,faces,coll,mat)
    bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    for face in bm.faces:face.smooth=abs(face.normal.y)>.8
    bm.to_mesh(ob.data);bm.free()
    from ..geometry import surfaces
    for k in range(5):ob.data.materials.append(surfaces.variant(mat,k))
    for face in ob.data.polygons:
        face.material_index=1+(face.index//34*17)%5
        face.use_smooth=face.index%34<16
    ob['roof_tiles']=True;ob['tile_count']=count;ob['tile_profile']='half_round';ob['tile_thickness_mm']=.58
    return ob


def ridge_cap(coll,mat,x,y0,y1,z,chimney=None):
    'IA: Cumbrera de medias cañas huecas con pared de .58 mm y solape; cubre ambos faldones con la misma cerámica curva.'
    verts=[];faces=[];courses=max(1,math.ceil((y1-y0)/6));count=0
    for k in range(courses):
        a=y0+(y1-y0)*k/courses;b=y0+(y1-y0)*(k+1)/courses+.6
        if chimney and abs(x-chimney['x'])<chimney['radius']+3.2 and a<chimney['y']+chimney['radius'] and b>chimney['y']-chimney['radius']:continue
        curved_tile(verts,faces,(x,a,z+4.7),(x,b,z+3.9),6.4,2.9,taper=.78)
        count+=1
    ceramic_mesh(coll,mat,'Tejas · cumbrera',verts,faces,count)
    return count


def curved_rafter(coll,wood,p,x0,x1,y,z,rise,seed,ta=0,tb=1):
    'IA: Deforma una sola viga cerrada siguiendo el perfil; conserva veta continua sin juntas entre segmentos de curva.'
    length=abs(x1-x0)*(tb-ta)
    ob=timber.timber_beam(coll,wood,'Madera · par curvo',(0,y,0),(length,y,0),3.2,3.2,seed)
    co=primitives.coords(ob)
    for v in co:
        t=ta+(tb-ta)*v[0]/length;v[2]+=spatial.roof_height(t,z,rise,p.roof_curve);v[0]=x0+(x1-x0)*t
    primitives.set_coords(ob,co)
    bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
    ob['roof_timber']=True
    return ob


def tile_bay(coll,mat,p,xa,xm,y0,y1,z,rise,rows,seed,patches=(),missing=None,chimney=None):
    'IA: Filas alineadas con 30% de solape longitudinal; sección ortogonal, boca elevada y cola estrecha que encaja debajo de la fila superior.'
    verts=[];faces=[];rng=random.Random(seed);count=0
    columns=max(2,math.ceil((y1-y0)/5.5));pitch=(y1-y0)/columns
    for row in range(rows):
        t0=row/rows;t1=min(1,(row+1.3)/rows)
        joints=[y0+j*pitch for j in range(columns+1)]
        for a,b in zip(joints,joints[1:]):
            cx=xa+(xm-xa)*(t0+t1)/2;cy=(a+b)/2
            q=roof_damage.distance(cx,cy,patches)
            if q<1:
                if missing is not None:missing.append((cx,cy))
                continue
            if chimney and abs(cx-chimney['x'])<chimney['radius']+.2+abs(xm-xa)*(t1-t0)/2 and abs(cy-chimney['y'])<chimney['radius']+.2+(b-a)/2:continue
            lip=rng.uniform(-.025,.025)*p.wood_damage
            tilt=0
            chip=rng.uniform(.12,.36) if q<1.7 else rng.uniform(0,.055)*p.wear
            width=max(1.5,b-a+.12);crown=min(2.3,width*.45)
            start=(xa+(xm-xa)*t0,cy,spatial.roof_height(t0,z,rise,p.roof_curve)+3.35+1.15+lip)
            end=(xa+(xm-xa)*t1,cy,spatial.roof_height(t1,z,rise,p.roof_curve)+3.35+lip+tilt)
            curved_tile(verts,faces,start,end,width,crown,thickness=min(.58,width*.25),taper=.72,chip=chip)
            count+=1
    ceramic_mesh(coll,mat,'Tejas · paño curvo',verts,faces,count)
    return count


def build(coll,p,scene):
    'IA: Cerchas con dos apoyos; enlaza únicamente vecinas supervivientes. Una zona sin cerchas no recibe tejas flotantes.'
    meta.put(scene,'cubierta_generada',[]);meta.put(scene,'cubierta_detalles',{})
    for key in ('cubierta_roturas','chimeneas_generadas','bajantes_generadas'):meta.put(scene,key,[])
    meta.put(scene,'escombros_cubierta',{})
    if not p.roof_frame or p.layout_mode!='ROOM':return
    walls={w['id']:w for w in meta.get(scene,'paredes_generadas',[])}
    left,right=walls['left'],walls['right'];x0,x1=left['origin'][0],right['origin'][0]
    bounds=envelope(coll,p,walls);xa,xb,ya,yb=bounds['cover']
    y0=-p.thickness/2;y1=walls['back']['origin'][1]+p.thickness/2
    z=p.height+2.2;rise=min(68,(xb-xa)*.52);xm=(xa+xb)/2
    patches=roof_damage.plan(p,bounds);missing=[]
    chimney=roof_accessories.chimney_plan(coll,p,walls,bounds,z,rise,patches)
    meta.put(scene,'cubierta_roturas',patches)
    trees={k:openings.wall_tree(coll,walls[k]) for k in ('left','right')}
    count=max(2,math.ceil((y1-y0)/16));records=[];wood=primitives.material('Madera · cubierta',(.31,.22,.13))
    clay=primitives.material('Tejas · arcilla',(.40,.20,.115));tiles=0
    for i in range(count+1):
        y=y0+(y1-y0)*i/count
        if not all(openings.wall_hit(trees[k],walls[k],p,openings.wall_local(walls[k],(walls[k]['origin'][0],y,p.height))[0],p.height-4) for k in trees):continue
        for lo,hi in roof_segments(x0,x1,y,patches,'x',chimney):
            ob=timber.timber_beam(coll,wood,'Madera · cercha cubierta',(lo,y,p.height+.4),(hi,y,p.height+.4),3.6,3.6,p.seed+8100+i*31);ob['roof_timber']=True
        if not chimney or abs(xm-chimney['x'])>chimney['radius']+2 or abs(y-chimney['y'])>chimney['radius']+2:
            ob=timber.timber_beam(coll,wood,'Madera · cercha cubierta',(xm,y,p.height+.4),(xm,y,z+rise),2.8,2.8,p.seed+8101+i*31);ob['roof_timber']=True
        for j,x in enumerate((xa,xb)):
            for lo,hi in roof_segments(x,xm,y,patches,'x',chimney):
                ta,tb=sorted(((lo-x)/(xm-x),(hi-x)/(xm-x)))
                curved_rafter(coll,wood,p,x,xm,y,z,rise,p.seed+8300+i*31+j,ta,tb)
        if p.roof_gables and i in (0,count):gable(coll,p,wood,xa,xb,xm,y,z,rise,i,chimney)
        records.append({'index':i,'y':y,'z':z,'ridge':z+rise})
    # Extremos en vuelo solo cuando hay dos cerchas contiguas para anclar las correas.
    bays=list(records)
    if len(records)>1 and records[0]['index']==0 and records[1]['index']==1:
        bays.insert(0,dict(records[0],index=-1,y=ya))
        for j,x in enumerate((xa,xb)):
            for lo,hi in roof_segments(x,xm,ya,(),'x',chimney):
                ta,tb=sorted(((lo-x)/(xm-x),(hi-x)/(xm-x)))
                curved_rafter(coll,wood,p,x,xm,ya,z,rise,p.seed+9210+j,ta,tb)
    if len(records)>1 and records[-1]['index']==count and records[-2]['index']==count-1:
        bays.append(dict(records[-1],index=count+1,y=yb))
        for j,x in enumerate((xa,xb)):
            for lo,hi in roof_segments(x,xm,yb,(),'x',chimney):
                ta,tb=sorted(((lo-x)/(xm-x),(hi-x)/(xm-x)))
                curved_rafter(coll,wood,p,x,xm,yb,z,rise,p.seed+9220+j,ta,tb)
    rows=max(4,math.ceil(math.hypot((xb-xa)/2,rise)/6))
    for a,b in zip(bays,bays[1:]):
        if b['index']!=a['index']+1:continue
        for side,edge in enumerate((xa,xb)):
            support_x=x0 if side==0 else x1
            support_t=(support_x-edge)/(xm-edge)
            underside=spatial.roof_height(support_t,z,rise,p.roof_curve)-1.5
            if 0<=a['index'] and b['index']<=count:
                for lo,hi in roof_segments(a['y'],b['y'],support_x,(),'y',chimney,2.2):
                    ob=timber.timber_beam(coll,wood,'Madera · durmiente de alero',(support_x,lo,(p.height+underside)/2),(support_x,hi,(p.height+underside)/2),underside-p.height+.7,4.2,p.seed+9290+a['index'],coarse=True);ob['roof_timber']=True
            for j in range(rows+1):
                t=j/rows;x=edge+(xm-edge)*t;top=spatial.roof_height(t,z,rise,p.roof_curve)+2.1
                for lo,hi in roof_segments(a['y'],b['y'],x,patches,'y',chimney):
                    ob=timber.timber_beam(coll,wood,'Madera · rastrel cubierta',(x,lo,top),(x,hi,top),1.7,1.8,p.seed+8400+a['index']*71+j+side*300,coarse=True);ob['roof_timber']=True
            for j,t in enumerate((.08,.5,.93)):
                x=edge+(xm-edge)*t;top=spatial.roof_height(t,z,rise,p.roof_curve)-1.7
                for lo,hi in roof_segments(a['y'],b['y'],x,patches,'y',chimney):
                    ob=timber.timber_beam(coll,wood,'Madera · correa cubierta',(x,lo,top),(x,hi,top),3.0,3.2,p.seed+8700+a['index']*71+j,coarse=True);ob['roof_timber']=True
            if p.roof_tiles:tiles+=tile_bay(coll,clay,p,edge,xm,a['y'],b['y'],z,rise,rows,p.seed+9100+a['index']*73+side*19,patches,missing,chimney)
        if p.roof_tiles:tiles+=ridge_cap(coll,clay,xm,a['y'],b['y'],z+rise,chimney)
    if p.roof_tiles:
        supported={r['index'] for r in records}
        for i in range(count):
            if i in supported and i+1 in supported:continue
            for edge in (xa,xb):
                for t in (.18,.4,.65,.85):
                    missing.append((edge+(xm-edge)*t,y0+(y1-y0)*(i+.5)/count))
    roof_accessories.chimney(coll,p,scene,chimney)
    roof_accessories.drains(coll,p,scene,walls,bounds,bays,z,patches)
    roof_damage.debris(coll,p,scene,bounds,missing)
    meta.put(scene,'cubierta_generada',records)
    meta.put(scene,'cubierta_detalles',{'curve':p.roof_curve,'tiles':tiles,'courses':rows,'supported_trusses':len(records),'profile':'concave' if p.roof_curve else 'straight','bounds':bounds,'eave_height':z,'overhang_mm':4,'missing_tiles':len(missing)})
