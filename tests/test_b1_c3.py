"""Propiedades y contratos de la revisión B1-C3."""
import random,unittest
from ruinas_panel.construction_core import graph
from ruinas_panel.structure import floor_frame


class B1C3Tests(unittest.TestCase):
    def test_stable_filtered_ids(self):
        'IA: Insertar un vano marca el candidato sin renumerar los ejes que sobreviven.'
        axes=floor_frame.aligned_axes([(x,8) for x in (0,10,20)],[(x,8) for x in (0,10,20)])['axes']
        before=floor_frame.filter_axes(axes,[],1)
        after=floor_frame.filter_axes(axes,[(-1,1,'BLOQUEADO_POR_VANO')],1)
        self.assertEqual([a['ordinal'] for a in before],[a['ordinal'] for a in after])
        self.assertEqual(after[0]['state'],'BLOQUEADO_POR_VANO')
        self.assertEqual(after[1:],before[1:])

    def test_loss_properties(self):
        'IA: 200 grafos DAG sembrados: conjuntos disjuntos, pérdidas monótonas y ausencia de revisión con políticas completas.'
        for seed in range(200):
            rng=random.Random(seed);nodes=[];relations=[]
            for i in range(15):
                parents=rng.sample(range(i),min(i,rng.randrange(4)))
                node={'id':str(i),'kind':'BEAM'}
                if parents and rng.random()<.8:node['minimum_supports']=rng.randint(1,len(parents))
                nodes.append(node)
                relations += [{'id':f'{i}-{j}','source':str(i),'target':str(j),'kind':'SUPPORTED_BY'} for j in parents]
            model={'elements':nodes,'relations':relations};removed={str(rng.randrange(15))}
            a=graph.loss(model,removed);b=graph.loss(model,removed|{str(rng.randrange(15))})
            self.assertFalse(set(a['unsupported'])&set(a['requires_review']))
            self.assertTrue(set(a['unsupported'])|set(a['removed'])<=set(b['unsupported'])|set(b['removed']))
            for node in nodes:
                count=sum(r['source']==node['id'] for r in relations)
                if count:node['minimum_supports']=1
            self.assertEqual(graph.loss(model,removed)['requires_review'],[])
