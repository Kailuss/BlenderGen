"""Dependencias constructivas sin bpy, ni mallas, ni solucionador físico."""
import unittest
from ruinas_panel.construction_core import graph,adapter,schema


def model():
    'IA: Viga sobre tres apoyos con mínimo dos, tablero dependiente y ventana alojada en un apoyo.'
    elements=[{'id':x,'kind':'WALL'} for x in ('a','b','c')]+[{'id':'beam','kind':'BEAM','minimum_supports':2},{'id':'deck','kind':'DECK','minimum_supports':1},{'id':'window','kind':'OPENING'}]
    relations=[{'id':x,'source':'beam','target':x,'kind':'SUPPORTED_BY'} for x in ('a','b','c')]
    relations.extend([{'id':'deck-beam','source':'deck','target':'beam','kind':'SUPPORTED_BY'},{'id':'window-a','source':'window','target':'a','kind':'HOSTED_BY'}])
    return {'elements':elements,'relations':relations}


class ConstructionTests(unittest.TestCase):
    def test_shared_schema_and_mass_units(self):
        'IA: Un litro de madera pesa 0,6 kg reales, sin multiplicadores Bullet; campos de evento e impresión existen también sin malla.'
        beam=schema.element('beam','BEAM',material='wood',volume_mm3=1000000)
        self.assertAlmostEqual(beam['mass_kg'],.6)
        self.assertIsNone(beam['capacity_N']);self.assertIsNone(beam['exposed_area_mm2'])
        self.assertFalse(beam['pozo_de_colapso']);self.assertEqual(beam['print_parts'],[])
        for value in (-1,float('nan'),float('inf')):
            with self.assertRaises(ValueError):schema.element('bad','BEAM',volume_mm3=value)

    def test_schema_supports_and_unknown_measurements(self):
        'IA: No confunde datos desconocidos con cero; detecta relaciones duplicadas en la vista de apoyos y masa escalada accidentalmente.'
        m=adapter.from_nominal({'nodes':[{'id':'a','type':'WALL'},{'id':'b','type':'BEAM'}],'relations':[['a','b','supports']]})
        self.assertEqual(schema.validate(m),[])
        self.assertEqual(m['elements'][1]['rests_on'],['a'])
        m['elements'][1]['rests_on']=[]
        self.assertIn('DIVERGENT_SUPPORTS',{x['code'] for x in schema.validate(m)})
        m['elements'][0]=schema.element('a','WALL',material='stone',volume_mm3=1000000)
        m['elements'][0]['mass_kg']*=10000
        self.assertIn('INCONSISTENT_MASS',{x['code'] for x in schema.validate(m)})

    def test_redundant_support_and_cascade(self):
        'IA: Un apoyo perdido no derrumba una viga redundante; dos pérdidas propagan al tablero, nunca al vano por alojamiento.'
        m=model();self.assertEqual(graph.validate(m),[])
        self.assertEqual(graph.loss(m,['a'])['unsupported'],[])
        self.assertEqual(graph.loss(m,['a','b'])['unsupported'],['beam','deck'])
        self.assertEqual(graph.affected(m,['a'])['dirty'],['a','beam','deck','window'])
        sequence,_=graph.order(m)
        self.assertLess(sequence.index('a'),sequence.index('beam'));self.assertLess(sequence.index('beam'),sequence.index('deck'))

    def test_unknown_policy_and_duplicate_contact(self):
        'IA: Varias relaciones al mismo apoyo no cuentan como apoyos independientes; política desconocida exige revisión.'
        m=model();m['relations'].append(dict(m['relations'][0],id='second-contact'))
        self.assertEqual(graph.loss(m,['b','c'])['unsupported'],['beam','deck'])
        del m['elements'][3]['minimum_supports']
        result=graph.loss(m,['a','b','c'])
        self.assertEqual(result['unsupported'],[]);self.assertEqual(result['requires_review'],['beam'])

    def test_invalid_and_cycles(self):
        'IA: Detecta soporte inexistente, ciclo, autocontacto y apoyo incompatible en vano.'
        m=model();m['relations'] += [{'id':'missing','source':'beam','target':'absent','kind':'SUPPORTED_BY'},{'id':'cycle','source':'a','target':'deck','kind':'SUPPORTED_BY'},{'id':'bad','source':'c','target':'window','kind':'SUPPORTED_BY'}]
        codes={i['code'] for i in graph.validate(m)}
        self.assertTrue({'MISSING_ELEMENT','DEPENDENCY_CYCLE_OR_BLOCKED','INVALID_SUPPORT_KIND'}<=codes)

    def test_connection_is_not_support(self):
        'IA: Una conexión lateral afecta revisión pero no transmite pérdida de estabilidad.'
        m=model();m['relations'].append({'id':'lateral','source':'c','target':'a','kind':'CONNECTED_TO'})
        self.assertEqual(graph.loss(m,['a'])['unsupported'],[])
        self.assertIn('c',graph.affected(m,['a'])['dirty'])

    def test_adapter_does_not_invent_strength(self):
        'IA: Adaptador conserva IDs y procedencia nominal, sin convertir el evento de daño en conexión física.'
        source={'nodes':[{'id':'wall','type':'WALL'},{'id':'roof','type':'ROOF'},{'id':'damage','type':'DAMAGE_EVENT'}],'relations':[['wall','roof','nominal_support'],['damage','roof','affects']]}
        converted=adapter.from_nominal(source)
        self.assertEqual(len(converted['relations']),1)
        self.assertEqual(graph.loss(converted,['wall'])['requires_review'],['roof'])
        self.assertEqual(adapter.report(converted)['unresolved_supports'],['wall'])

    def test_order_independent_of_input(self):
        'IA: Orden e IDs de evaluación estables al reordenar registros de entrada.'
        m=model();expected=graph.order(m)
        m['elements'].reverse();m['relations'].reverse()
        self.assertEqual(graph.order(m),expected)
