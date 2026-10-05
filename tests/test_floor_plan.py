"""Reglas de habitación útil y circulación de 35 mm."""
from types import SimpleNamespace
import unittest
from ruinas_panel.structure import floor_plan


class FloorPlanTests(unittest.TestCase):
    def test_connected_rooms(self):
        'IA: Todos los cuartos alcanzables y útiles de 60×60; distribuidor de 35 mm fuera de escalera.'
        for mode,count in (('TWO',2),('THREE',3)):
            p=SimpleNamespace(interior_layout=mode,layout_mode='ROOM',height=112)
            plan=floor_plan.plan(p,(-110,110,5,205),{'left':-19,'right':19},{'y0':178})
            self.assertEqual(len(plan['rooms']),count)
            reached={plan['entry_room']}
            for _ in range(count):
                for a,b in plan['connections']:
                    if a in reached or b in reached:reached.update((a,b))
            self.assertEqual(reached,{r['id'] for r in plan['rooms']})
            for room in plan['rooms']:
                a,b,c,d=room['bounds'];minimum=60 if room['kind']=='room' else 35
                self.assertGreaterEqual(min(b-a,d-c),minimum)
            self.assertEqual(plan['door_width'],35)
            self.assertLess(plan['partitions'][0]['fixed']+1.5,178)

    def test_small_building_rejected(self):
        'IA: Umbral 80×80 y división imposible no generan habitaciones estrechas.'
        p=SimpleNamespace(interior_layout='TWO',layout_mode='ROOM',height=57)
        for bounds in ((0,80,0,80),(0,90,0,90),(0,122,0,100)):
            self.assertIn('error',floor_plan.plan(p,bounds))
        plan=floor_plan.plan(p,(0,123,0,100))
        self.assertEqual(plan['partitions'][0]['axis'],'y')
