#coding:utf-8
from operator import is_
import sys

sys.path.append('..')
from vg_node_port import NodeInput, NodeOutput
from vg_node import Node
from vg_dtypes import VGDtypes

from vg_env import register_node

from vg_config import NodeConfig

NodeConfig.node_title_back_color['Array Action'] = '#FF6347'


@register_node(name='Get (Array)',input={'array':VGDtypes.Array,'index':VGDtypes.Integer},output={'item':VGDtypes.Class},package='Array Action',is_pure=True)
def ArrayGet(array:VGDtypes.Array,index:VGDtypes.Integer):
    return array[index]

@register_node(name='Set (Array)',output={'array':VGDtypes.Array},package='Array Action')
def ArraySet(array:VGDtypes.Array,index:VGDtypes.Integer,value:VGDtypes.Class):
    array[index] = value
    return array

@register_node(name='Length (Array)',output={'length':VGDtypes.Integer},package='Array Action',is_pure=True)
def ArrayLength(array:VGDtypes.Array):
    return len(array)
