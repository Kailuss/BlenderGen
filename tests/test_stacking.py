"""C5-4: regla pura de apoyo pieza sobre pieza (antes en línea en prune_support)."""
import unittest
from ruinas_panel.construction_core import stacking


def box(key,x0,x1,z0,z1,anchored=False):
    'IA: Caja de prueba de 10 mm de fondo con clave y marca de anclaje.'
    return (key,(x0,0.0,z0),(x1,10.0,z1),anchored)


class StackingTests(unittest.TestCase):
    def test_column_collapses_above_removed(self):
        'IA: Retirar la base de una columna de tres hace caer las dos superiores y su junta.'
        stones=[box('a',0,10,1,6),box('b',0,10,6.5,11.5),box('c',0,10,12,17)]
        mortar=[box('m',0,10,6,6.5)]
        self.assertEqual(stacking.prune(stones,mortar),(['a','b','c'],[]))
        self.assertEqual(stacking.predict(stones,mortar,['a']),['b','c','m'])

    def test_twelve_percent_threshold(self):
        'IA: Un solape algo mayor del 12 % de la huella basta; uno menor no.'
        base=box('a',0,10,1,6)
        self.assertEqual(stacking.prune([base,box('b',8.7,18.7,6.2,11)],[])[1],[])
        self.assertEqual(stacking.prune([base,box('b',8.9,18.9,6.2,11)],[])[1],['b'])

    def test_contact_window(self):
        'IA: La cara superior del apoyo debe quedar entre 1,8 mm bajo y 1,2 mm sobre la base.'
        base=box('a',0,10,1,6)
        self.assertEqual(stacking.prune([base,box('b',0,10,7.8,12)],[])[1],[])
        self.assertEqual(stacking.prune([base,box('b',0,10,7.9,12)],[])[1],['b'])

    def test_anchored_and_ground(self):
        'IA: El dintel anclado y las piezas a ras de suelo se conservan sin apoyo de piedra.'
        self.assertEqual(stacking.prune([box('d',0,10,20,24,True),box('g',30,40,2.5,8)],[])[1],[])

    def test_support_relations(self):
        'IA: Las relaciones informan la fracción de huella apoyada en cada pieza inferior.'
        rel=stacking.support_relations([box('a',0,10,1,6),box('b',5,15,6.5,11)])
        self.assertEqual(rel,[{'source':'b','target':'a','kind':'SUPPORTED_BY','area_fraction':.5}])


if __name__=='__main__':
    unittest.main()
