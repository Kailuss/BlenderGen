"""Reglas puras de cotas, reparto y posiciones manuales."""
import unittest
from types import SimpleNamespace
from ruinas_panel.structure import layout


class ConstructionRules(unittest.TestCase):
    def test_independent_levels(self):
        'IA: Entreplanta y coronación coinciden con las hiladas, también con plantas desiguales.'
        p=SimpleNamespace(height_type='TWO',ground_storey_height=65,upper_storey_height=42,stone_size=6,alternate_height=.7)
        edges,_=layout.course_layout(p)
        self.assertIn(67,edges);self.assertEqual(edges[-1],109);self.assertEqual(layout.building_height(p),109)

    def test_spacing(self):
        'IA: Un tramo libre no concentra las tres ventanas al principio; un obstáculo mantiene separación y distribución.'
        self.assertEqual(layout.spread_positions(range(0,101,5),3,0,100,20),[25,50,75])
        xs=layout.spread_positions([x for x in range(0,101,5) if not 40<=x<=60],3,0,100,20)
        self.assertGreaterEqual(xs[-1]-xs[0],50)
        self.assertTrue(all(b-a>=20 for a,b in zip(xs,xs[1:])))

    def test_manual_pillars(self):
        'IA: Las posiciones explícitas se respetan y los conflictos de puerta se rechazan antes de construir.'
        p=SimpleNamespace(length=200,pillar_count=3,pillar_width=12,pillar_distribution='CUSTOM',pillar_positions='20;50;80',lock_distribution=False,seed=17,left_turn='NONE',right_turn='NONE',connection_enabled=False)
        for actual,expected in zip([x for x,w in layout.pillar_layout(p,None,6)],[-60,0,60]):self.assertAlmostEqual(actual,expected)
        with self.assertRaises(ValueError):layout.pillar_layout(p,{'left':-20,'right':20},6)


if __name__=='__main__':unittest.main()
