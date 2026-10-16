"""Identidad arquitectónica independiente de la enumeración global de vanos."""
import unittest
from ruinas_panel.structure import building_definition


class BuildingGraphTests(unittest.TestCase):
    def test_facade_slots_stay_stable(self):
        'IA: Añadir un vano en otra fachada no renumera los existentes y la terraza no declara tejas inexistentes.'
        definition={'levels':[{'id':'floor.0'},{'id':'floor.1'}],'roof_type':'TOWER'}
        walls=[{'id':'front'},{'id':'back'}];back={'wall':'back','floor':1,'balcony':True}
        first=building_definition.graph(definition,walls,{},[back],[],True)
        second=building_definition.graph(definition,walls,{},[{'wall':'front','floor':0,'balcony':False},back],[],True)
        a=next(n['id'] for n in first['nodes'] if n.get('balcony'))
        b=next(n['id'] for n in second['nodes'] if n.get('balcony'))
        self.assertEqual(a,b);self.assertNotIn('tiles',{n['id'] for n in second['nodes']})
