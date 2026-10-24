"""B1.3: extremos independientes y reparto total de cargas."""
import copy,unittest
from ruinas_panel.construction_core import adapter,graph,schema


def fixture():
    'IA: Dos piedras por extremo de viga, otra viga independiente y tablón que admite cualquiera de las dos.'
    nodes=[{'id':x,'type':'WALL'} for x in ('a','b','c','d')]
    nodes += [{'id':x,'type':'BEAM'} for x in ('beam','neighbour')]+[{'id':'plank','type':'PLANK'}]
    edges=[[x,'beam','supports'] for x in ('a','b','c','d')]
    edges += [['a','neighbour','supports'],['beam','plank','supports'],['neighbour','plank','supports']]
    model=adapter.from_nominal({'nodes':nodes,'relations':edges})
    by_id={e['id']:e for e in model['elements']}
    by_id['beam']['support_groups']=[{'id':'left','members':['a','b'],'minimum':1},{'id':'right','members':['c','d'],'minimum':1}]
    by_id['plank']['minimum_supports']=1
    return model


class FloorSupportGroups(unittest.TestCase):
    def test_header_post_cascade(self):
        'IA: Perder el poste hace caer su cabecero y la viga que termina allí, sin afectar la viga larga independiente.'
        m=fixture()
        m['elements'] += [schema.element('post','POST'),schema.element('header','HEADER')]
        m['relations'] += [adapter.relation('post','c','SUPPORTED_BY'),adapter.relation('header','post','SUPPORTED_BY')]
        m['relations']=[r for r in m['relations'] if not (r['source']=='beam' and r['target'] in ('c','d'))]
        m['relations'].append(adapter.relation('beam','header','SUPPORTED_BY'))
        nodes={e['id']:e for e in m['elements']}
        nodes['post']['minimum_supports']=1;nodes['header']['minimum_supports']=1
        nodes['beam']['support_groups'][1]['members']=['header']
        schema.synchronise_supports(m)
        self.assertEqual(graph.validate(m),[])
        self.assertEqual(graph.loss(m,['post'])['unsupported'],['beam','header'])

    def test_independent_ends(self):
        'IA: Dos apoyos supervivientes en el mismo extremo no sustituyen al extremo perdido.'
        m=fixture();self.assertEqual(graph.validate(m),[])
        self.assertEqual(graph.loss(m,['c'])['unsupported'],[])
        self.assertEqual(graph.loss(m,['c','d'])['unsupported'],['beam'])
        self.assertEqual(graph.loss(m,['c','d','neighbour'])['unsupported'],['beam','plank'])

    def test_invalid_groups(self):
        'IA: Grupos vacíos, referencias ajenas, mínimos imposibles e IDs repetidos son errores explícitos.'
        for groups in ([],[{'id':'end','members':[],'minimum':1}],
                       [{'id':'end','members':['missing'],'minimum':1}],
                       [{'id':'end','members':['a','b','c','d'],'minimum':5}],
                       [{'id':'end','members':['a','b'],'minimum':1},{'id':'end','members':['c','d'],'minimum':1}]):
            m=fixture();next(e for e in m['elements'] if e['id']=='beam')['support_groups']=copy.deepcopy(groups)
            with self.subTest(groups=groups):
                self.assertTrue(any(i['code']=='INVALID_SUPPORT_GROUPS' for i in graph.validate(m)))
                with self.assertRaises(ValueError):graph.loss(m,['a'])

    def test_total_load_share(self):
        'IA: El reparto se suma por elemento entre relaciones y contactos; los desconocidos no se convierten en cero físico.'
        m=fixture();relations=[r for r in m['relations'] if r['source']=='beam']
        for r in relations:r['contacts']=[{'load_share':.25}]
        self.assertFalse(any(i['code']=='EXCESS_SUPPORT_LOAD_SHARE' for i in schema.validate(m)))
        relations[0]['contacts'].append({'load_share':.01})
        self.assertTrue(any(i['code']=='EXCESS_SUPPORT_LOAD_SHARE' for i in schema.validate(m)))
