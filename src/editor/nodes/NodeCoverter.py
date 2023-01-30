#coding:utf-8
import sys
from tools.vg_tools import PrintHelper
from vg_env import register_node

sys.path.append('..')
from vg_node_port import NodeInput, NodeOutput
from vg_node import Node
from vg_dtypes import VGDtypes


@register_node(name='bool -> str',
               output={'str': VGDtypes.String},
               package='Node Converter',
               is_pure=True)
def bool2String(bool: VGDtypes.Bool):
    return 'True' if bool else 'False'


@register_node(name='int -> str',
               output={'str': VGDtypes.String},
               package='Node Converter',
               is_pure=True)
def int2String(int: VGDtypes.Integer):
    return str(int)


@register_node(name='float -> str',
               output={'str': VGDtypes.String},
               package='Node Converter',
               is_pure=True)
def float2String(float: VGDtypes.Float):
    return str(float)


@register_node(name='obj -> str',
               output={'str': VGDtypes.String},
               package='Node Converter',
               is_pure=True)
def obj2String(object: VGDtypes.Class):
    return str(object)


@register_node(name='dict -> str',
               package='Node Converter',
               output={'str': VGDtypes.String},
               is_pure=True)
def dict2String(dic: VGDtypes.Dict):
    return str(dic)


@register_node(name='array -> str',
               package='Node Converter',
               output={'str': VGDtypes.String},
               is_pure=True)
def array2String(array: VGDtypes.Array):
    return str(array)


@register_node(name='int -> float',
               package='Node Converter',
               output={'str': VGDtypes.Float},
               is_pure=True)
def int2Float(int: VGDtypes.Integer):
    return float(int)


@register_node(name='str -> float',
               package='Node Converter',
               output={'float': VGDtypes.Float},
               is_pure=True)
def str2Float(str: VGDtypes.String):
    try:
        f = float(str)
        return f
    except:
        PrintHelper.printError(f'{str} 不能转化为 float类型。')


@register_node(name='str -> int',
               package='Node Converter',
               output={'int': VGDtypes.Integer},
               is_pure=True)
def str2Integer(str: VGDtypes.String):
    try:
        i = int(str)
        return i
    except:
        PrintHelper.printError(f'{str} 不能转化为 Integer类型。')



@register_node(name='float -> int',
               package='Node Converter',
               output={'int': VGDtypes.Integer},
               is_pure=True)
def float2Int(float: VGDtypes.Float):
    return int(float)
