"""Resistencia artística por familia, independiente de selección y colisión."""
FIELDS=('physics_stone_strength','physics_tile_strength','physics_wood_strength','physics_floor_strength','physics_metal_strength','physics_plaster_strength')


def family(ob):
    'IA: Prioriza revoco y tablones sobre el material general; usa identidad de fuente conservada en las copias físicas.'
    if ob.get('fragile_material')=='plaster':return 'plaster'
    if ob.get('physical_role')=='wood' and 'suelo' in ob.get('source_piece',ob.name).lower():return 'floor'
    return ob.get('physical_role','stone')


def apply(scene):
    'IA: En la copia de cálculo, multiplica cada umbral original por la menor resistencia de sus familias; repetir no acumula factores y no altera soldaduras irrompibles.'
    count=0
    for ob in scene.objects:
        c=ob.rigid_body_constraint
        if not c or not c.use_breaking or not c.object1 or not c.object2:continue
        if 'material_base_threshold' not in ob:ob['material_base_threshold']=c.breaking_threshold
        factors=[getattr(scene.ruin_settings,'physics_'+family(part)+'_strength',1) for part in (c.object1,c.object2)]
        c.breaking_threshold=max(1e-7,ob['material_base_threshold']*min(factors));count+=1
    return count
