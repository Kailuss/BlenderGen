"""Materiales compartidos: variación cromática acotada y microrelieve de sombreado sin subdividir."""
import bpy


def configure(mat,color):
    'IA: Configura nodos una vez por material; el bump es visual y no se presenta como geometría exportable.'
    if mat.get('ruin_surface_version')==1:return
    family=mat.name.split(' · ')[0]
    if family not in ('Madera','Piedra','Tejas','Tierra','Latón','Hierro','Revoco','Núcleo'):return
    mat.use_nodes=True;nodes=mat.node_tree.nodes;links=mat.node_tree.links;nodes.clear()
    output=nodes.new('ShaderNodeOutputMaterial');bsdf=nodes.new('ShaderNodeBsdfPrincipled');links.new(bsdf.outputs['BSDF'],output.inputs['Surface'])
    coords=nodes.new('ShaderNodeTexCoord');scale=nodes.new('ShaderNodeVectorMath');scale.operation='MULTIPLY'
    wood=family=='Madera'
    position=coords.outputs['UV'] if wood else nodes.new('ShaderNodeNewGeometry').outputs['Position']
    links.new(position,scale.inputs[0]);scale.inputs[1].default_value=(10,.65,1) if wood else (.32,.32,.32)
    noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=1;noise.inputs['Detail'].default_value=2;links.new(scale.outputs['Vector'],noise.inputs['Vector'])
    ramp=nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.18;ramp.color_ramp.elements[1].position=.85
    ramp.color_ramp.elements[0].color=tuple(c*.63 for c in color)+(1,);ramp.color_ramp.elements[1].color=tuple(min(1,c*1.2+.015) for c in color)+(1,)
    links.new(noise.outputs['Fac'],ramp.inputs['Fac']);links.new(ramp.outputs['Color'],bsdf.inputs['Base Color'])
    bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.27;bump.inputs['Distance'].default_value=.10 if wood else .075
    links.new(noise.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs['Normal'],bsdf.inputs['Normal'])
    bsdf.inputs['Roughness'].default_value=.78
    if family in ('Latón','Hierro'):bsdf.inputs['Metallic'].default_value=.7;bsdf.inputs['Roughness'].default_value=.55
    mat['ruin_surface_version']=1


def variant(mat,index):
    'IA: Paleta de cinco tonos por familia, compartida por todas las piezas; nunca crea material por ladrillo.'
    base=mat.name.split(' / tono')[0];name=base+' / tono'+str(index%5)
    existing=bpy.data.materials.get(name)
    if existing:return existing
    color=tuple(float(c) for c in mat.diffuse_color[:3]);factor=(.86,.94,1,1.055,1.11)[index%5]
    color=tuple(min(1,c*factor) for c in color);result=bpy.data.materials.new(name);result.diffuse_color=(*color,1);configure(result,color)
    return result


def grain_uv(ob,values):
    'IA: Coordenadas de veta en ejes físicos de la pieza antes de rotarla; permanecen alineadas tras transformaciones.'
    layer=ob.data.uv_layers.new(name='Fibra longitudinal')
    for loop in ob.data.loops:layer.data[loop.index].uv=values[loop.vertex_index]
