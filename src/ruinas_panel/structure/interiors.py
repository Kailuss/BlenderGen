"""Tabiques de planta baja derivados del plano previo."""
from .. import meta
from ..geometry import primitives
from . import spatial


def build(coll,p,scene):
    'IA: Tabiques de revoco de 3 mm con pasos y dinteles; cimentados en planta baja, coronación limitada por el daño espacial existente.'
    plan=meta.get(scene,'plano_interior',{})
    if not plan or 'error' in plan:return
    mat=primitives.material('Revoco · interior',(.64,.58,.46))
    wood=primitives.material('Madera · tabique',(.30,.20,.12))
    bottom=3 if p.ground_floor else .7;top=min(p.height,55.2)
    for index,part in enumerate(plan['partitions']):
        doors=[(c-12.5,c+12.5) for c in part['doors']]
        cuts=sorted({part['start'],part['end'],*[x for pair in doors for x in pair]})
        for a,b in zip(cuts,cuts[1:]):
            mid=(a+b)/2;over=any(lo<mid<hi for lo,hi in doors)
            z0=bottom+34 if over else bottom
            x,y=(mid,part['fixed']) if part['axis']=='x' else (part['fixed'],mid)
            z1=min(top,spatial.collapse_height(p,x,y))
            if z1-z0<1:continue
            if part['axis']=='x':bounds=(a,b,y-1.5,y+1.5)
            else:bounds=(x-1.5,x+1.5,a,b)
            ob=primitives.block('Revoco · tabique interior',*bounds,z0,z1,coll,mat)
            ob['interior_partition']=True;ob['partition_id']=index
            if over:
                ob=primitives.block('Madera · dintel interior',*bounds,z0-.6,min(z1,z0+2),coll,wood)
                ob['interior_partition']=True
