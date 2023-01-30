#coding:utf-8
import sys
from tools.vg_tools import PrintHelper

sys.path.append('..')
from vg_node_port import NodeInput, NodeOutput
from vg_node import Node
from vg_dtypes import VGDtypes

from vg_env import register_node
from vg_config import NodeConfig

class FileReadNode(Node):

    package_name = 'File Action'
    node_title = 'Read File'
    node_description = '从指定的filepath中进行逐行读取'

    input_pins = [

        NodeInput(pin_type='exec'),
        NodeInput(pin_name='Filepath',pin_type='data',pin_class=VGDtypes.String)
    ]

    output_pins = [
        NodeOutput(pin_type='exec',pin_name='Per Line'),
        NodeOutput(pin_name='line',pin_class=VGDtypes.String,pin_type='data'),
        NodeOutput(pin_name='Finished',pin_type='exec')
    ]


    def run_node(self):
        for line in open(self.input(1)):
            self._scene._view.new_session()
            line = line.strip()
            self.output(1,line)

            self.exec_output(0)
        
        self.exec_output(2)
