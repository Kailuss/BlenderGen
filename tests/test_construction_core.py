"""Dependencias constructivas sin bpy, ni mallas, ni solucionador físico."""
import unittest
from ruinas_panel.construction_core import graph,adapter,schema,units,materials


def model():
    'IA: Viga sobre tres apoyos con mínimo dos, tablero dependiente y ventana alojada en un apoyo.'
    elements=[{'id':x,'kind':'WALL'} for x in ('a','b','c')]+[{'id':'beam','kind':'BEAM','minimum_supports':2},{'id':'deck','kind':'DECK','minimum_supports':1},{'id':'window','kind':'OPENING'}]
    relations=[{'id':x,'source':'beam','target':x,'kind':'SUPPORTED_BY'} for x in ('a','b','c')]
    relations.extend([{'id':'deck-beam','source':'deck','target':'beam','kind':'SUPPORTED_BY'},{'id':'window-a','source':'window','target':'a','kind':'HOSTED_BY'}])
    return {'elements':elements,'relations':relations}


class ConstructionTests(unittest.TestCase):
    def test_material_catalog_confidence_and_fingerprint(self):
        'IA: La tabla conserva C por campo y cambia su firma al cambiar un valor; no acepta caminos críticos provisionales.'
        from ruinas_panel import config_materials
        before=materials.signature();old=config_materials.MECHANICAL['TIMBER_SOFT']['compression']
        try:
            config_materials.MECHANICAL['TIMBER_SOFT']['compression']=(21,15,35)
            self.assertNotEqual(before,materials.signature())
        finally:config_materials.MECHANICAL['TIMBER_SOFT']['compression']=old
        self.assertEqual(before,materials.signature())
        self.assertFalse(materials.acceptance('TIMBER_SOFT',['compression'])['accepted'])
        self.assertEqual(materials.acceptance('PLASTER',['density_kg_m3'])['unknown'],['density_kg_m3'])

    def test_variability_local_and_bounded(self):
        'IA: Variabilidad reproducible e independiente del orden, acotada en espacio logarítmico sin usar hash de proceso.'
        import math,random
        state=random.getstate();sigma=math.sqrt(math.log1p(.25**2))
        values=[materials.variability(seed,'beam.1',.25) for seed in range(100)]
        self.assertEqual(state,random.getstate());self.assertEqual(len(set(values)),100)
        self.assertEqual(values,[materials.variability(seed,'beam.1',.25) for seed in range(100)])
        self.assertTrue(all(math.exp(-sigma*sigma/2-2*sigma)<=v<=math.exp(-sigma*sigma/2+2*sigma) for v in values))

    def test_world_scale_invariance(self):
        'IA: El mismo pilar de mundo a 1:30 y 1:60 conserva masa, área y tensión; una escala ausente falla explícitamente.'
        results=[]
        for scale in (30,60):
            area=units.to_world((300/scale)**2,2,scale)
            volume=units.to_world((300/scale)**2*(3000/scale),3,scale)
            e=schema.element('pillar','POST',material='stone',volume_mm3=volume)
            results.append((e['mass_kg'],area,e['mass_kg']*9.81/area))
        self.assertEqual(results[0],results[1])
        self.assertAlmostEqual(results[0][2],.064746)
        with self.assertRaises(ValueError):units.to_world(1,3,None)

    def test_bracing_and_event_are_separate(self):
        'IA: Perder arriostramiento invalida revisión lateral sin inventar pérdida vertical; igual pico puede tener distinto impulso.'
        m=adapter.from_nominal({'nodes':[{'id':'wall','type':'WALL'},{'id':'floor','type':'FLOOR'}],'relations':[]})
        m['relations'].append({'id':'brace','source':'wall','target':'floor','kind':'ARRIOSTRADO_POR','state':'INTACTO'})
        schema.synchronise_supports(m)
        self.assertEqual(schema.validate(m),[])
        self.assertEqual(graph.affected(m,['floor'])['dirty'],['floor','wall'])
        self.assertEqual(graph.loss(m,['floor'])['unsupported'],[])
        a=units.event(5,.01,(1,0,0));b=units.event(5,.1,(1,0,0))
        self.assertEqual(a['peak_kpa'],b['peak_kpa']);self.assertNotEqual(a['impulse_kpa_s'],b['impulse_kpa_s'])

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
