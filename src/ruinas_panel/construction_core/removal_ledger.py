"""Registro causal serializable de operaciones, independiente de Blender."""
import copy


class RemovalLedger:
    """IA: Conserva identidad y operaciones confirmadas; un recorte no se confunde con retirar una pieza completa."""

    def __init__(self):
        'IA: Crea inventario y eventos vacíos por generación, sin estado global.'
        self.elements={};self.events=[]

    def register(self,identifier,metadata):
        'IA: Registra una identidad única antes de operaciones; una colisión es un error, no un renombrado silencioso.'
        if identifier in self.elements:raise ValueError('ID duplicado: '+identifier)
        self.elements[identifier]=copy.deepcopy(metadata)

    def record(self,identifier,operation,cause,details=None):
        'IA: Añade una operación confirmada y ordenada; rechaza IDs desconocidos, causas vacías y mutaciones tras retirada.'
        if identifier not in self.elements:raise ValueError('ID desconocido: '+identifier)
        if operation not in ('REMOVE','CUT'):raise ValueError('Operación no registrada')
        if not isinstance(cause,str) or not cause:raise ValueError('Falta causa')
        if identifier in self.removed():raise ValueError('Pieza ya retirada: '+identifier)
        self.events.append({'sequence':len(self.events),'element_id':identifier,'operation':operation,'cause':cause,'details':copy.deepcopy(details or {})})

    def removed(self):
        'IA: Deriva retiradas completas del registro, sin consultar objetos supervivientes.'
        return {e['element_id'] for e in self.events if e['operation']=='REMOVE'}

    def state(self,identifier):
        'IA: Devuelve REMOVED, MODIFIED o INTACT según causas registradas; no inventa volumen residual de un corte.'
        if identifier not in self.elements:raise ValueError('ID desconocido: '+identifier)
        if identifier in self.removed():return 'REMOVED'
        return 'MODIFIED' if any(e['element_id']==identifier for e in self.events) else 'INTACT'

    def dump(self):
        'IA: Copia JSON apta para meta y caché, separando inventario de eventos.'
        return {'schema':1,'elements':copy.deepcopy(self.elements),'events':copy.deepcopy(self.events)}

    @classmethod
    def load(cls,data):
        'IA: Reconstruye y valida registro en orden; un salto o ID duplicado no se acepta.'
        if data.get('schema')!=1:raise ValueError('Esquema de registro incompatible')
        ledger=cls()
        for key,value in data['elements'].items():ledger.register(key,value)
        for index,event in enumerate(data['events']):
            if event['sequence']!=index:raise ValueError('Secuencia discontinua')
            ledger.record(event['element_id'],event['operation'],event['cause'],event['details'])
        return ledger
