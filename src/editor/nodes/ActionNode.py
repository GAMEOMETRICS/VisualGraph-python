#coding:utf-8
import sys

sys.path.append('..')
from vg_node_port import NodeInput, NodeOutput
from vg_node import Node
from vg_dtypes import VGDtypes


class BeginNode(Node):
    package_name = 'Action Default'
    node_title = 'Begain To Run'
    node_description = '本graph必须包含的一个节点，graph的开始'

    input_pins = [
    ]

    output_pins = [
        NodeOutput(pin_name='Begin',pin_type='exec')
    ]

    
    def run_node(self):
        self.exec_output(0)


class PrintNode(Node):
    package_name = 'Action Default'
    node_title = 'Print To Console'
    node_description = '本graph必须包含的一个节点，graph的开始'

    input_pins = [
        NodeInput(pin_name='', pin_type='exec'),
        NodeInput(pin_name='str', pin_class=VGDtypes.String)
    ]

    output_pins = [NodeOutput(pin_name='',pin_type='exec'),NodeOutput(pin_name='str',pin_class = VGDtypes.String)]

    def run_node(self):

        input_v = self.input(1)
        print(input_v)
        self.output(1,input_v)
        self.exec_output(0)
