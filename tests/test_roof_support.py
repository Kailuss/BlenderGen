"""0.32.31: apoyo real de cubiertas (caso imposible.blend, semilla 17)."""
import unittest
from ruinas_panel.construction_core import roof_support as rs


class RoofSupportTests(unittest.TestCase):
    def test_beam_without_stone_does_not_bear(self):
        'IA: Cabeza de viga a 8,4 mm de la piedra más alta (medida de imposible.blend): no entrega; a 0,2 mm sí.'
        foot=(-117.6,-103.6,37.4,41.4);bottom=417.0
        low=[((-119.7,26.5,401.6),(-102.6,40.2,408.6))]
        self.assertFalse(rs.bearing(foot,bottom,low)[0])
        crown=[((-119.7,26.5,409.1),(-102.6,43.2,416.8))]
        self.assertTrue(rs.bearing(foot,bottom,crown)[0])

    def test_partial_bearing_needs_half_length(self):
        'IA: Piedra que solo cubre 3 de 14 mm de entrega no basta.'
        foot=(0,14,0,4)
        self.assertFalse(rs.bearing(foot,10,[((11,0,5),(20,4,10))])[0])
        self.assertTrue(rs.bearing(foot,10,[((6,0,5),(20,4,10))])[0])

    def test_slab_on_one_edge_strip_tips(self):
        'IA: Losa de imposible.blend: franja de 2 mm sobre una sola viga en su borde → vuelca; con viga en el otro borde → apoya.'
        slab=((-101.6,23.84,421.0),(-84.8,39.37,424.0))
        beam=((-117.6,37.4,417.0),(117.6,41.4,421.0))
        self.assertFalse(rs.seated(slab,[beam],rs.MIN_SLAB_CONTACT)[0])
        other=((-117.6,22.0,417.0),(117.6,26.0,421.0))
        self.assertTrue(rs.seated(slab,[beam,other],rs.MIN_SLAB_CONTACT)[0])

    def test_zero_area_contact_is_not_support(self):
        'IA: Tocar por una arista (área cero) no es apoyo, al contrario que la regla anterior con >=.'
        block=((0,0,10),(10,10,14))
        self.assertFalse(rs.seated(block,[((10,0,6),(20,10,10))])[0])

    def test_block_needs_area_and_centre(self):
        'IA: Bloque con el 30 % apoyado en un lado: área suficiente pero el centro queda fuera → vuelca; apoyado bajo el centro → aguanta.'
        block=((0,0,10),(10,6,14))
        self.assertFalse(rs.seated(block,[((-5,0,6),(3,6,10))])[0])
        self.assertTrue(rs.seated(block,[((2,0,6),(8,6,10))])[0])

    def test_seat_height_window(self):
        'IA: Un asiento 1 mm por debajo de la base no cuenta como contacto.'
        block=((0,0,10),(10,6,14))
        self.assertFalse(rs.seated(block,[((0,0,6),(10,6,9))])[0])

    def test_landing_ignores_surfaces_above_start(self):
        'IA: La pieza cae sobre la superficie más alta bajo su huella que no supera su base de partida.'
        foot=(0,10,0,10)
        surfaces=[((-5,-5,0),(20,20,2)),((2,2,0),(8,8,40)),((50,50,0),(60,60,90)),((0,0,300),(10,10,320))]
        self.assertEqual(rs.landing(foot,100,surfaces),(40,1))
        self.assertEqual(rs.landing((100,110,100,110),100,surfaces),(0.0,-1))


if __name__=='__main__':
    unittest.main()
