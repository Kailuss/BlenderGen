"""Prefractura acotada de revocos y fábrica hueca sobre copias físicas en mm."""
import hashlib
import random
import bpy
import bmesh
from mathutils import Vector
from .. import config


def triangulate_closed(bm):
    'IA: Triangula polígonos sin reutilizar como diagonal una arista exterior de otra cara; separa esa diagonal con un punto interior propio y conserva la superficie.'
    from mathutils.geometry import tessellate_polygon
    for face in list(bm.faces):
        if len(face.verts)<=3:continue
        vertices=list(face.verts);lookup={tuple(v.co):v for v in vertices}
        triangles=[[vertices[co] if isinstance(co,int) else lookup[tuple(co)] for co in tri] for tri in tessellate_polygon([[v.co.copy() for v in vertices]])]
        triangles=[tri for tri in triangles if len(set(tri))==3]
        boundary={frozenset(edge.verts) for edge in face.edges}
        interior={}
        for tri in triangles:
            for a,b in zip(tri,tri[1:]+tri[:1]):
                key=frozenset((a,b))
                if key not in boundary and bm.edges.get((a,b)) is not None and key not in interior:
                    interior[key]=bm.verts.new((a.co+b.co)*.5)
        material=face.material_index;bm.faces.remove(face)
        for tri in triangles:
            ring=[]
            for a,b in zip(tri,tri[1:]+tri[:1]):
                ring.append(a)
                midpoint=interior.get(frozenset((a,b)))
                if midpoint is not None:ring.append(midpoint)
            if len(ring)==3:
                bm.faces.new(ring).material_index=material
            else:
                center=bm.verts.new(sum((v.co for v in tri),Vector())/3)
                for a,b in zip(ring,ring[1:]+ring[:1]):bm.faces.new((a,b,center)).material_index=material
    bmesh.ops.triangulate(bm,faces=list(bm.faces),ngon_method='EAR_CLIP')


def split(mesh,axis,seed):
    'IA: Ensaya hasta ocho planos oblicuos sembrados para evitar cortes tangentes degenerados; cada resultado debe conservar cierre y volumen, sin aceptar fragmentos defectuosos.'
    failure=None
    for attempt in range(8):
        try:return _split_once(mesh,axis,seed+attempt*104729)
        except ValueError as error:failure=error
    raise failure


def _split_once(mesh,axis,seed):
    'IA: Bisección oblicua reproducible de un sólido triangulado antes del corte para preservar el relieve; exige cierre y conservación de volumen, incluidas las tapas interiores de conductos.'
    rng=random.Random(seed);points=[v.co for v in mesh.vertices]
    lo=Vector([min(v[k] for v in points) for k in range(3)]);hi=Vector([max(v[k] for v in points) for k in range(3)])
    center=(lo+hi)/2;center[axis]+=(hi[axis]-lo[axis])*rng.uniform(-.08,.08)
    normal=Vector((0,0,0));normal[axis]=1
    other=max((k for k in range(3) if k!=axis),key=lambda k:hi[k]-lo[k]);normal[other]=rng.uniform(-.09,.09)
    results=[];volumes=[]
    original=bmesh.new();original.from_mesh(mesh)
    triangulate_closed(original)
    before=abs(original.calc_volume());original.free()
    try:
        for side in (False,True):
            bm=bmesh.new();bm.from_mesh(mesh)
            try:
                triangulate_closed(bm)
                bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-6,plane_co=center,plane_no=normal,clear_inner=side,clear_outer=not side)
                boundary=[e for e in bm.edges if e.is_boundary]
                if boundary:bmesh.ops.holes_fill(bm,edges=boundary,sides=0)
                cut_edges=[e for e in bm.edges if all(abs((v.co-center).dot(normal.normalized()))<1e-5 for v in e.verts)]
                if cut_edges:bmesh.ops.dissolve_degenerate(bm,edges=cut_edges,dist=1e-6)
                wires=[edge for edge in bm.edges if edge.is_wire]
                if wires:bmesh.ops.delete(bm,geom=wires,context='EDGES')
                isolated=[vertex for vertex in bm.verts if not vertex.link_edges]
                if isolated:bmesh.ops.delete(bm,geom=isolated,context='VERTS')
                triangulate_closed(bm)
                # La disolución de triángulos casi nulos puede reabrir pequeños
                # bucles de la tapa. Solo se cierran si pertenecen al plano cortado.
                remaining=[e for e in bm.edges if e.is_boundary]
                if remaining and all(abs((v.co-center).dot(normal.normalized()))<1e-4 for e in remaining for v in e.verts):
                    bmesh.ops.holes_fill(bm,edges=remaining,sides=0)
                    triangulate_closed(bm)
                bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
                volume=bm.calc_volume()
                invalid=sum(not e.is_manifold for e in bm.edges)
                if not bm.faces or invalid or volume<=1e-5:raise ValueError('Corte frágil no cerrado: %s (%s aristas, volumen %.8f, enlaces %s)'%(mesh.name,invalid,volume,[(len(e.link_faces),round(e.calc_length(),8)) for e in bm.edges if not e.is_manifold][:6]))
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
