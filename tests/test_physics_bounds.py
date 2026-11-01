"""Regresión: caer fuera del suelo finito no equivale a atravesarlo."""
import unittest
from ruinas_panel.services.physics_bounds import below_floor


def box(lo, hi):
    'IA: Devuelve las ocho esquinas de una caja para comprobar huellas y cotas.'
    return tuple((x,y,z) for x in (lo[0],hi[0]) for y in (lo[1],hi[1]) for z in (lo[2],hi[2]))


class SafetyFloorTests(unittest.TestCase):
    def test_finite_floor_and_scale(self):
        'IA: Mantiene el rechazo dentro y en bordes parcialmente solapados; acepta exterior, contacto y altura superior a escalas 1 y 100.'
        cases=[((-0.08,.38,-.004),(-.07,.39,-.003),True),
               ((-5.51,.04,-.03),(-5.48,.06,-.01),False),
               ((4.99,0,-.03),(5.01,.02,-.01),True),
               ((5,0,-.03),(5.02,.02,-.01),False),
               ((0,5.2,-.03),(.02,5.3,-.01),False),
               ((0,0,0),(.02,.02,.01),False),
               ((0,0,-.002),(.02,.02,-.0015),False)]
        for factor in (1,100):
            floor=box((-5*factor,-4.886*factor,-.501*factor),(5*factor,5.114*factor,-.001*factor))
            for lo,hi,expected in cases:
                with self.subTest(factor=factor,lo=lo):
                    points=box(tuple(v*factor for v in lo),tuple(v*factor for v in hi))
                    self.assertEqual(below_floor(points,floor,.001*factor),expected)
