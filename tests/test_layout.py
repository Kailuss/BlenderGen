"""Invariantes de aparejo y alturas: se ejecutan con Python sin Blender."""
from types import SimpleNamespace
import unittest

from ruinas_panel import config, runtime
from ruinas_panel.structure import layout


class LayoutTests(unittest.TestCase):
    """Contratos físicos de los cálculos puros del generador."""

    def test_courses_fit_storeys(self):
        """IA: preserva altura total, apoyo entre plantas y mínimo de hilada para todos los perfiles."""
        for kind, profile in config.BUILD_TYPES.items():
            for height, top in config.HEIGHT_TYPES.items():
                for variation in (.6,1.,1.4):
                    with self.subTest(kind=kind,height=height,variation=variation):
                        p=SimpleNamespace(height_type=height,stone_size=profile[1],alternate_height=variation)
                        edges,_=layout.course_layout(p)
                        self.assertAlmostEqual(edges[-1],top)
                        self.assertTrue(all(b-a>=3-1e-8 for a,b in zip(edges,edges[1:])))
                        if height=='TWO':self.assertIn(52.,edges)

    def test_thin_stones_keep_gaps(self):
        """IA: fusionar una tira no debe tapar el hueco de una puerta o ventana."""
        result=layout.merge_thin_stones([(0,1),(1,8),(12,20)],3)
        self.assertEqual(result,[(0,8),(12,20)])

    def test_profile_preserves_busy(self):
        """IA: aplicar presets dentro de una operación protegida no debe reactivar callbacks."""
        for busy in (False,True):
            runtime.busy=busy
            p=SimpleNamespace(build_type='WALL',height_type='TWO',layout_mode='ROOM',extra_side='RIGHT',building_depth=50)
            layout.apply_profiles(p)
            self.assertEqual(runtime.busy,busy)
            self.assertEqual((p.height,p.thickness),(102,12))
        runtime.busy=False
