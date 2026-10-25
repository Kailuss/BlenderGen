"""Extracción mecánica verificable del cálculo de aparejo heredado."""
from pathlib import Path


def run():
    'IA: Mueve bloques exactos a layout sin cambiar operaciones ni RNG; falla si ya se ha aplicado.'
    root=Path(__file__).resolve().parents[1]
    wp=root/'src/ruinas_panel/structure/walls.py';lp=root/'src/ruinas_panel/structure/layout.py'
    w=wp.read_text(encoding='utf8');l=lp.read_text(encoding='utf8')
    assert 'def front_courses(' not in l
    start=w.index('    # Referencias físicas de los extremos.')
    end=w.index("    meta.put(context.scene,'puerta_generada',door)",start)
    body=w[start:end].replace('layout.','')
    header="\n\ndef front_courses(p):\n    'IA: Calcula hiladas, derrumbe, puerta y pilares sin mallas; conserva el orden de RNG y devuelve intervalos nominales en mm.'\n    L,H,T=p.length,p.height,p.thickness\n    dseed=distribution_seed(p);door=plan_door(p)\n    z_edges,rh=course_layout(p);rows=len(z_edges)-1\n"
    l+='\n'+header+body+"    return {'courses':courses,'centers':centers,'door':door,'edges':z_edges,'row_height':rh}\n"
    w=w[:start]+"    planned=layout.front_courses(p)\n    courses,centers=planned['courses'],planned['centers']\n"+w[end:]
    start=w.index('    bays=max(2,round(length/(rh*1.8)))')
    end=w.index('        for j,(a,b) in enumerate(pieces):',start)
    body=w[start:end].replace('layout.','')
    body=body.replace('        pieces=merge_thin_stones(list(zip(joints,joints[1:])),3.2)',
                      '        pieces=merge_thin_stones(list(zip(joints,joints[1:])),3.2)\n        result.append({\'row\':row,\'z0\':z0,\'z1\':z1,\'pieces\':pieces})')
    l+="\n\ndef return_courses(p,wall_id,start,end,height,edges):\n    'IA: Aparejo puro de retornos y trasera; intervalos nominales y cotas previos al bisel, con semillas históricas por pared.'\n    length=end-start;rh=(p.height-2)/(len(edges)-1);result=[]\n"+body+"    return result\n"
    w=w[:start]+"    for course in layout.return_courses(p,wall_id,start,end,height,edges):\n        row,z0,z1,pieces=course['row'],course['z0'],course['z1'],course['pieces']\n"+w[end:]
    l=l.replace('import random','import random\nimport math',1)
    lp.write_text(l,encoding='utf8');wp.write_text(w,encoding='utf8')


if __name__=='__main__':run()
