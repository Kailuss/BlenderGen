"""Coherencia de la API visible: secciones, ajustes guardados, operadores y registro, sin bpy."""
import ast
import importlib.util
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT/'src/ruinas_panel'


def load_config():
    """IA: Carga config.py como módulo aislado (no importa bpy) para leer SECTIONS y HIDDEN_FIELDS."""
    spec = importlib.util.spec_from_file_location('ruinas_config_isolated', PKG/'config.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def settings_fields():
    """IA: Nombres de las propiedades anotadas en RuinSettings, leídos del árbol sintáctico."""
    tree = ast.parse((PKG/'ui/settings.py').read_text(encoding='utf8'))
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'RuinSettings')
    return [n.target.id for n in cls.body if isinstance(n, ast.AnnAssign)]


def operator_ids():
    """IA: bl_idname de cada clase de operador en ui/operators.py, por nombre de clase."""
    tree = ast.parse((PKG/'ui/operators.py').read_text(encoding='utf8'))
    found = {}
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, ast.Assign) and any(getattr(t, 'id', None) == 'bl_idname' for t in item.targets):
                    found[node.name] = item.value.value
    return found


class ApiLayoutTests(unittest.TestCase):
    """El panel, los ajustes y los operadores no se contradicen."""

    def setUp(self):
        """IA: Lee config, ajustes, panel y registro una vez por prueba."""
        self.config = load_config()
        self.fields = settings_fields()
        self.panel = (PKG/'ui/panel.py').read_text(encoding='utf8')
        self.registration = (PKG/'registration.py').read_text(encoding='utf8')
        self.strength = (PKG/'services/material_strength.py').read_text(encoding='utf8')

    def test_sections_reference_real_fields_once(self):
        """IA: Cada campo de sección existe en RuinSettings y aparece en una sola sección; los ids son únicos."""
        seen = {}
        for section in self.config.SECTIONS:
            for field in section['fields'] + ((section['toggle'],) if 'toggle' in section else ()):
                self.assertIn(field, self.fields, section['id'])
                self.assertNotIn(field, seen, f"{field} en {section['id']} y {seen.get(field)}")
                seen[field] = section['id']
        ids = [s['id'] for s in self.config.SECTIONS]
        self.assertEqual(len(ids), len(set(ids)))

    def test_every_setting_is_shown_or_declared_hidden(self):
        """IA: Ningún ajuste guardado queda huérfano: o se dibuja, o figura en HIDDEN_FIELDS con motivo; y lo oculto existe."""
        shown = {f for s in self.config.SECTIONS for f in s['fields']} | {s['toggle'] for s in self.config.SECTIONS if 'toggle' in s}
        shown |= set(re.findall(r"'([a-z_]+)'", self.panel)) | set(re.findall(r"'(physics_\w+_strength)'", self.strength))
        orphans = [f for f in self.fields if f not in shown and f not in self.config.HIDDEN_FIELDS]
        self.assertEqual(orphans, [])
        self.assertEqual([f for f in self.config.HIDDEN_FIELDS if f not in self.fields], [])

    def test_panel_operators_exist_and_are_registered(self):
        """IA: Cada operador dibujado existe, y cada clase de operador está registrada (y viceversa)."""
        ids = operator_ids()
        drawn = set(re.findall(r"operator\(\s*'(ruin\.[a-z_]+)'", self.panel))
        self.assertEqual(sorted(drawn - set(ids.values())), [])
        registered = set(re.findall(r'operators\.(RUIN_OT_\w+)', self.registration))
        self.assertEqual(sorted(set(ids) - registered), [])
        self.assertEqual(sorted(registered - set(ids)), [])

    def test_no_removed_features(self):
        """IA: El zarandeo se retiró (2026-11-03): ni operador, ni ajuste, ni modo de trabajador."""
        for path in PKG.rglob('*.py'):
            text = path.read_text(encoding='utf8')
            self.assertNotIn('SHAKE', text, path)
            self.assertNotIn('shake_physics', text, path)


if __name__ == '__main__':
    unittest.main()
