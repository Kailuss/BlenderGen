"""Torreón: aparejo puro de torre circular y cuadrada."""
import math
import unittest
from ruinas_panel.structure import tower_plan as tp


class TowerPlanTests(unittest.TestCase):
    def test_courses_exact(self):
        'IA: Las hiladas suman la altura exacta y ninguna baja de 3 mm.'
        rows=tp.courses(121.3,6.5)
        self.assertAlmostEqual(rows[-1][1],121.3)
        self.assertTrue(all(b-a>=3 for a,b in rows))

    def test_round_closed_and_staggered(self):
        'IA: Cada hilada circular cierra la vuelta (piedras + saeteras) y sus juntas caen lejos de las de la hilada inferior.'
        plan=tp.round_plan(30,10,120,6.5,seed=3,slits=4,floors=3)
        r_mid=25.
        for course in plan:
            arcs=sum(b-a for a,b in course['stones'])+sum(b-a for a,b in course['slits'])
            self.assertAlmostEqual(arcs,2*math.pi,places=6)
            self.assertTrue(all((b-a)*r_mid>=tp.MIN_STONE_MM-1e-9 for a,b in course['stones']))
        pitch=2*math.pi/tp.ring_count(r_mid,plan[0]['z1']-plan[0]['z0'])
        for low,high in zip(plan,plan[1:]):
            if low['slits'] or high['slits']:continue
            below=[a%(2*math.pi) for a,_ in low['stones']]
            for a,_ in high['stones']:
                gap=min(min(abs(a%(2*math.pi)-b),2*math.pi-abs(a%(2*math.pi)-b)) for b in below)
                self.assertGreater(gap,.25*pitch)

    def test_round_slits_per_floor(self):
        'IA: Cada planta tiene sus saeteras y se giran entre plantas para no apilarlas.'
        plan=tp.round_plan(30,10,120,6.5,seed=3,slits=2,floors=3)
        centres=sorted({round((a+b)/2,6) for c in plan for a,b in c['slits']})
        self.assertGreaterEqual(len(centres),4)

    def test_square_bond(self):
        'IA: Torre cuadrada sin solapes, con el anillo completo cubierto y esquinas que alternan dueño (trabadas).'
        side,t=60.,12.
        plan=tp.square_plan(side,t,120,6.5,seed=3)
        ring=side*side-(side-2*t)**2
        owners=[c['corner_owner'] for c in plan]
        self.assertTrue(all(a!=b for a,b in zip(owners,owners[1:])))
        for course in plan:
            boxes=[(s['x'],s['y']) for s in course['stones']]
            self.assertAlmostEqual(sum((x[1]-x[0])*(y[1]-y[0]) for x,y in boxes),ring,places=6)
            for i,(xa,ya) in enumerate(boxes):
                for xb,yb in boxes[i+1:]:
                    self.assertLessEqual(max(0,min(xa[1],xb[1])-max(xa[0],xb[0]))*max(0,min(ya[1],yb[1])-max(ya[0],yb[0])),1e-9)
            self.assertEqual({s['wall'] for s in course['stones']},{'front','back','left','right'})

    def test_square_slit_removes_area(self):
        'IA: Una saetera resta exactamente su anchura por el grosor del muro en su hilada.'
        side,t=60.,12.
        plain=tp.square_plan(side,t,120,6.5,seed=3);slit=tp.square_plan(side,t,120,6.5,seed=3,slits=1,floors=3)
        area=lambda c:sum((s['x'][1]-s['x'][0])*(s['y'][1]-s['y'][0]) for s in c['stones'])
        diffs=[area(a)-area(b) for a,b in zip(plain,slit)]
        self.assertTrue(any(abs(d-tp.SLIT_WIDTH_MM*t)<1e-6 for d in diffs))
        self.assertTrue(all(abs(d)<1e-6 or abs(d-tp.SLIT_WIDTH_MM*t)<1e-6 for d in diffs))

    def test_square_rows_never_share_joints(self):
        'IA: Dos hiladas seguidas de un mismo muro nunca repiten una junta interior (salvo cerca de las esquinas trabadas).'
        plan=tp.square_plan(56,12,120,6.5,seed=7,variation=0)
        for low,high in zip(plan,plan[1:]):
            joints=lambda c:{round(s['x'][0],3) for s in c['stones'] if s['wall']=='front' and abs(s['x'][0])<16}
            self.assertFalse(joints(low)&joints(high))

    def test_ruin_keeps_support(self):
        'IA: La ruina quita coronación sin dejar piedras sin al menos la mitad apoyada; amount=0 no quita nada.'
        plan=tp.round_plan(30,10,120,6.5,seed=7)
        same,removed=tp.ruin_round(plan,120,seed=7,amount=0)
        self.assertEqual(removed,0)
        ruined,removed=tp.ruin_round(plan,120,seed=7,amount=.4)
        self.assertGreater(removed,0)
        for low,high in zip(ruined,ruined[1:]):
            for a,b in high['stones']:
                self.assertGreaterEqual(tp._angular_support(a,b,low['stones']),.5*(b-a)-1e-9)
        self.assertEqual(len(ruined[0]['stones']),len(plan[0]['stones']))
        sq,removed=tp.ruin_square(tp.square_plan(56,12,120,6.5,seed=7),120,seed=7,amount=.4)
        self.assertGreater(removed,0)

    def test_lost_angles_and_heaps(self):
        'IA: Los ángulos perdidos coinciden con las retiradas y el primer montón cae donde más se perdió.'
        plan=tp.round_plan(30,10,120,6.5,seed=7)
        ruined,removed=tp.ruin_round(plan,120,seed=7,amount=.45)
        angles=tp.lost_angles(plan,ruined)
        self.assertEqual(len(angles),removed)
        heaps=tp.heap_directions(angles)
        self.assertTrue(heaps and heaps[0][1]>=heaps[-1][1])
        sq=tp.square_plan(56,12,120,6.5,seed=7);sr,sremoved=tp.ruin_square(sq,120,seed=7,amount=.45)
        self.assertEqual(len(tp.lost_angles(sq,sr,square=True)),sremoved)

    def test_invalid(self):
        'IA: Rechaza grosores imposibles.'
        with self.assertRaises(ValueError):tp.round_plan(10,12,50,6)
        with self.assertRaises(ValueError):tp.square_plan(20,12,50,6)


if __name__=='__main__':
    unittest.main()
