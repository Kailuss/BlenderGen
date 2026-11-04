"""C5-3: una sola definición de asiento para constructor, plan y ensayos."""
import unittest
from ruinas_panel.construction_core import seat
from ruinas_panel.structure import floor_frame


class SeatTests(unittest.TestCase):
    def test_legacy_values(self):
        'IA: La unificación no mueve geometría: cotas, caja y sección iguales a los literales anteriores.'
        self.assertEqual(seat.beam_z(50.0),50.0-3.6)
        self.assertEqual(seat.beam_z(50.0,'FACADE'),50.0-2.5)
        self.assertEqual(seat.pocket(10.0,20.0),(10.0-2.5,10.0+2.5,20.0-2,20.0+4.5/2))
        self.assertEqual(seat.embed_length(12),12/2+4)
        self.assertEqual((seat.BEAM_WIDTH_MM,seat.BEAM_HEIGHT_MM),(4.2,4.5+.2))

    def test_bearing_band(self):
        'IA: La banda del ensayo de daño queda entre 4,5 y 2,7 mm bajo el eje, bordes excluidos.'
        z=30.0
        self.assertTrue(seat.bearing_overlap(z-5,z-3,z))
        self.assertFalse(seat.bearing_overlap(z-2.7,z,z))
        self.assertFalse(seat.bearing_overlap(z-9,z-4.5,z))

    def test_rays_inside_band_and_pocket(self):
        'IA: Los rayos del constructor caen en la banda de piedra y dentro del ancho del alojamiento.'
        x0,x1,_,_=seat.pocket(0.0,30.0)
        for x,z in seat.samples(0.0,30.0):
            self.assertTrue(x0<x<x1)
            self.assertTrue(30.0+seat.BEARING_BAND_MM[0]<=z<=30.0+seat.BEARING_BAND_MM[1])

    def test_plan_seat_from_geometry(self):
        'IA: El plan toma ancho de viga y profundidad igual al grosor atravesado; grosor nulo se rechaza.'
        values=seat.plan_seat(12)
        self.assertEqual(values,{'seat_width_mm':4.2,'seat_depth_mm':12.0})
        model=floor_frame.beam_skeleton({'x_mm':0,'ordinal':0},[(2,50)],{'front':0,'back':100},**values,margin_world_mm=30,min_seat_world_mm=120,model_scale=60)
        contact=next(r for r in model['relations'] if r['kind']=='SUPPORTED_BY')['contacts'][0]
        self.assertEqual(contact['seat_mm'],720)
        with self.assertRaises(ValueError):seat.plan_seat(0)


if __name__=='__main__':
    unittest.main()
