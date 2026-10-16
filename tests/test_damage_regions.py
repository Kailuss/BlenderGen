"""Contorno único y semillas independientes del detalle geométrico."""
import unittest
from ruinas_panel.structure import damage_regions as regions


class RegionTests(unittest.TestCase):
    def test_seed_and_asymmetry(self):
        'IA: Dos eventos no espejados y deterministas; cambiar la semilla de daño cambia solo el plan de daño.'
        a=regions.roof_events(17,0,.85,(-100,100,0,160))
        self.assertEqual(a,regions.roof_events(17,0,.85,(-100,100,0,160)))
        self.assertNotEqual(a,regions.roof_events(17,1,.85,(-100,100,0,160)))
        self.assertGreater(abs(a[0]['y']-a[1]['y']),20)
        self.assertNotAlmostEqual(a[0]['x'],-a[1]['x'])
        self.assertEqual(regions.roof_events(17,0,0,(-100,100,0,160)),[])

    def test_support_intersections(self):
        'IA: Los extremos recortados coinciden con el contorno que elimina tejas; ningún tramo conservado atraviesa el núcleo.'
        for seed in range(10):
            events=regions.roof_events(seed,3,.85,(-100,100,0,160))
            for event in events:
                self.assertTrue(regions.broken(event['x'],event['y'],events))
                spans=regions.segments(-100,100,event['y'],events,'x')
                self.assertTrue(spans)
                for a,b in spans:
                    for step in range(1,100):self.assertFalse(regions.broken(a+(b-a)*step/100,event['y'],events))
                early=regions.roof_events(seed,3,.35,(-100,100,0,160))
                self.assertEqual(regions.segments(-100,100,event['y'],early,'x'),[(-100,100)])
