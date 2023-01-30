#coding:utf-8
import sys

sys.path.append('..')
from vg_node_port import NodeInput, NodeOutput
from vg_node import Node
from vg_dtypes import VGDtypes

from vg_env import register_node

from vg_config import NodeConfig
import math

NodeConfig.node_title_back_color['Num Action'] = '#66CDAA'


@register_node(name='+ (Integer)',
               output={'sum': VGDtypes.Integer},
               package='Num Action',
               is_pure=True)
def addInteger(A: VGDtypes.Integer, B: VGDtypes.Integer):
    return A + B


@register_node(name='+ (Float)',
               output={'sum': VGDtypes.Float},
               package='Num Action',
               is_pure=True)
def add_float(A: VGDtypes.Float, B: VGDtypes.Float) -> VGDtypes.Float:
    return A + B


@register_node(name='- (Float)',
               package='Num Action',
               output={'minus': VGDtypes.Float},
               is_pure=True)
def minus_float(A: VGDtypes, B: VGDtypes.Float) -> VGDtypes.Float:
    '''减法 返回A-B'''
    return A - B

@register_node(name='* (Float)',
               package='Num Action',
               output={'mul': VGDtypes.Float},
               is_pure=True)
def multuply_float(A: VGDtypes, B: VGDtypes.Float) -> VGDtypes.Float:
    '''乘法 返回A*B'''
    return A * B


@register_node(name='/ (Float)',
               package='Num Action',
               output={'divide': VGDtypes.Float},
               is_pure=True)
def divide_float(A: VGDtypes.Float, B: VGDtypes.Float) -> VGDtypes.Float:
    '''除法，A/B，B不能为0。'''
    if B == 0:
        raise ValueError(f'除法参数B不能为0。')

    return A / B


@register_node(name='// (Float)',
               package='Num Action',
               output={'times': VGDtypes.Integer},
               is_pure=True)
def divide_float(A: VGDtypes.Float, B: VGDtypes.Float) -> VGDtypes.Integer:
    '''除法取商，A//B，B不能为0。'''
    if B == 0:
        raise ValueError(f'除法参数B不能为0。')

    return int(A // B)


@register_node(name='% (Float)',
               package='Num Action',
               output={'divide': VGDtypes.Float},
               is_pure=True)
def mod_float(A: VGDtypes.Float, B: VGDtypes.Float) -> VGDtypes.Float:
    '''除法，A%B，求余数。'''
    if B == 0:
        raise ValueError(f'除法参数B不能为0。')

    return A % B

@register_node(name='Ceil (Float)',
               package='Num Action',
               output={'Ceil': VGDtypes.Integer},
               is_pure=True)
def ceil_float(float:VGDtypes.Float)->VGDtypes.Integer:
    '''向上取整'''
    return math.ceil(float)


@register_node(name='Round (Float)',
               package='Num Action',
               output={'Round': VGDtypes.Integer},
               is_pure=True)
def round_float(float:VGDtypes.Float)->VGDtypes.Integer:
    '''四舍五入'''
    return round(float)


@register_node(name='Floor (Float)',
               package='Num Action',
               output={'Floor': VGDtypes.Integer},
               is_pure=True)
def floor_float(float:VGDtypes.Float)->VGDtypes.Integer:
    '''向下取整'''
    return math.floor(float)


@register_node(name='> (Float)',
               package='Num Action',
               output={
                   'isTrue': VGDtypes.Bool,
                   'A': VGDtypes.Float,
                   'B': VGDtypes.Float
               },
               is_pure=True)
def greater_float(A: VGDtypes.Float, B: VGDtypes.Float) -> VGDtypes.Float:
    '''A和B比大小，如果A>B则返回True'''
    return A > B, A, B


@register_node(name='< (Float)',
               package='Num Action',
               output={
                   'isTrue': VGDtypes.Bool,
                   'A': VGDtypes.Float,
                   'B': VGDtypes.Float
               },
               is_pure=True)
def smaller_float(A: VGDtypes.Float, B: VGDtypes.Float) -> VGDtypes.Float:
    '''A和B比大小，如果A>B则返回True'''
    return A < B, A, B


@register_node(name='>= (Float)',
               package='Num Action',
               output={
                   'isTrue': VGDtypes.Bool,
                   'A': VGDtypes.Float,
                   'B': VGDtypes.Float
               },
               is_pure=True)
def not_smaller_float(A: VGDtypes.Float, B: VGDtypes.Float) -> VGDtypes.Float:
    '''A和B比大小，如果A>B则返回True'''
    return A >= B, A, B


@register_node(name='<= (Float)',
               package='Num Action',
               output={
                   'isTrue': VGDtypes.Bool,
                   'A': VGDtypes.Float,
                   'B': VGDtypes.Float
               },
               is_pure=True)
def not_greater_float(A: VGDtypes.Float, B: VGDtypes.Float) -> VGDtypes.Float:
    '''A和B比大小，如果A>B则返回True'''
    return A <= B, A, B


@register_node(name='!= (Float)',
               output={'Not Equal': bool},
               package='Num Action',
               is_pure=True)
def not_equal_float(A: VGDtypes.Float, B: VGDtypes.Float) -> bool:

    return A != B


@register_node(name='== (Float)',
               output={'Equal': bool},
               package='Num Action',
               is_pure=True)
def equal(A: VGDtypes.Float, B: VGDtypes.Float) -> bool:

    return A == B


class GreaterIntegerNode(Node):

    package_name = 'Num Action'

    node_title = '> (Integer)'
    node_description = '基本运算 除法'

    input_pins = [
        NodeInput(pin_name='A', pin_type='data', pin_class=VGDtypes.Integer),
        NodeInput(pin_name='B', pin_type='data', pin_class=VGDtypes.Integer)
    ]

    output_pins = [
        NodeOutput(pin_name='isTrue', pin_class=VGDtypes.Bool,
                   pin_type='data'),
        NodeOutput(pin_name='A', pin_type='data', pin_class=VGDtypes.Integer),
        NodeOutput(pin_name='B', pin_type='data', pin_class=VGDtypes.Integer)
    ]

    def run_node(self):

        isTrue = self.input(0) > self.input(1)
        self.output(0, isTrue)

        self.output(1, self.input(0))
        self.output(2, self.input(1))



@register_node(name='!= (Integer)',
               output={'Not Equal': bool},
               package='Num Action',
               is_pure=True)
def not_equal2(A: VGDtypes.Integer, B: VGDtypes.Integer) -> bool:

    return A != B


@register_node(name='== (Integer)',
               output={'Equal': bool},
               package='Num Action',
               is_pure=True)
def equal2(A: VGDtypes.Integer, B: VGDtypes.Integer) -> bool:
    return A == B
