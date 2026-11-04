"""Causalidad, identidad y persistencia del registro de retiradas."""
import unittest
from ruinas_panel.construction_core.removal_ledger import RemovalLedger
from ruinas_panel.construction_core import identifiers
from ruinas_panel.construction_core import causal_support,seat


class LedgerTests(unittest.TestCase):
    def test_segment_floor_identity(self):
        'IA: La planta de la viga forma parte del ID; filtrar otros ordinales no altera el superviviente.'
        self.assertEqual(identifiers.segment('front',2,0,7),'seg.front.f2.b0.7')
        self.assertNotEqual(identifiers.segment('front',1,0,7),identifiers.segment('front',2,0,7))
        for values in ((0,0,1),(1,-1,1),(1,0,-1),(1,0,1.5)):
            with self.assertRaises(ValueError):identifiers.segment('front',*values)

    def test_layout_key_identity(self):
        'IA: La clave de aparejo no depende del nombre de Blender; tipos, hiladas e índices distintos no colisionan (C5-5).'
        self.assertEqual(identifiers.layout_key('stone',3,7),'stone.c3.i7')
        keys={identifiers.piece(w,identifiers.layout_key(k,c,i)) for w in ('front','left') for k in ('stone','mortar','pier0')
              for c in range(3) for i in range(3)}
        self.assertEqual(len(keys),2*3*9)
        self.assertNotEqual(identifiers.layout_key('pier1',0,12),identifiers.layout_key('pier11',0,2))
        for values in (('',0,0),('stone',-1,0),('stone',0,1.5),('stone','1',0)):
            with self.assertRaises(ValueError):identifiers.layout_key(*values)

    def test_masonry_roles(self):
        'IA: Sillares, núcleo de mortero y cimentación se distinguen por el tipo de aparejo; otras piezas no tienen papel.'
        self.assertEqual([identifiers.role(k) for k in ('stone','pier3','mortar','found2','step',None,'beam')],
                         ['SILLAR','SILLAR','NUCLEO','CIMENTACION','CIMENTACION',None,None])

    def test_layout_key_fallback(self):
        'IA: removal_events usa la clave de aparejo si la pieza la lleva y el nombre en caso contrario.'
        import sys,types
        sys.modules.setdefault('bpy',types.ModuleType('bpy'))
        try:
            from ruinas_panel.services import removal_events
        except Exception as error:
            self.skipTest('removal_events necesita Blender: %s'%error)
        class Fake(dict):
            name='Piedra · 01.02.001'
        tagged=identifiers.tag(Fake(),'stone',1,2)
        self.assertEqual(removal_events.source_key(tagged),'stone.c1.i2')
        self.assertEqual(removal_events.source_key(Fake()),'Piedra · 01.02.001')

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
        'IA: Dos de tres rayos, ahora en el centro de la banda de piedra (−3,6 mm, C5-2); rechaza auditorías con muestras omitidas.'
        self.assertEqual(seat.samples(10,20),[(8.5,20-3.6),(10,20-3.6),(11.5,20-3.6)])
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
