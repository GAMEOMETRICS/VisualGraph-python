import sys

sys.path.append('..')
from vg_node_port import NodeInput, NodeOutput
from vg_node import Node
from vg_dtypes import VGDtypes


class Getter_Setter_Helper:

    @staticmethod
    def variable_getter_node(var_name,var_class):

        return type(f'Get_{var_name}',(GetterNode,),{'var_name':var_name,'var_class':var_class})

    @staticmethod
    def variable_setter_node(var_name,var_class):

        return type(f'Set_{var_name}',(SetterNode,),{'var_name':var_name,'var_class':var_class})




class GetterNode(Node):

    stored = False

    package_name = 'Variable'
    node_description = '变量的Gettter方法'

    var_name = None
    var_class = None

    def __init__(self):

        self.node_title = f"Get {self.var_name}"
        self.input_pins = []
        self.output_pins = [NodeOutput(pin_name=self.var_name,pin_type='data',pin_class=self.var_class)]

        super().__init__()


    def run_node(self):
        # 从graph里面获得对应名字变量的值，进行返回
        self.output(0,self.getVariableValue(self.var_name))


class SetterNode(Node):

    stored = False

    package_name = 'Variable'
    node_description = '变量的Setter方法'
    var_name = None
    var_class = None

    def __init__(self):

        self.node_title = f'Set {self.var_name}'

        self.input_pins = [NodeInput(pin_type='exec'),NodeInput(pin_name=self.var_name,pin_type='data',pin_class=self.var_class)]

        self.output_pins = [NodeOutput(pin_type='exec'),NodeOutput(pin_name='',pin_class=self.var_class,pin_type='data')]

        super().__init__()

    def run_node(self):

        # 首先设置width在graph中的值
        v = self.input(1)
        self.setVariableValue(self.var_name,v)
        # 将值设置到输出
        self.output(1,v)
        self.exec_output(0)
