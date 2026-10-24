"""Contratos A: catálogo, contactos, identidad y aceptación."""
import unittest
from unittest.mock import patch
from ruinas_panel.construction_core import adapter,materials,schema
from ruinas_panel.structure import building_definition


class Contracts(unittest.TestCase):
    def test_acceptance_states(self):
        'IA: Distingue desconocido, provisional y evidencia B con fuente; una etiqueta B sin fuente no basta.'
        self.assertEqual(materials.acceptance('GLASS',['compression'])['state'],'RECHAZADO')
        self.assertEqual(materials.acceptance('TIMBER_SOFT',['compression'])['state'],'PROVISIONAL')
        table=materials.catalog();table['TIMBER_SOFT']['compression'].update(confidence='B',source='Fuente ficticia solo de prueba')
        with patch.object(materials,'catalog',return_value=table):
            self.assertEqual(materials.acceptance('TIMBER_SOFT',['compression'])['state'],'ACEPTADO')
            table['TIMBER_SOFT']['compression']['source']=None
            self.assertEqual(materials.acceptance('TIMBER_SOFT',['compression'])['state'],'RECHAZADO')

    def test_contact_merge(self):
        'IA: Dos zonas del mismo apoyo quedan en una relación con dos contactos, no dos apoyos.'
        contacts=[{'point_mm':[x,0,0],'area_mm2':100,'seat_mm':10,'load_share':.5} for x in (0,20)]
        relations=[adapter.relation('beam','wall','SUPPORTED_BY',[c]) for c in contacts]
        merged=adapter.merge_relations(relations)
        self.assertEqual(len(merged),1);self.assertEqual(merged[0]['contacts'],contacts)
        relations[1]['state']='ASENTADO'
        with self.assertRaises(ValueError):adapter.merge_relations(relations)

    def test_opening_identity(self):
        'IA: Insertar otro vano no renombra los anteriores; planta es atributo y carpintería tiene entidad propia.'
        definition={'levels':[{'id':'floor.0'}]};walls=[{'id':'front'}]
        windows=[{'wall':'front','floor':0,'x':x,'x0':x-5,'x1':x+5} for x in (20,40)]
        a=building_definition.graph(definition,walls,{},windows,[],False)
        b=building_definition.graph(definition,walls,{},[{'wall':'front','floor':0,'x':0,'x0':-5,'x1':5}]+windows,[],False)
        ids={n['id'] for n in a['nodes'] if n['type']=='OPENING'}
        self.assertTrue(ids<={n['id'] for n in b['nodes']})
        self.assertFalse(any(x=='floor.0' and y in ids and kind=='contains' for x,y,kind in a['relations']))
        self.assertEqual(len([n for n in a['nodes'] if n['type']=='JOINERY']),2)

    def test_invalid_contact(self):
        'IA: Área negativa y reparto mayor que uno no pasan como contacto válido.'
        m=adapter.from_nominal({'nodes':[{'id':'wall','type':'WALL'},{'id':'beam','type':'BEAM'}],'relations':[['wall','beam','supports']]})
        m['relations'][0]['contacts']=[{'point_mm':None,'area_mm2':-1,'seat_mm':None,'load_share':2}]
        self.assertEqual(len([i for i in schema.validate(m) if i['code']=='INVALID_CONTACT']),2)
