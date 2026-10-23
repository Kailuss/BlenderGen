"""Catálogo provisional de mundo; números C del documento del usuario, no valores de diseño."""
VERSION='materials-0.1.0-C'
SOURCE='Usuario: Ruinas tabla mínima de materiales y revisión del esquema v2.docx; bibliografía de memoria no contrastada'
# Cada entrada numérica: valor inicial, mínimo, máximo. Las resistencias son MPa.
MECHANICAL={
    'MASONRY_LIME':{'density_ref':'stone','compression':(2,1,5),'tension':(.05,0,.2),'shear':(.15,.05,.3),'bearing':(2,1,5),'friction':(.6,.5,.7)},
    'STONE_BLOCK':{'density_ref':'stone','compression':(50,30,100),'tension':(3,2,8),'shear':(8,5,15),'bending':(6,3,15),'bearing':(50,30,100),'friction':(.6,.6,.6)},
    'TIMBER_SOFT':{'density_ref':'wood','compression':(20,15,35),'tension':(15,10,40),'shear':(3,2,6),'bending':(20,15,40),'bearing':(3,2,5),'friction':(.4,.4,.4)},
    'TIMBER_HARD':{'density_ref':'wood','compression':(35,30,50),'tension':(30,20,60),'shear':(7,5,12),'bending':(40,30,70),'bearing':(7,5,10),'friction':(.4,.4,.4)},
    'IRON_WROUGHT':{'density_ref':'metal','compression':(250,200,350),'tension':(250,200,350),'shear':(150,120,200),'friction':(.3,.3,.3)},
    'GROUND':{'density_ref':'ground','bearing':(.15,.1,.3),'tension':(0,0,0),'friction':(.5,.4,.6)},
    'GLASS':{'density_ref':None},'PLASTER':{'density_ref':None},
    'JOINERY':{'density_ref':None},'TILE_CLAY':{'density_ref':'tile'},
}
# Densidad ref es solo correspondencia heredada, no validación de esa densidad.
EVENT={
    'GLASS':('F4',(1,2),'brittle',0),
    'PLASTER':('F4',(2,5),'detachment',0),
    'JOINERY':('F3',(3,7),'fastener_pullout',.2),
    'TILE_CLAY':('F3',(3,7),'fixing_loss',.1),
    'TIMBER_SOFT':('F2',None,'support_loss_or_overload',.2),
    'TIMBER_HARD':('F2',None,'support_loss_or_bending',.2),
    'MASONRY_LIME':('F1',(15,35),'out_of_plane_or_shear',.2),
    'STONE_BLOCK':('F1',None,'bending_or_support_loss',.2),
    'IRON_WROUGHT':('F1',None,'anchor_pullout',.3),
}
AGE_RANGES={'TIMBER_SOFT':(.4,.8),'TIMBER_HARD':(.4,.8),'MASONRY_LIME':(.5,.9),'STONE_BLOCK':(.9,1),'IRON_WROUGHT':(.6,.9)}
VARIABILITY_CV={'MASONRY_LIME':.3,'TIMBER_SOFT':.25,'TIMBER_HARD':.25,'STONE_BLOCK':.2,'IRON_WROUGHT':.1}
