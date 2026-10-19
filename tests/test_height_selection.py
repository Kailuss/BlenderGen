"""Porcentaje exacto y gradiente reproducible sin depender de Blender."""
import unittest
from ruinas_panel.services.height_selection import ranked,regional


class HeightSelectionTests(unittest.TestCase):
    def test_local_zone(self):
        'IA: La zona excluye piezas exteriores, selecciona primero las cercanas y mantiene selecciones anidadas al subir el porcentaje.'
        records=[(str(i),(i,0,0)) for i in range(10)]
        small,count=regional(records,(0,0,0),(4,1,1),40)
        large,_=regional(list(reversed(records)),(0,0,0),(4,1,1),100)
        self.assertEqual(count,5);self.assertEqual(small,['0','1'])
        self.assertEqual(large,['0','1','2','3','4'])
        self.assertTrue(set(small)<=set(large))
        self.assertEqual(regional(records,(0,9,0),(4,1,1),100),([],0))
        with self.assertRaises(ValueError):regional(records,(0,0,0),(0,1,1),100)

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
