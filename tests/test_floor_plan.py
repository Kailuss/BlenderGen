"""Reglas mínimas de circulación y reservas del plano interior."""
from types import SimpleNamespace
import unittest
from ruinas_panel.structure import floor_plan


class FloorPlanTests(unittest.TestCase):
    def test_connected_rooms(self):
        'IA: Todos los cuartos son alcanzables desde el acceso, sin mover la puerta exterior.'
        for mode,count in (('TWO',2),('THREE',3)):
            p=SimpleNamespace(interior_layout=mode,layout_mode='ROOM',height=112)
            plan=floor_plan.plan(p,(-80,80,5,115),{'left':-12,'right':12},{'y0':88})
            self.assertEqual(len(plan['rooms']),count)
            reached={plan['entry_room']}
            for _ in range(count):
                for a,b in plan['connections']:
                    if a in reached or b in reached:reached.update((a,b))
            self.assertEqual(reached,{r['id'] for r in plan['rooms']})
            self.assertLess(plan['partitions'][0]['fixed']+1.5,88)
            self.assertEqual(plan['door_width'],25)
            self.assertTrue(floor_plan.window_blocked(plan,'left',50,70))

    def test_small_building_rejected(self):
        'IA: Una distribución que no cabe explica el límite, en vez de producir cuartos estrechos.'
        p=SimpleNamespace(interior_layout='THREE',layout_mode='ROOM',height=57)
        self.assertIn('error',floor_plan.plan(p,(-25,25,0,50)))
