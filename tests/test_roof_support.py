"""Apoyo real de cubierta: el caso de la terraza colgada y sus contrarios."""
import unittest
from ruinas_panel.construction_core import roof_support as rs


def wall(x0,x1,top):
    'IA: Bloque de fábrica de 0 a top en z, y de 0 a 40.'
    return ((x0,0.,0.),(x1,40.,top))


class RoofSupportTests(unittest.TestCase):
    def test_beam_needs_both_heads(self):
        'IA: Viga de lado a lado: asentada con los dos muros a cota; colgada si un muro queda 8 mm bajo.'
        lo,hi=(1.,10.,100.),(99.,14.,104.)
        self.assertTrue(rs.beam_seated(lo,hi,0,[wall(0,15,100),wall(85,100,100)],7))
        self.assertFalse(rs.beam_seated(lo,hi,0,[wall(0,15,91.6),wall(85,100,100)],7))
        self.assertTrue(rs.beam_seated(lo,hi,0,[wall(0,15,99.8),wall(85,100,100.4)],7))

    def test_imposible_chain_falls(self):
        'IA: Viga sin asiento → losas, parapeto y almena caen por punto fijo; con asiento todo queda.'
        pieces={'beam':('beam',(1.,37.4,417.),(99.,41.4,421.),0),
                'slab_a':('slab',(10.,23.8,421.),(30.,39.4,424.),None),
                'slab_b':('slab',(10.,39.5,421.),(30.,55.,424.),None),
                'parapet':('block',(10.,24.,424.),(30.,30.,428.),None),
                'merlon':('block',(10.,24.,428.),(20.,30.,436.),None)}
        low=[((0.,0.,0.),(15.,80.,408.6)),((85.,0.,0.),(100.,80.,401.1))]
        self.assertEqual(rs.unsupported(pieces,low,7)[0],'beam')
        self.assertEqual(set(rs.unsupported(pieces,low,7)),set(pieces))
        good=[((0.,0.,0.),(15.,80.,417.)),((85.,0.,0.),(100.,80.,417.))]
        removed=rs.unsupported(pieces,good,7)
        # Una sola viga en un borde: cada losa queda en voladizo y cae; el parapeto y la almena con ella.
        self.assertEqual(set(removed),{'slab_a','slab_b','parapet','merlon'})

    def test_slab_between_two_beams(self):
        'IA: Losa con una franja de 2 mm en cada borde sobre dos vigas: apoyada; con una sola, vuelca.'
        beams={'b1':('beam',(1.,-2.,417.),(99.,2.,421.),0),'b2':('beam',(1.,14.,417.),(99.,18.,421.),0)}
        slab={'s':('slab',(10.,0.,421.),(30.,16.,424.),None)}
        walls=[((0.,-5.,0.),(15.,25.,417.)),((85.,-5.,0.),(100.,25.,417.))]
        self.assertEqual(rs.unsupported({**beams,**slab},walls,7),[])
        self.assertEqual(rs.unsupported({'b1':beams['b1'],**slab},walls,7),['s'])

    def test_trimmer_on_beams(self):
        'IA: El brochal apoya en las vigas que cruza: cae si se pierde una de ellas.'
        beams={'b1':('beam',(1.,0.,100.),(99.,4.,104.),0),'b2':('beam',(1.,40.,100.),(99.,44.,104.),0)}
        trimmer={'t':('beam',(48.,0.,100.),(52.,44.,104.),1)}
        walls=[((0.,-5.,0.),(15.,50.,100.)),((85.,-5.,0.),(100.,50.,100.))]
        self.assertEqual(rs.unsupported({**beams,**trimmer},walls,4),[])
        low=[walls[0],((85.,30.,0.),(100.,50.,100.)),((85.,-5.,0.),(100.,30.,90.))]
        self.assertEqual(set(rs.unsupported({**beams,**trimmer},low,4)),{'b1','t'})

    def test_block_area_and_overhang(self):
        'IA: Un bloque apoyado sobre una franja de borde no basta aunque toque.'
        slab={'s':('slab',(0.,0.,10.),(20.,20.,13.),None)}
        beams={'b1':('beam',(-10.,0.,6.),(30.,2.,10.),0),'b2':('beam',(-10.,18.,6.),(30.,20.,10.),0)}
        walls=[((-12.,-5.,0.),(-2.,25.,6.)),((22.,-5.,0.),(32.,25.,6.))]
        edge={'blk':('block',(18.,5.,13.),(28.,15.,17.),None)}
        self.assertEqual(rs.unsupported({**beams,**slab,**edge},walls,5),['blk'])
        inner={'blk':('block',(5.,5.,13.),(15.,15.,17.),None)}
        self.assertEqual(rs.unsupported({**beams,**slab,**inner},walls,5),[])


if __name__=='__main__':
    unittest.main()
