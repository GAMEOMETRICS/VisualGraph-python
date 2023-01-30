#coding:utf-8
import sys
sys.path.append('..')
from vg_node_port import NodeInput,NodeOutput
from vg_node import Node
from vg_dtypes import VGDtypes
import time

class BranchNode(Node):


    package_name = 'Basic Control'
    node_title = 'Branch'
    node_description = 'Execute based on input condition'

    input_pins = [
        NodeInput(pin_type='exec'),
        NodeInput(pin_name='Condition',pin_class=VGDtypes.Bool,pin_type='data')
    ]

    output_pins = [
        NodeOutput(pin_name='True',pin_type='exec'),
        NodeOutput(pin_name='False',pin_type='exec')
    ]


    def run_node(self):
        if self.input(1):
            self.exec_output(0)
        else:
            self.exec_output(1)


class ForEahcNode(Node):


    package_name = 'Basic Control'
    node_title = 'ForEach'
    node_description = 'For Each loop'

    refresh_along_session = False

    input_pins = [
        NodeInput(pin_type='exec'),
        NodeInput(pin_name='arrays',pin_class=VGDtypes.Array,pin_type='data')
    ]

    output_pins = [
        NodeOutput(pin_name='Loop Body',pin_type='exec'),
        NodeOutput(pin_name='index',pin_class=VGDtypes.Integer,pin_type='data'),
        NodeOutput(pin_name='item',pin_class=VGDtypes.Class,pin_type='data'),
        NodeOutput(pin_name='Completed',pin_type='exec')

    ]


    def run_node(self):

        for index,item in enumerate(self.input(1)):
            self.output(1,index)
            self.output(2,item)
            self.exec_output(0)
            self.spawn_new_session()

        self.exec_output(3)


class ForLoop(Node):

    package_name = 'Basic Control'
    node_title = 'ForLoop'
    node_description = 'For loop'

    refresh_along_session = False

    input_pins = [
        NodeInput(pin_type='exec'),
        NodeInput(pin_name='start',
                  pin_class=VGDtypes.Integer,
                  pin_type='data'),
        NodeInput(pin_name='end', pin_class=VGDtypes.Integer, pin_type='data')
    ]

    output_pins = [
        NodeOutput(pin_name='Loop Body', pin_type='exec'),
        NodeOutput(pin_name='index',
                   pin_class=VGDtypes.Integer,
                   pin_type='data'),
        NodeOutput(pin_name='Completed', pin_type='exec')
    ]

    def run_node(self):
        start = self.input(1)
        end = self.input(2)
        for i in range(start, end):
            self.output(1, i)
            self.exec_output(0)
            self.spawn_new_session()

        self.exec_output(2)


class ForLoopWithBreak(Node):

    package_name = 'Basic Control'
    node_title = 'ForLoopWithBreak'
    node_description = 'For loop with Break'

    refresh_along_session = False

    input_pins = [
        NodeInput(pin_type='exec'),
        NodeInput(pin_name='start',
                  pin_class=VGDtypes.Integer,
                  pin_type='data'),
        NodeInput(pin_name='end', pin_class=VGDtypes.Integer, pin_type='data'),
        NodeInput(pin_name='Break',pin_type='exec')
    ]

    output_pins = [
        NodeOutput(pin_name='Loop Body', pin_type='exec'),
        NodeOutput(pin_name='index',
                   pin_class=VGDtypes.Integer,
                   pin_type='data'),
        NodeOutput(pin_name='Completed', pin_type='exec')
    ]

    def run_node(self):

        self.loop_break = False

        if self.exec_input(3):
            self.loop_break = True
            return


        for i in range(self.input(1), self.input(2)):

            if self.loop_break:
                break

            self.output(1, i)
            self.exec_output(0)
            self.spawn_new_session()

        self.exec_output(2)


class WhileNode(Node):

    package_name = 'Basic Control'
    node_title = 'While'
    node_description = 'While loop'

    refresh_along_session = False

    input_pins = [
        NodeInput(pin_type='exec'),
        NodeInput(pin_name='condition',
                  pin_class=VGDtypes.Bool,
                  pin_type='data')
    ]

    output_pins = [
        NodeOutput(pin_name='Loop Body', pin_type='exec'),
        NodeOutput(pin_name='Completed', pin_type='exec')
    ]

    def run_node(self):

        while self.input(1):
            self.spawn_new_session()
            self.exec_output(0)

        self.exec_output(1)
