"""Esqueleto D1 de una viga con daño localizado por segmento."""
import unittest
from ruinas_panel.structure import floor_frame
from ruinas_panel.construction_core import graph


class FloorFrameTests(unittest.TestCase):
    def test_axis_matching_and_empty(self):
        'IA: Juntas sin pareja quedan informadas; cada pareja usa ambas paredes una sola vez.'
        result=floor_frame.aligned_axes([(0,8),(10,8)],[(.2,8),(30,8)],.5)
        self.assertEqual(len(result['axes']),1)
        self.assertEqual(len(result['discarded_axes']),2)
        self.assertTrue(floor_frame.aligned_axes([(0,8)],[(3,8)],.5)['errors'])

    def test_segment_loss_is_local(self):
        'IA: Perder asiento superior elimina su viga sin eliminar muro padre, otra columna ni base inferior.'
        model=floor_frame.beam_skeleton({'x_mm':-20,'ordinal':0},[(2,25),(25,50)],{'front':0,'back':100},4.2,3,30,120,60)
        result=graph.loss(model,['seg.front.1.0'])
        self.assertEqual(result['unsupported'],[model['beam_id']])
        self.assertEqual(result['requires_review'],[])
        self.assertEqual(model['segment_count'],4)
        result=graph.loss(model,['seg.front.0.0'])
        self.assertEqual(result['unsupported'],['beam.2.0','seg.front.1.0'])

    def test_insufficient_seat(self):
        'IA: Rechaza un asiento inferior al mínimo explícito sin inventar relación de apoyo.'
        with self.assertRaises(ValueError):
            floor_frame.beam_skeleton({'x_mm':0,'ordinal':0},[(2,50)],{'front':0,'back':100},4.2,1,30,120,60)
