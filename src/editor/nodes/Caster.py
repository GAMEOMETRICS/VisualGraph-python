#coding:utf-8

import sys

sys.path.append('..')
from vg_node_port import NodeInput, NodeOutput
from vg_node import Node
from vg_dtypes import VGDtypes

from vg_config import NodeConfig
from vg_env import register_node, use_dtypes

NodeConfig.node_title_back_color['Casting'] = '#b45363'

# @register_node(name='Cast To (String)',output={'As String':VGDtypes.String},package='Casting')
# def cast_to(object:VGDtypes.Class)->VGDtypes.String:

#     return str(object)


# 遍历所有的类型生成node
@use_dtypes
class CastingNode(Node):
    stored = False

    package_name = 'Casting'
    node_title = 'Cast obj to'
    node_description = '转换节点'

    dtype = None

    def __init__(self):

        self.input_pins = [
            NodeInput(pin_type='exec'),
            NodeInput(pin_name='object',pin_type='data',pin_class=VGDtypes.Class)
        ]

        self.output_pins = [
            NodeOutput(pin_type='exec'),
            NodeOutput(pin_type='exec',pin_name='Cast Failed'),
            NodeOutput(pin_type='data',pin_class=self.dtype,pin_name=f'As {self.dtype.__name__}')
        ]

        super().__init__()

    def run_node(self):

        obj = self.input(1)

        if isinstance(obj,self.dtype):
            self.output(2,obj)
            self.exec_output(0)
        else:
            self.exec_output(1)

        return super().run_node()
