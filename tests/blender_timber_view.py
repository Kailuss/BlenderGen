"""Inspección de madera afectada sobre la fuente integrada, sin modificar el archivo."""
import sys
from pathlib import Path
import bpy
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tests'));sys.path.insert(0,str(ROOT/'src'))
from blender_v032 import render


def run():
    'IA: Muestra las fracturas y el conjunto de vigas sin tejas; exige que el eje de cada tramo afectado sea recto con relieve acotado.'
    scene=bpy.context.scene;pieces=[o for o in scene.objects if o.get('roof_fracture_parent')]
    assert pieces
    for ob in pieces:
        a,b=[Vector(v) for v in ob['timber_path']];axis=(b-a).normalized()
        width=ob['timber_width'];depth=ob['timber_depth'];limit=(width*width+depth*depth)**.5/2+.1
        assert max(((v.co-a)-axis*(v.co-a).dot(axis)).length for v in ob.data.vertices)<=limit,ob.name
    for ob in scene.objects:ob.hide_render=not bool(ob.get('roof_timber'))
    render(scene,ROOT/'reports/synergy_timber.png',focus=(0,90,145),location=(200,-200,300),scale=285)
    part=max((o for o in pieces if o.get('timber_broken_start') or o.get('timber_broken_end')),key=lambda o:o.get('roof_sag_mm',0))
    a,b=[Vector(v) for v in part['timber_path']];center=(a+b)/2
    render(scene,ROOT/'reports/synergy_splinters.png',focus=center,location=center+Vector((35,-50,45)),scale=65)
    print('TIMBER_VIEW_PASSED',len(pieces),flush=True)


if __name__=='__main__':run()
