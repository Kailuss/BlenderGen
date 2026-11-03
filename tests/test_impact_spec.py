"""Contratos de unidades y transferencia de energía del banco de impacto."""
import math
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from ruinas_panel.services import impact_spec


class ImpactSpecTests(unittest.TestCase):
    """Magnitudes auditables sin bpy ni valores ocultos de material."""

    def test_invariant_world_size(self):
        """IA: Igual radio y velocidad de mundo a escalas 30/60 produce igual masa y energía."""
        a=impact_spec.projectile(.02,2200,.4,60,10000,1,100000)
        b=impact_spec.projectile(.04,2200,.8,30,10000,1,100000)
        self.assertAlmostEqual(a['mass_world_kg'],b['mass_world_kg'])
        self.assertAlmostEqual(a['surrogate_energy_world_j'],b['surrogate_energy_world_j'])

    def test_thin_mass(self):
        """IA: La masa fina depende de área por espesor real, no de una malla imprimible."""
        self.assertAlmostEqual(impact_spec.thin_mass(.2,.01,1800),3.6)

    def test_invalid_values(self):
        """IA: Rechaza unidades numéricas imposibles y velocidad superior al máximo."""
        for density in (0,-1,math.nan,math.inf):
            with self.assertRaises(ValueError):
                impact_spec.projectile(.02,density,.8,60,10000,1,1000)
        with self.assertRaises(ValueError):
            impact_spec.projectile(.02,2200,2,60,10000,1,1000)

    def test_budget_is_not_universal(self):
        """IA: Demuestra que eta 0,3 no es límite universal para masas iguales y e=0,3."""
        result=impact_spec.central_collision(1,1,1,.3)
        self.assertAlmostEqual(result['eta'],.4225)
        self.assertAlmostEqual(result['projectile_speed']+result['target_speed'],1)

    def test_explicit_dissipation(self):
        """IA: El barrido conserva momento y energía contabilizando la disipación adicional necesaria para eta<=0,3."""
        for mass in (.1,1,10):
            for restitution in (.1,.3):
                r=impact_spec.dissipative_collision(mass,1,10,restitution)
                self.assertLessEqual(r['eta'],.3+1e-12)
                self.assertAlmostEqual(mass*r['projectile_speed']+r['target_speed'],mass*10)
                self.assertAlmostEqual(r['energy_initial'],r['energy_final']+r['energy_dissipated'])
                self.assertGreaterEqual(r['additional_dissipation'],0)
        self.assertGreater(impact_spec.dissipative_collision(1,1,10,.3)['additional_dissipation'],0)

    def test_impossible_internal_budget(self):
        """IA: No inventa impulso externo para cumplir un presupuesto menor que el choque completamente inelástico."""
        with self.assertRaises(ValueError):
            impact_spec.dissipative_collision(1,1,10,.3,.1)

    def test_contact_regime_scale_invariant(self):
        """IA: El régimen depende de avance/radio: escalar velocidad y radio por 100 no lo cambia."""
        a=impact_spec.contact_regime(.8,.005,24,160)
        b=impact_spec.contact_regime(80,.5,24,160)
        self.assertAlmostEqual(a['step_ratio'],b['step_ratio'])
        self.assertEqual(a['resolved'],b['resolved'])
        self.assertEqual(a['substeps_required'],b['substeps_required'])

    def test_contact_regime_threshold(self):
        """IA: Resuelto con razón <= 0,025 y pareja convexa; fuera, restitución desconocida (None), nunca 0."""
        ok=impact_spec.contact_regime(10*.02*4800/1,10,120,40)
        self.assertTrue(ok['resolved']);self.assertEqual(ok['restitution_effective'],0.);self.assertEqual(ok['eta_bound'],.25)
        fast=impact_spec.contact_regime(10*.04*4800,10,120,40)
        self.assertFalse(fast['resolved']);self.assertIsNone(fast['restitution_effective']);self.assertIsNone(fast['eta_bound'])
        self.assertLessEqual(impact_spec.contact_regime(10*.04*4800,10,120,fast['substeps_required'])['step_ratio'],.025+1e-12)

    def test_contact_regime_unsupported_pair(self):
        """IA: Parejas de primitivas o malla nunca se declaran resueltas, aunque el paso sea mínimo."""
        for shapes in (('SPHERE','SPHERE'),('BOX','BOX'),('MESH','CONVEX_HULL')):
            r=impact_spec.contact_regime(.001,1,120,400,shapes=shapes)
            self.assertFalse(r['resolved']);self.assertIsNone(r['substeps_required'])

    def test_inelastic_budget(self):
        """IA: En régimen resuelto eta <= 0,25 para cualquier razón de masas y se conserva el momento."""
        for mass in (.01,.1,1,10,100):
            r=impact_spec.inelastic_collision(mass,1,10)
            self.assertLessEqual(r['eta'],.25+1e-12)
            self.assertAlmostEqual(mass*r['projectile_speed']+r['target_speed'],mass*10)
            self.assertAlmostEqual(r['energy_initial'],r['energy_final']+r['energy_dissipated'])
        self.assertAlmostEqual(impact_spec.inelastic_collision(1,1,10)['eta'],.25)


if __name__ == '__main__':
    unittest.main()
