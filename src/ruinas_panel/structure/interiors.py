"""Tabiques de madera de planta baja derivados del plano previo."""
import math
import random
from .. import meta,config
from ..geometry import primitives
from . import spatial


def wood_panel(coll,mat,part,a,b,z0,z1,grain,seed):
    'IA: Panel único cerrado de 3 mm; juntas y veta física en ambas caras, sin booleanos ni tablas sueltas; espesor mínimo 2,3 mm.'
    import bmesh
    from ..geometry import surfaces
    boards=max(1,round((b-a)/6));nx=boards*6;nz=max(2,min(20,math.ceil((z1-z0)/3)))
    rng=random.Random(seed);phases=[rng.uniform(0,math.tau) for _ in range(boards)]
    verts=[];faces=[];uvs=[];n=(nx+1)*(nz+1)
    for side in (-1,1):
        for j in range(nz+1):
            t=j/nz;z=z0+(z1-z0)*t
            for i in range(nx+1):
                u=i/nx;along=a+(b-a)*u;board=min(boards-1,i//6);local=(i%6)/6
                phase=phases[board]+(0 if side<0 else .7)
                seam=.32 if i%6==0 and 0<i<nx else 0
                fiber=max(0,math.cos(local*math.tau*2+.25*math.sin(t*9+phase)))**6
                knot=math.exp(-((local-.5)/.22)**2-((t-.45-.15*math.sin(phase))/.13)**2)
                relief=min(.35,seam+grain*(.30*fiber+.20*knot))
                cross=part['fixed']+side*(1.5-relief)
                verts.append((along,cross,z) if part['axis']=='x' else (cross,along,z))
                uvs.append((u*boards,(z-z0)/8))
    for side in range(2):
        for j in range(nz):
            for i in range(nx):
                k=side*n+j*(nx+1)+i;faces.append((k,k+1,k+nx+2,k+nx+1))
    border=list(range(nx+1))+[j*(nx+1)+nx for j in range(1,nz+1)]+[nz*(nx+1)+i for i in range(nx-1,-1,-1)]+[j*(nx+1) for j in range(nz-1,0,-1)]
    for i,k in enumerate(border):
        q=border[(i+1)%len(border)];faces.append((k,q,q+n,k+n))
    ob=primitives.mesh_obj('Revoco · tabique interior',verts,faces,coll,mat)
    bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
    surfaces.grain_uv(ob,uvs)
    ob['partition_finish']='WOOD';ob['minimum_thickness_mm']=2.3
    return ob


def build(coll,p,scene):
    'IA: Secciones cerradas de madera con apoyo identificado, solape interno de .02 mm y pasos del plano libres; daño limita la coronación de cada columna.'
    plan=meta.get(scene,'plano_interior',{})
    if not plan or 'error' in plan:return
    mat=primitives.material('Madera · interior',(.37,.255,.145))
    wood=primitives.material('Madera · tabique',(.30,.20,.12))
    bottom=3 if p.ground_floor else .7;top=min(p.height,55.2)
    for index,part in enumerate(plan['partitions']):
        doors=[(c-plan['door_width']/2,c+plan['door_width']/2) for c in part['doors']]
        cuts=sorted({part['start'],part['end'],*[x for pair in doors for x in pair]})
        for a,b in zip(cuts,cuts[1:]):
            mid=(a+b)/2;over=any(lo<mid<hi for lo,hi in doors)
            z0=bottom+34 if over else bottom
            x,y=(mid,part['fixed']) if part['axis']=='x' else (part['fixed'],mid)
            z1=min(top,spatial.collapse_height(p,x,y))
            if over and z1-z0<1:continue
            if part['axis']=='x':bounds=(a,b,y-1.5,y+1.5)
            else:bounds=(x-1.5,x+1.5,a,b)
            columns=max(1,math.ceil((b-a)/config.PARTITION_SECTION_WIDTH))
            for column in range(columns):
                left=a+(b-a)*column/columns;right=a+(b-a)*(column+1)/columns
                mid=(left+right)/2
                sx,sy=(mid,part['fixed']) if part['axis']=='x' else (part['fixed'],mid)
                rng=random.Random(p.seed+72000+index*193+round(left*11))
                height=min(top,spatial.collapse_height(p,sx,sy))-p.wood_damage*rng.uniform(0,5)
                if height-z0<1:continue
                rows=max(1,math.ceil((height-z0)/config.PARTITION_SECTION_HEIGHT));below='%s:%s:lintel'%(index,round(a,3)) if over else 'ground'
                for row in range(rows):
                    low=z0+config.PARTITION_SECTION_HEIGHT*row;high=min(height,low+config.PARTITION_SECTION_HEIGHT)
                    if high-low<1:continue
                    if row:low-=config.PARTITION_JOINT_OVERLAP
                    if column:left_overlap=left-config.PARTITION_JOINT_OVERLAP
                    else:left_overlap=left
                    ob=wood_panel(coll,mat,part,left_overlap,right,low,high,p.wood_grain,p.seed+71000+index*193+round(left*11)+row*29)
                    key='%s:%s:%s:%s'%(index,round(a,3),column,row)
                    ob['interior_partition']=True;ob['partition_id']=index
                    ob['partition_section']=key;ob['rests_on']=below;below=key
            if over:
                ob=primitives.block('Madera · dintel interior',*bounds,z0-.6,min(z1,z0+2),coll,wood)
                ob['interior_partition']=True;ob['partition_section']='%s:%s:lintel'%(index,round(a,3));ob['rests_on']='jambs'
