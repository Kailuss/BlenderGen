"""Vista de control de la fuente máxima sin recorte lejano de cámara."""
import sys
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
from blender_v032 import render
s=bpy.context.scene
render(s,ROOT/'reports/ejercicio02_pristino.png',focus=(0,120,230),location=(600,-700,600),scale=700)
s.camera.data.clip_end=10000
bpy.ops.render.render(write_still=True)
