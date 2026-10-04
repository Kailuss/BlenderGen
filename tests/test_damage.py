"""Contrato de compatibilidad y conservación del interruptor de daño."""
from types import SimpleNamespace
import unittest
from ruinas_panel.structure.damage import effective_settings, DISABLED_VALUES


class DamageTests(unittest.TestCase):
    def test_legacy_and_enabled(self):
        """IA: Un archivo antiguo o daño activo conserva exactamente el objeto de ajustes."""
        p=SimpleNamespace(collapse=.8)
        self.assertIs(effective_settings(p),p)
        p.damage_enabled=True
        self.assertIs(effective_settings(p),p)

    def test_disabled_preserves_source(self):
        """IA: Apagar neutraliza todos los daños sin modificar semillas, calidad ni valores originales."""
        p=SimpleNamespace(damage_enabled=False,seed=12,preview_quality='DETAIL',collapse=.8)
        view=effective_settings(p)
        for name,value in DISABLED_VALUES.items():
            self.assertEqual(getattr(view,name),value)
        self.assertEqual(view.seed,12)
        self.assertEqual(view.preview_quality,'DETAIL')
        self.assertEqual(p.collapse,.8)
