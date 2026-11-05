"""Torreón, paso 6: forjados sobre ménsulas y escalera de caracol volada (sin Blender)."""
import math
import unittest
from ruinas_panel.structure import tower_plan as tp
from ruinas_panel.structure import tower_floors as tf

CASES=(('ROUND',40,6),('ROUND',60,10),('ROUND',100,10),('SQUARE',40,6),('SQUARE',56,12),('SQUARE',100,10))


def build(shape,size,thickness,seed=7,floors=3,terrace=True):
    'IA: Plan intacto con interior para un caso de prueba.'
    geo=tf.geometry(shape,size,thickness)
    parapet=tf.PARAPET_COURSES if terrace else 0
    plan=(tp.round_plan(size/2,thickness,120,6.5,seed=seed,slits=3,floors=floors,parapet=parapet) if shape=='ROUND'
          else tp.square_plan(size,thickness,120,6.5,seed=seed,slits=1,floors=floors,parapet=parapet))
    frames,steps=tf.interior(geo,plan,floors,terrace)
    return geo,plan,frames,steps


def inside_step(geo,step,x,y,z):
    'IA: Comprobación independiente: punto estrictamente dentro del volumen de un peldaño (arco, banda y altura).'
    if not step['z0']+1e-6<z<step['z1']-1e-6:return False
    theta=math.atan2(y,x);r=math.hypot(x,y)
    if (theta-step['a0'])%(2*math.pi)>=step['a1']-step['a0']:return False
    scale=1. if geo['shape']=='ROUND' else 1/max(abs(math.cos(theta)),abs(math.sin(theta)))
    return (geo['inner']-step['depth'])*scale<r<geo['inner']*scale


def box_points(x0,x1,y0,y1,z0,z1,n=6):
    'IA: Puntos interiores de una caja (sin tocar sus caras) para buscar choques.'
    e=.05   # un contacto de menos de dos píxeles de impresión se funde al exportar
    for i in range(n):
        for j in range(n):
            for k in range(3):
                yield (x0+e+(x1-x0-2*e)*i/(n-1),y0+e+(y1-y0-2*e)*j/(n-1),z0+e+(z1-z0-2*e)*k/2)


class TowerFloorsTests(unittest.TestCase):
    def test_stair_continuous_turn_per_floor(self):
        'IA: La hélice sube sin saltos, cada peldaño monta sobre el anterior, cada tramo acaba en su piso y los de planta dan una vuelta.'
        for shape,size,t in CASES:
            geo,plan,frames,steps=build(shape,size,t)
            tops=[f[0]['top'] for f in frames]
            for a,b in zip(steps,steps[1:]):
                self.assertAlmostEqual(a['z1'],b['z0'],places=9)
                self.assertGreater(a['a1']-b['a0'],.1*(b['a1']-b['a0']))
            for f,top in enumerate(tops):
                flight=[s for s in steps if s['flight']==f]
                self.assertAlmostEqual(flight[-1]['z1'],top,places=9)
                if frames[f][0]['terrace']:continue
                self.assertAlmostEqual(flight[-1]['a0']+(flight[-1]['a1']-flight[-1]['a0'])/(1+tf.STEP_OVERLAP)-flight[0]['a0'],2*math.pi,places=6)

    def test_beams_seated_on_corbels_in_plan(self):
        'IA: Cada viga entrega al menos MIN_SEAT_MM y sus dos ménsulas están en el plan de la hilada; desde 56 mm hay al menos dos vigas por forjado.'
        for shape,size,t in CASES:
            geo,plan,frames,steps=build(shape,size,t)
            for lv,beams,boards,_ in frames:
                # La torre circular de 40 mm (radio interior 14) no tiene sitio para viga y escalera en todas las plantas.
                if size>=56:self.assertGreaterEqual(len(beams),2,(shape,size))
                course=plan[lv['corbel_row']]
                for b in beams:
                    self.assertGreaterEqual(tf.beam_seat(geo,*b['y']),tf.MIN_SEAT_MM-1e-9)
                    self.assertTrue(tf.corbel_alive(geo,course,b['id']),(shape,size,b['id']))
                for board in boards:
                    self.assertTrue(tf.supports(board,beams))

    def test_round_corbel_course_closes(self):
        'IA: En la circular, la hilada de ménsulas sigue cerrando la vuelta sin solapes (piedras + ménsulas + saeteras = 2π).'
        for shape,size,t in CASES:
            if shape!='ROUND':continue
            geo,plan,frames,steps=build(shape,size,t)
            for lv,*_ in frames:
                course=plan[lv['corbel_row']]
                arcs=sorted((a%(2*math.pi),a%(2*math.pi)+b-a) for a,b in course['stones']+course['slits'])
                self.assertAlmostEqual(sum(b-a for a,b in arcs),2*math.pi,places=6)
                for (a,b),(c,d) in zip(arcs,arcs[1:]):self.assertLessEqual(b,c+1e-9)

    def test_square_corbel_course_no_overlap(self):
        'IA: En la cuadrada, ménsulas y piedras de la hilada no se solapan y la ménsula vuela hacia dentro.'
        for shape,size,t in CASES:
            if shape!='SQUARE':continue
            geo,plan,frames,steps=build(shape,size,t)
            for lv,*_ in frames:
                stones=plan[lv['corbel_row']]['stones']
                for i,s in enumerate(stones):
                    for u in stones[i+1:]:
                        area=max(0.,min(s['x'][1],u['x'][1])-max(s['x'][0],u['x'][0]))*max(0.,min(s['y'][1],u['y'][1])-max(s['y'][0],u['y'][0]))
                        self.assertLess(area,1e-9,(s,u))
                corbels=[s for s in stones if s.get('corbels')]
                self.assertTrue(corbels)
                self.assertTrue(all(min(abs(s['x'][0]),abs(s['x'][1]))<geo['inner']-1 for s in corbels))

    def test_timber_clear_of_stair(self):
        'IA: Comprobación independiente: ningún punto interior de viga, tabla o ménsula cae dentro de un peldaño.'
        for shape,size,t in CASES:
            geo,plan,frames,steps=build(shape,size,t)
            for lv,beams,boards,tiles in frames:
                near=[s for s in steps if s['z1']>lv['corbel_z0'] and s['z0']<lv['top']]
                boxes=[(b['x'][0],b['x'][1],b['y'][0],b['y'][1],lv['beam_z0'],lv['beam_z1']) for b in beams]
                boxes+=[(t['x'][0],t['x'][1],t['y'][0],t['y'][1],lv['beam_z1'],lv['board_top']) for t in boards]
                boxes+=[(t['x'][0],t['x'][1],t['y'][0],t['y'][1],lv['board_top'],lv['top']) for t in tiles]
                for box in boxes:
                    for p in box_points(*box):
                        self.assertFalse(any(inside_step(geo,s,*p) for s in near),(shape,size,box,p))

    def test_floor_covers_most_of_interior(self):
        'IA: Desde 56 mm, el forjado intacto cubre al menos el 35 % de la planta interior (el resto es hueco de escalera y bordes).'
        for shape,size,t in CASES:
            geo,plan,frames,steps=build(shape,size,t)
            area=math.pi*geo['inner']**2 if shape=='ROUND' else (2*geo['inner'])**2
            for lv,_,boards,_ in frames:
                cover=sum((b['x'][1]-b['x'][0])*(b['y'][1]-b['y'][0]) for b in boards)/area
                if size>=56:self.assertGreater(cover,.35,(shape,size,lv['floor']))

    def test_ruin_keeps_only_supported(self):
        'IA: Tras la ruina, toda viga conserva sus ménsulas, toda tabla dos vigas vivas y todo peldaño el anterior y muro detrás; con mucha ruina se pierde algo.'
        lost_any=False
        for shape,size,t in CASES:
            for seed in (1,7,13):
                geo,plan,frames,steps=build(shape,size,t,seed=seed)
                ruin=(tp.ruin_round if shape=='ROUND' else tp.ruin_square)
                for amount in (.3,.8):
                    kept_plan=ruin(plan,120,seed=seed,amount=amount)[0]
                    kept,alive,lost=tf.settle(geo,kept_plan,frames,steps)
                    lost_any=lost_any or any(lost.values())
                    for lv,beams,boards,tiles in kept:
                        for b in beams:self.assertTrue(tf.corbel_alive(geo,kept_plan[lv['corbel_row']],b['id']))
                        for board in boards:self.assertTrue(tf.supports(board,beams))
                        for slab in tiles:self.assertGreaterEqual(tf.bearing(slab,boards),tf.SLAB_BEARING)
                    for s in alive:self.assertGreaterEqual(tf.wall_behind(geo,kept_plan,s),tf.WALL_BEHIND)
                    ids=[(s['flight'],s['index']) for s in alive]
                    self.assertEqual(ids,[(s['flight'],s['index']) for s in steps[:len(alive)]])
        self.assertTrue(lost_any)

    def test_terrace_under_parapet(self):
        'IA: La terraza queda PARAPET_COURSES hiladas bajo la coronación, la escalera llega a su piso de losas y las losas cubren al menos el 25 % de la planta.'
        for shape,size,t in CASES:
            geo,plan,frames,steps=build(shape,size,t)
            lv,beams,boards,tiles=frames[-1]
            self.assertTrue(lv['terrace'])
            self.assertEqual(len(plan)-lv['corbel_row']-1,tf.PARAPET_COURSES)
            self.assertAlmostEqual(steps[-1]['z1'],lv['top'],places=9)
            area=math.pi*geo['inner']**2 if shape=='ROUND' else (2*geo['inner'])**2
            cover=sum((s['x'][1]-s['x'][0])*(s['y'][1]-s['y'][0]) for s in tiles)/area
            self.assertGreater(cover,.25,(shape,size,cover))
            for s in tiles:self.assertTrue(tf.inside(geo,s['x'][0],s['x'][1],s['y'][0],s['y'][1]))
            self.assertFalse(any(f[0]['terrace'] for f in build(shape,size,t,terrace=False)[2]))

    def test_single_floor_has_no_interior(self):
        'IA: Con una sola planta no hay forjados ni escalera.'
        geo,plan,frames,steps=build('ROUND',60,10,floors=1,terrace=False)
        self.assertEqual((frames,steps),([],[]))


if __name__=='__main__':unittest.main()
