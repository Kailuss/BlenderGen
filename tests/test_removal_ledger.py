"""Causalidad, identidad y persistencia del registro de retiradas."""
import unittest
from ruinas_panel.construction_core.removal_ledger import RemovalLedger
from ruinas_panel.construction_core import identifiers
from ruinas_panel.construction_core import causal_support,seat


class LedgerTests(unittest.TestCase):
    def test_cut_outside_contact(self):
        'IA: Un alojamiento sobre el rayo no invalida asiento; un corte que toca el rayo permanece incierto, y REMOVE siempre propaga.'
        ledger=RemovalLedger();ledger.register('stone',{})
        model={'elements':[{'id':'stone'},{'id':'seat','minimum_supports':1}],
               'relations':[{'source':'seat','target':'stone','kind':'SUPPORTED_BY','contact_z_mm':10}]}
        ledger.record('stone','CUT','SOCKET',{'box':[0,1,0,1,11,14]})
        self.assertNotIn('seat',causal_support.replay(model,ledger)['requires_review'])
        ledger.record('stone','CUT','WINDOW',{'box':[0,1,0,1,9,14]})
        self.assertIn('seat',causal_support.replay(model,ledger)['requires_review'])
        ledger.record('stone','REMOVE','DAMAGE')
        self.assertIn('seat',causal_support.replay(model,ledger)['unsupported'])

    def test_causal_bounds(self):
        'IA: Un corte incierto no certifica caída; retirar un extremo sí, sin necesitar malla final.'
        ledger=RemovalLedger()
        for key in ('front','back'):ledger.register(key,{})
        model={'elements':[{'id':'front'},{'id':'back'},{'id':'beam','minimum_supports':2}],
               'relations':[{'source':'beam','target':key,'kind':'SUPPORTED_BY'} for key in ('front','back')]}
        ledger.record('front','CUT','HOLE_BORDER')
        result=causal_support.replay(model,ledger)
        self.assertEqual(result['unsupported'],[])
        self.assertIn('beam',result['requires_review'])
        ledger.record('back','REMOVE','COLLAPSE')
        self.assertEqual(causal_support.replay(model,ledger)['unsupported'],['beam'])
        ledger.register('unmapped',{})
        with self.assertRaises(ValueError):causal_support.replay(model,ledger)

    def test_shared_seat(self):
        'IA: La regla mantiene el umbral histórico y rechaza auditorías con muestras omitidas.'
        self.assertEqual(seat.samples(10,20),[(8.5,17.3),(10,17.3),(11.5,17.3)])
        self.assertTrue(seat.supported([True,False,True]))
        self.assertFalse(seat.supported([False,False,True]))
        with self.assertRaises(ValueError):seat.supported([True,True])

    def test_replay(self):
        'IA: Corte y retirada posterior conservan causas sin confundir modificación y desaparición.'
        ledger=RemovalLedger();key=identifiers.piece('front','Piedra · 01.02')
        ledger.register(key,{'wall':'front'})
        ledger.record(key,'CUT','HOLE_BORDER',{'plane':[1,0,0]})
        self.assertEqual(ledger.state(key),'MODIFIED')
        ledger.record(key,'REMOVE','PRUNE_SUPPORT')
        self.assertEqual(RemovalLedger.load(ledger.dump()).removed(),{key})
        with self.assertRaises(ValueError):ledger.record(key,'REMOVE','SECOND')

    def test_invalid_and_isolated(self):
        'IA: Inventario copiado, IDs únicos y eventos sin identidad rechazan corrupción silenciosa.'
        ledger=RemovalLedger();metadata={'wall':'front'};ledger.register('a',metadata);metadata['wall']='back'
        self.assertEqual(ledger.elements['a']['wall'],'front')
        with self.assertRaises(ValueError):ledger.register('a',{})
        with self.assertRaises(ValueError):ledger.record('b','REMOVE','DAMAGE')
        with self.assertRaises(ValueError):ledger.record('a','REMOVE','')
        self.assertNotEqual(identifiers.piece('a/b','c'),identifiers.piece('a','b/c'))
