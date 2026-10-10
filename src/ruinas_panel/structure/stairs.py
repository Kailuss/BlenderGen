"""Escaleras rectas interiores: reserva de hueco, desembarco y apoyos explícitos."""
import math
import random
import bmesh
from .. import meta,config,runtime
from ..geometry import primitives,timber,weather
from . import floors,layout


def plan(p,bounds):
    'IA: Reserva una escalera junto al muro trasero para dos plantas; reserva 35 mm libres antes del primer peldaño sin reducir su huella.'
    if p.stair_type=='NONE' or p.height_type!='TWO' or not p.upper_floor or not p.floor_beams:return None
    xmin,xmax,ymin,ymax=bounds
    approach=35.0
    available=xmax-xmin-8-approach
    pitch=22.4;landing=22.4
    steps=min(7,int((available-landing)/pitch))
    if steps<2 or ymax-ymin<29:return {'error':'Escalera jugable: necesita 111 × 29 mm interiores para peldaños útiles de 20 × 20 mm.'}
    run=steps*pitch;left=xmin+4+approach
    bottom=3.2 if p.ground_floor else 1.0
    right=left+run;ya=ymax-26.4;yb=ymax-4
    reverse=p.stair_side=='LEFT'
    if reverse:left=xmax-4-approach-run;right=xmax-4-approach
    x0=left-landing if reverse else left
    x1=right if reverse else right+landing
    return {'x0':left,'x1':right,'y0':ya,'y1':yb,'bottom':bottom,'top':layout.upper_floor(p),'steps':steps,'reverse':reverse,
            'opening':[left-.5,right+.5,ya-.8,yb+.8],'landing':[x0,left] if reverse else [right,x1],'type':p.stair_type,
            'usable_tread_mm':20,'pitch_mm':pitch,'riser_mm':(layout.upper_floor(p)-bottom)/steps,'width_mm':yb-ya,'approach_mm':approach,'approach':[right+1.5,right+approach+1.5,ya,yb] if reverse else [left-approach-1.5,left-1.5,ya,yb]}


def stone_skin(coll,p,s,stone,xx):
    'IA: Aparejo solo en caras expuestas de la escalera; reutiliza desgaste de pared y termina 0,55 mm bajo cada huella para no tapar el relieve de la losa.'
    n=s['steps'];pitch=s['pitch_mm'];rise=s['riser_mm'];ya,yb=s['y0'],s['y1']
    for i in range(n):
        top=s['bottom']+(i+1)*rise
        rows=max(1,math.ceil((top-.6)/p.stone_size));rh=(top-.6)/rows
        for row in range(rows):
            z0=.6+row*rh;z1=min(z0+rh-.18,top-.55)
            joints=[0,pitch*.5,pitch] if row%2==0 else [0,pitch*.25,pitch*.75,pitch]
            for part,(a,b) in enumerate(zip(joints,joints[1:])):
                lo,hi=sorted((xx(i*pitch+a+.12),xx(i*pitch+b-.12)))
                for side,(y0,y1) in enumerate(((ya-.05,ya+1.3),(yb-1.3,yb+.05))):
                    ob=primitives.block('Piedra · escalera lateral %s.%s.%s.%s'%(i,row,part,side),lo,hi,y0,y1,z0,z1,coll,stone)
                    ob['stair']=True;weather.weather_stone(ob,p.wear*.65,p.seed+31000+i*101+row*17+part+side*7)
        zbase=s['bottom']+i*rise
        rows=max(1,math.ceil(rise/p.stone_size))
        for row in range(rows):
            cuts=[ya,ya+7.4,yb-7.4,yb] if row%2==0 else [ya,(ya+yb)/2,yb]
            lo,hi=sorted((xx(i*pitch-.2),xx(i*pitch+1.3)))
            for part,(a,b) in enumerate(zip(cuts,cuts[1:])):
                ob=primitives.block('Piedra · escalera contrahuella %s.%s.%s'%(i,row,part),lo,hi,a+.12,b-.12,zbase+row*rise/rows,min(zbase+(row+1)*rise/rows-.18,zbase+rise-.55),coll,stone)
                ob['stair']=True;weather.weather_stone(ob,p.wear*.65,p.seed+32000+i*101+row*17+part)


def stone_tread(coll,stone,name,a,b,ya,yb,top,amount,seed):
    'IA: Losa cerrada de 1,05 mm con relieve físico sembrado y cantos gastados; centro útil 20×20 mm con depresiones de hasta 0,24 mm; Borrador/Trabajo omiten erosión.'
    import numpy
    detail=runtime.quality in config.DAMAGE_QUALITIES
    amount=max(0.0,min(1.0,amount)) if detail else 0.0
    # La densidad solo cubre la huella; el fondo plano usa un único polígono.
    spacing=.8 if detail else 3.2
    nx=max(2,math.ceil((b-a)/spacing));ny=max(2,math.ceil((yb-ya)/spacing))
    cx=(a+b)/2;cy=(ya+yb)/2
    xs=sorted(set(numpy.linspace(a,b,nx+1).tolist()+[cx-10,cx+10]))
    ys=sorted(set(numpy.linspace(ya,yb,ny+1).tolist()+[cy-10,cy+10]))
    nx=len(xs)-1;ny=len(ys)-1
    xx,yy=numpy.meshgrid(xs,ys)
    rng=random.Random(seed)
    phase=rng.uniform(0,math.tau)
    distance=numpy.minimum.reduce((xx-a,b-xx,yy-ya,yb-yy))
    edge_width=.75+.2*numpy.sin(xx*.38+yy*.21+phase)
    border=numpy.clip(1-distance/edge_width,0,1)
    # Huella suavizada por el paso: depresiones limitadas, sin puntas que inclinen una peana.
    broad=(1+numpy.sin(xx*.61+phase)*numpy.cos(yy*.47-phase))*.5
    chisel=(1+numpy.sin(xx*2.7+yy*.4+phase)*numpy.cos(yy*2.1))*.5
    pits=numpy.zeros_like(xx)
    for _ in range(22):
        px=rng.uniform(a,b);py=rng.uniform(ya,yb);radius=rng.uniform(.65,1.25)
        pits+=rng.uniform(.3,1.0)*numpy.exp(-((xx-px)**2+(yy-py)**2)/(radius*radius))
    # Piedra tallada en placas, no ruido aplicado a cada vértice de forma independiente.
    loss=.12*border+amount*(.03*broad+.03*chisel+.18*numpy.minimum(pits,1)
                              +border*(.12+.18*broad))
    loss=numpy.minimum(loss,.62)  # El macizo queda al menos 0,03 mm bajo el fondo de cualquier poro.
    surface=top+.1-loss
    # Desconchones pequeños en el contorno, fuera de los 20 mm de apoyo central.
    inset=amount*.16*border**3*(.3+.7*broad)
    sx=xx+numpy.sign(cx-xx)*inset*numpy.clip(1-numpy.minimum(xx-a,b-xx)/.95,0,1)
    sy=yy+numpy.sign(cy-yy)*inset*numpy.clip(1-numpy.minimum(yy-ya,yb-yy)/.95,0,1)
    verts=[(float(x),float(y),float(z)) for x,y,z in zip(sx.ravel(),sy.ravel(),surface.ravel())]
    faces=[]
    for j in range(ny):
        for i in range(nx):
            k=j*(nx+1)+i
            # Triángulos explícitos conservan el relieve al fusionar/exportar caras no planas.
            faces.extend(((k,k+1,k+nx+2),(k,k+nx+2,k+nx+1)))
    ring=list(range(nx+1))+[j*(nx+1)+nx for j in range(1,ny+1)]
    ring+=[ny*(nx+1)+i for i in range(nx-1,-1,-1)]+[j*(nx+1) for j in range(ny-1,0,-1)]
    bottom=len(verts)
    verts.extend((verts[k][0],verts[k][1],top-.95) for k in ring)
    faces.append(tuple(reversed(range(bottom,bottom+len(ring)))))
    for j,k in enumerate(ring):
        following=(j+1)%len(ring)
        faces.append((k,bottom+j,bottom+following,ring[following]))
    ob=primitives.mesh_obj(name,verts,faces,coll,stone)
    for face in ob.data.polygons[:nx*ny*2]:face.use_smooth=True
    ob['stair']=True;ob['stair_surface']=True;ob['usable_tread_mm']=20.0
    ob['stair_relief_mm']=float(loss.max()-loss.min())
    return ob


def build(coll,p,scene,plan):
    'IA: Peldaños jugables y zancas o macizo hasta suelo; reserva 0,55 mm de relieve bajo losas de piedra; desembarco a layout.upper_floor(p) y postes bajo cabecero.'
    meta.put(scene,'escalera_generada',plan or {})
    if not plan or 'error' in plan:return
    s=plan;wood=primitives.material('Madera · escalera',(.34,.235,.13));stone=primitives.material('Piedra · neutro',(.52,.52,.52))
    x0,x1,ya,yb=s['x0'],s['x1'],s['y0'],s['y1'];n=s['steps'];pitch=(x1-x0)/n;rise=(s['top']-s['bottom'])/n
    def xx(u):
        'IA: Convierte distancia de ascenso a X conservando la misma reserva de hueco al invertir.'
        return x1-u if s['reverse'] else x0+u
    if s['type']=='STONE':
        # Perfil escalonado extruido: un solo macizo, sin pilas de cubos interiores.
        profile=[(0,.6),(x1-x0,.6),(x1-x0,s['top']-.55)]
        for i in range(n-1,-1,-1):
            profile.append((i*pitch,s['bottom']+(i+1)*rise-.55))
            if i:profile.append((i*pitch,s['bottom']+i*rise-.55))
        verts=[(xx(u),y,z) for y in (ya+1.0,yb-1.0) for u,z in profile];count=len(profile)
        faces=[tuple(range(count)),tuple(reversed(range(count,2*count)))]+[(i,(i+1)%count,(i+1)%count+count,i+count) for i in range(count)]
        ob=primitives.mesh_obj('Escalera · macizo piedra',verts,faces,coll,stone)
        bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
        ob['stair']=True
        stone_skin(coll,p,s,stone,xx)
        # El macizo queda bajo el relieve y cada losa mantiene solape de 0,4 mm con él.
        for i in range(n):
            a,b=sorted((xx(i*pitch),xx((i+1)*pitch)))
            stone_tread(coll,stone,'Escalera · losa %02d'%i,a,b,ya-.2,yb+.2,s['bottom']+(i+1)*rise,p.wear,p.seed+33000+i)
    else:
        for y in (ya+1.2,yb-1.2):
            ob=timber.timber_beam(coll,wood,'Madera · zanca escalera',(xx(0),y,s['bottom']+.5),(xx(x1-x0),y,s['top']-1.5),3.8,3.6,p.seed+27110+round(y))
            ob['stair']=True
        for i in range(n):
            a,b=sorted((xx(i*pitch),xx((i+1)*pitch)))
            ob=floors.plank(coll,wood,'Madera · peldaño %02d'%i,a-.2,b+.2,(ya+yb)/2,yb-ya,s['bottom']+(i+1)*rise,p.seed+27300+i,p.wood_grain)
            ob['stair']=True
    # Cabecero bajo el corte de las vigas existentes; sus postes mantienen el apoyo.
    hy=ya-2.4
    for x in (x0-1.8,x1+1.8):
        ob=timber.timber_beam(coll,wood,'Madera · poste hueco escalera',(x,hy,.7),(x,hy,s['top']-3.5),3.8,3.8,p.seed+round(x*11))
        ob['stair']=True
    ob=timber.timber_beam(coll,wood,'Madera · cabecero escalera',(x0-3,hy,(layout.upper_floor(p)-3.6)),(x1+3,hy,(layout.upper_floor(p)-3.6)),4.2,4.7,p.seed+27400);ob['stair']=True
    for x in s['landing']:
        ob=timber.timber_beam(coll,wood,'Madera · poste desembarco',(x,(ya+yb)/2,.7),(x,(ya+yb)/2,s['top']-1.5),4,4,p.seed+round(x*7));ob['stair']=True
    a,b=s['landing']
    for i in range(4):
        ob=floors.plank(coll,wood,'Madera · desembarco %s'%i,a,b,ya+(i+.5)*(yb-ya)/4,(yb-ya)/4-.08,s['top'],p.seed+27500+i,p.wood_grain);ob['stair']=True
