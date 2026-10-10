"""Prefractura acotada de revocos y fábrica hueca sobre copias físicas en mm."""
import hashlib
import random
import bpy
import bmesh
from mathutils import Vector
from .. import config


def split(mesh,axis,seed):
    'IA: Bisección oblicua reproducible de un sólido; exige cierre y conservación de volumen, incluidas las tapas interiores de conductos.'
    rng=random.Random(seed);points=[v.co for v in mesh.vertices]
    lo=Vector([min(v[k] for v in points) for k in range(3)]);hi=Vector([max(v[k] for v in points) for k in range(3)])
    center=(lo+hi)/2;center[axis]+=(hi[axis]-lo[axis])*rng.uniform(-.08,.08)
    normal=Vector((0,0,0));normal[axis]=1
    other=max((k for k in range(3) if k!=axis),key=lambda k:hi[k]-lo[k]);normal[other]=rng.uniform(-.09,.09)
    results=[];volumes=[]
    original=bmesh.new();original.from_mesh(mesh);before=abs(original.calc_volume());original.free()
    try:
        for side in (False,True):
            bm=bmesh.new();bm.from_mesh(mesh)
            try:
                bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-6,plane_co=center,plane_no=normal,clear_inner=side,clear_outer=not side)
                boundary=[e for e in bm.edges if e.is_boundary]
                if boundary:bmesh.ops.holes_fill(bm,edges=boundary,sides=0)
                bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=1e-6)
                bmesh.ops.triangulate(bm,faces=list(bm.faces));bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
                volume=bm.calc_volume()
                if not bm.faces or not all(e.is_manifold for e in bm.edges) or volume<=1e-5:raise ValueError('Corte frágil no cerrado: '+mesh.name)
                result=bpy.data.meshes.new(mesh.name+' · fragmento');bm.to_mesh(result)
                for material in mesh.materials:result.materials.append(material)
                results.append(result);volumes.append(volume)
            finally:bm.free()
        if abs(sum(volumes)-before)>max(.001,before*.0001):raise ValueError('La prefractura alteraría el volumen o cerraría el conducto: '+mesh.name)
        return results
    except Exception:
        for result in results:bpy.data.meshes.remove(result)
        raise


def fragment(objects,coll,report,size=20):
    'IA: Sustituye solo copias de paños grandes por sólidos cerrados con IDs derivados; límite global explícito, sin dejar bloques gigantes silenciosamente.'
    created=0
    for ob in list(objects):
        name=ob.get('source_piece',ob.name);key=name.lower()
        plaster='revoco' in key
        chimney=any(s in key for s in ('chimenea','hogar','campana'))
        if ob.get('physical_role')!='stone' or not (plaster or chimney):continue
        seed=int.from_bytes(hashlib.sha256(name.encode()).digest()[:4],'big')
        pending=[(ob.data.copy(),'')];finished=[]
        try:
            while pending:
                mesh,lineage=pending.pop()
                points=[v.co for v in mesh.vertices];spans=[max(v[k] for v in points)-min(v[k] for v in points) for k in range(3)]
                if max(spans)<=size*1.1:
                    finished.append((mesh,lineage));continue
                if created+len(pending)+len(finished)+2>config.PHYSICS_FRAGILE_LIMIT:
                    bpy.data.meshes.remove(mesh);raise ValueError('Demasiados fragmentos de revoco/chimenea: aumenta el tamaño de fragmento o reduce la casa.')
                # Abrir primero el anillo en vertical evita tapar la luz hueca al cortar por altura.
                axis=0 if not lineage and any(s in key for s in ('conducto','campana','remate chimenea')) else max(range(3),key=lambda k:spans[k])
                try:children=split(mesh,axis,seed+sum((i+1)*ord(c) for i,c in enumerate(lineage)))
                finally:bpy.data.meshes.remove(mesh)
                pending.extend((child,lineage+str(i)) for i,child in enumerate(children))
            if len(finished)==1:
                bpy.data.meshes.remove(finished[0][0]);ob['fragile_material']='plaster' if plaster else 'chimney';continue
            for mesh,lineage in finished:
                clone=bpy.data.objects.new(ob.name+' · fractura '+lineage,mesh);coll.objects.link(clone)
                for k in ob.keys():clone[k]=ob[k]
                clone['fragile_material']='plaster' if plaster else 'chimney';clone['fracture_parent']=name
                clone['physical_piece_id']='%s:%s:%s:fragment:%s'%(name,ob.get('source_component',0),ob.get('cut_component',0),lineage)
                objects.append(clone)
            created+=len(finished);objects.remove(ob);old=ob.data;bpy.data.objects.remove(ob,do_unlink=True)
            if old.users==0:bpy.data.meshes.remove(old)
        except Exception:
            for mesh,_ in pending+finished:
                if mesh.users==0:bpy.data.meshes.remove(mesh)
            raise
    report['fragile_fragments']=created
    return objects
