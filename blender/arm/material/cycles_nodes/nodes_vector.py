from typing import Union

import bpy
from mathutils import Euler, Vector

import arm.material.cycles as c
from arm.material.parser_state import ParserState
from arm.material.shader import floatstr, vec3str


def parse_curvevec(node: bpy.types.ShaderNodeVectorCurve, out_socket: bpy.types.NodeSocket, state: ParserState) -> vec3str:
    fac = c.parse_value_input(node.inputs[0])
    vec = c.parse_vector_input(node.inputs[1])
    curves = node.mapping.curves
    name = c.node_name(node.name)
    # mapping.curves[0].points[0].handle_type # bezier curve
    return '(vec3({0}, {1}, {2}) * {3})'.format(
        c.vector_curve(name + '0', vec + '.x', curves[0].points),
        c.vector_curve(name + '1', vec + '.y', curves[1].points),
        c.vector_curve(name + '2', vec + '.z', curves[2].points), fac)


def parse_bump(node: bpy.types.ShaderNodeBump, out_socket: bpy.types.NodeSocket, state: ParserState) -> vec3str:
    # Interpolation strength
    strength = c.parse_value_input(node.inputs[0])
    # Height multiplier
    # distance = c.parse_value_input(node.inputs[1])
    state.sample_bump = True
    height = c.parse_value_input(node.inputs[2])
    state.sample_bump = False
    nor = c.parse_vector_input(node.inputs[3])
    if state.sample_bump_res != '':
        if node.invert:
            ext = ['1', '2', '3', '4']
        else:
            ext = ['2', '1', '4', '3']
        state.curshader.write('float {0}_fh1 = {0}_{1} - {0}_{2}; float {0}_fh2 = {0}_{3} - {0}_{4};'.format(state.sample_bump_res, ext[0], ext[1], ext[2], ext[3]))
        state.curshader.write('{0}_fh1 *= ({1}) * 3.0; {0}_fh2 *= ({1}) * 3.0;'.format(state.sample_bump_res, strength))
        state.curshader.write('vec3 {0}_a = normalize(vec3(2.0, 0.0, {0}_fh1));'.format(state.sample_bump_res))
        state.curshader.write('vec3 {0}_b = normalize(vec3(0.0, 2.0, {0}_fh2));'.format(state.sample_bump_res))
        res = 'normalize(mat3({0}_a, {0}_b, normalize(vec3({0}_fh1, {0}_fh2, 2.0))) * n)'.format(state.sample_bump_res)
        state.sample_bump_res = ''
    else:
        res = 'n'
    return res


def parse_mapping(node: bpy.types.ShaderNodeMapping, out_socket: bpy.types.NodeSocket, state: ParserState) -> vec3str:
    # Only "Point", "Texture" and "Vector" types supported for now..
    # More information about the order of operations for this node:
    # https://docs.blender.org/manual/en/latest/render/shader_nodes/vector/mapping.html#properties

    input_vector: bpy.types.NodeSocket = node.inputs[0]
    input_location: bpy.types.NodeSocket = node.inputs['Location']
    input_rotation: bpy.types.NodeSocket = node.inputs['Rotation']
    input_scale: bpy.types.NodeSocket = node.inputs['Scale']
    out = c.parse_vector_input(input_vector) if input_vector.is_linked else c.to_vec3(input_vector.default_value)
    location = c.parse_vector_input(input_location) if input_location.is_linked else c.to_vec3(input_location.default_value)
    rotation = c.parse_vector_input(input_rotation) if input_rotation.is_linked else c.to_vec3(input_rotation.default_value)
    scale = c.parse_vector_input(input_scale) if input_scale.is_linked else c.to_vec3(input_scale.default_value)

    # Use inner functions because the order of operations varies between
    # mapping node vector types. This adds a slight overhead but makes
    # the code much more readable.
    # - "Point" and "Vector" use Scale -> Rotate -> Translate
    # - "Texture" uses Translate -> Rotate -> Scale
    def calc_location(output: str) -> str:
        # Vectors and Eulers support the "!=" operator
        if input_scale.is_linked or input_scale.default_value != Vector((1, 1, 1)):
            if node.vector_type == 'TEXTURE':
                output = f'({output} / {scale})'
            else:
                output = f'({output} * {scale})'

        return output

    def calc_scale(output: str) -> str:
        if input_location.is_linked or input_location.default_value != Vector((0, 0, 0)):
            # z location is a little off sometimes?...
            if node.vector_type == 'TEXTURE':
                output = f'({output} - {location})'
            else:
                output = f'({output} + {location})'
        return output

    out = calc_location(out) if node.vector_type == 'TEXTURE' else calc_scale(out)

    if input_rotation.is_linked or input_rotation.default_value != Euler((0, 0, 0)):
        var_name = c.node_name(node.name) + "_rotation"
        if node.vector_type == 'TEXTURE':
            state.curshader.write(f'mat3 {var_name}X = mat3(1.0, 0.0, 0.0, 0.0, cos({rotation}.x), sin({rotation}.x), 0.0, -sin({rotation}.x), cos({rotation}.x));')
            state.curshader.write(f'mat3 {var_name}Y = mat3(cos({rotation}.y), 0.0, -sin({rotation}.y), 0.0, 1.0, 0.0, sin({rotation}.y), 0.0, cos({rotation}.y));')
            state.curshader.write(f'mat3 {var_name}Z = mat3(cos({rotation}.z), sin({rotation}.z), 0.0, -sin({rotation}.z), cos({rotation}.z), 0.0, 0.0, 0.0, 1.0);')
        else:
            # A little bit redundant, but faster than 12 more multiplications to make it work dynamically
            state.curshader.write(f'mat3 {var_name}X = mat3(1.0, 0.0, 0.0, 0.0, cos(-{rotation}.x), sin(-{rotation}.x), 0.0, -sin(-{rotation}.x), cos(-{rotation}.x));')
            state.curshader.write(f'mat3 {var_name}Y = mat3(cos(-{rotation}.y), 0.0, -sin(-{rotation}.y), 0.0, 1.0, 0.0, sin(-{rotation}.y), 0.0, cos(-{rotation}.y));')
            state.curshader.write(f'mat3 {var_name}Z = mat3(cos(-{rotation}.z), sin(-{rotation}.z), 0.0, -sin(-{rotation}.z), cos(-{rotation}.z), 0.0, 0.0, 0.0, 1.0);')

        # XYZ-order euler rotation
        out = f'{out} * {var_name}X * {var_name}Y * {var_name}Z'

    out = calc_scale(out) if node.vector_type == 'TEXTURE' else calc_location(out)

    return out


def parse_normal(node: bpy.types.ShaderNodeNormal, out_socket: bpy.types.NodeSocket, state: ParserState) -> Union[floatstr, vec3str]:
    if out_socket == node.outputs[0]:
        return c.to_vec3(node.outputs[0].default_value)
    elif out_socket == node.outputs[1]: # TODO: is parse_value path preferred?
        nor = c.parse_vector_input(node.inputs[0])
        return f'dot({c.to_vec3(node.outputs[0].default_value)}, {nor})'


def parse_normalmap(node: bpy.types.ShaderNodeNormalMap, out_socket: bpy.types.NodeSocket, state: ParserState) -> vec3str:
    if state.curshader == state.tese:
        return c.parse_vector_input(node.inputs[1])
    else:
        # space = node.space
        # map = node.uv_map
        # Color
        c.parse_normal_map_color_input(node.inputs[1], node.inputs[0])
        return None


def parse_vectortransform(node: bpy.types.ShaderNodeVectorTransform, out_socket: bpy.types.NodeSocket, state: ParserState) -> vec3str:
    # type = node.vector_type
    # conv_from = node.convert_from
    # conv_to = node.convert_to
    # Pass through
    return c.parse_vector_input(node.inputs[0])


def parse_displacement(node: bpy.types.ShaderNodeDisplacement, out_socket: bpy.types.NodeSocket, state: ParserState) -> vec3str:
    height = c.parse_value_input(node.inputs[0])
    midlevel = c.parse_value_input(node.inputs[1])
    scale = c.parse_value_input(node.inputs[2])
    nor = c.parse_vector_input(node.inputs[3])
    return f'(vec3({height}) * {scale})'