"""Dibuja todos los paneles de Ruinas con un layout simulado y comprueba propiedades y operadores.

Blender en segundo plano no dibuja interfaz; aquí cada draw() recibe un layout falso que
registra las llamadas y falla si una propiedad no existe en su dato o un operador no está
registrado. Escenarios: casa, laboratorio estructural, laboratorio de ladrillos y reproducción.
"""
import sys
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
import ruinas_panel as addon
from ruinas_panel.ui import panel


class FakeOperator:
    """Propiedades de operador asignables (p. ej. section) sin efecto."""

    def __setattr__(self, name, value):
        """IA: Acepta cualquier propiedad de operador; solo se registra la llamada."""
        object.__setattr__(self, name, value)


class FakeLayout:
    """Layout que valida prop() y operator() y devuelve sub-layouts para row/column/box."""

    def __init__(self, log):
        """IA: Comparte el registro de llamadas con todos los sub-layouts."""
        object.__setattr__(self, 'log', log)

    def __setattr__(self, name, value):
        """IA: enabled, alert, scale_y, use_property_split… se aceptan sin efecto."""
        object.__setattr__(self, name, value)

    def _child(self, *args, **kwargs):
        """IA: row/column/box/split devuelven otro layout falso con el mismo registro."""
        return FakeLayout(self.log)

    row = column = box = split = grid_flow = column_flow = _child

    def prop(self, data, name, **kwargs):
        """IA: Falla si la propiedad no existe en el dato (RNA o atributo)."""
        if data is None or (name not in data.bl_rna.properties and not hasattr(data, name)):
            raise AssertionError('Propiedad inexistente: %s.%s' % (type(data).__name__, name))
        self.log['props'].add(name)

    def operator(self, idname, **kwargs):
        """IA: Falla si el operador no está registrado en bpy.ops."""
        group, name = idname.split('.')
        if not hasattr(getattr(bpy.ops, group), name) or getattr(getattr(bpy.ops, group), name).idname() is None:
            raise AssertionError('Operador inexistente: ' + idname)
        try:
            getattr(getattr(bpy.ops, group), name).get_rna_type()
        except KeyError:
            raise AssertionError('Operador no registrado: ' + idname)
        self.log['operators'].add(idname)
        return FakeOperator()

    def label(self, **kwargs):
        """IA: Las etiquetas solo se cuentan."""
        self.log['labels'] += 1

    def separator(self, **kwargs):
        """IA: Sin efecto."""


def draw_all(scene, title):
    """IA: Ejecuta poll y draw (y cabeceras) de cada panel de Ruinas en la escena dada; devuelve paneles dibujados."""
    bpy.context.window.scene = scene
    log = dict(props=set(), operators=set(), labels=0)
    drawn = []
    for cls in (panel.RUIN_PT_panel,) + panel.SUBPANELS + panel.LAB_SUBPANELS:
        if not cls.poll(bpy.context):
            continue
        fake = type('Fake', (), {})()
        fake.layout = FakeLayout(log)
        for method in ('draw_header', 'draw_header_preset', 'draw'):
            fn = getattr(cls, method, None)
            if fn is not None:
                fn(fake, bpy.context)
        drawn.append(cls.bl_idname)
    print('UI_DRAW', title, len(drawn), 'paneles', len(log['props']), 'propiedades', len(log['operators']), 'operadores', flush=True)
    return drawn


def run():
    """IA: Registra el add-on, prepara cuatro escenas tipo y dibuja todos los paneles en cada una."""
    addon.register()
    house = bpy.context.scene
    draw_all(house, 'casa')
    draw_all(house, 'casa-fisica-edificio')
    labs = {}
    for name, flags in (('lab-estructural', dict(ruinas_physics_lab=True, structural_physics=True)),
                        ('lab-ladrillos', dict(ruinas_physics_lab=True, masonry_lab=True)),
                        ('reproduccion', dict(ruinas_replay=True, physics_result_scene=True, lab_scene='x'))):
        scene = bpy.data.scenes.new(name)
        for key, value in flags.items():
            scene[key] = value
        bpy.context.window.scene = scene
        bpy.ops.rigidbody.world_add()
        labs[name] = draw_all(scene, name)
    assert any(n.startswith('RUIN_PT_lab_') for n in labs['lab-estructural'])
    assert not any(n.startswith('RUIN_PT_lab_') for n in labs['reproduccion'])
    assert 'RUIN_PT_lab_event' not in labs['lab-ladrillos']
    print('UI_DRAW_PASSED', flush=True)


if __name__ == '__main__':
    run()
