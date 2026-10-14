"""Porcentaje exacto y gradiente reproducible sin depender de Blender."""
import unittest
from ruinas_panel.services.height_selection import ranked


class HeightSelectionTests(unittest.TestCase):
    def test_count_and_seed(self):
        'IA: Cumple extremos, porcentaje redondeado y semilla sin depender del orden de entrada.'
        records=[(str(i),i) for i in range(100)]
        chosen=ranked(records,27,.7,17)
        self.assertEqual(len(set(chosen)),27)
        self.assertEqual(chosen,ranked(list(reversed(records)),27,.7,17))
        self.assertEqual(ranked(records,0,.7,17),[])
        self.assertEqual(len(ranked(records,100,.7,17)),100)
        self.assertEqual(ranked([],50,.7,17),[])

    def test_height_preference(self):
        'IA: El gradiente eleva la altura media sin convertirse en un corte horizontal fijo.'
        records=[(str(i),i) for i in range(1000)]
        uniform=ranked(records,20,0,17);upper=ranked(records,20,1,17)
        self.assertGreater(sum(map(int,upper))/len(upper),sum(map(int,uniform))/len(uniform)+150)
        self.assertLess(min(map(int,upper)),500)


if __name__=='__main__':unittest.main()
