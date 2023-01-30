#coding:utf-8
import sys

sys.path.append('..')
from PySide6.QtWidgets import QFileDialog
from vg_node_port import NodeInput, NodeOutput
from vg_node import Node
from vg_dtypes import VGDtypes
import os
from widgets.PortWidget import StringArrayWdg, ReadFileWdg, WriteFileWdg


class IntegerNode(Node):
    package_name = 'Input Nodes'

    node_title = 'Integer'
    node_description = '输入节点'

    input_pins = [
        NodeInput(pin_name='',
                  pin_type='data',
                  pin_class=VGDtypes.Integer,
                  has_input=False)
    ]

    output_pins = [
        NodeOutput(pin_name='', pin_type='data', pin_class=VGDtypes.Integer)
    ]

    def run_node(self):

        self.output(0, int(self.input(0)))


class FloatNode(Node):
    package_name = 'Input Nodes'

    node_title = 'Float'
    node_description = '输入节点'

    input_pins = [
        NodeInput(pin_name='',
                  pin_type='data',
                  pin_class=VGDtypes.Float,
                  has_input=False)
    ]

    output_pins = [
        NodeOutput(pin_name='', pin_type='data', pin_class=VGDtypes.Float)
    ]

    def run_node(self):

        self.output(0, float(self.input(0)))


class BoolNode(Node):
    package_name = 'Input Nodes'

    node_title = 'Bool'
    node_description = '输入节点'

    input_pins = [
        NodeInput(pin_name='',
                  pin_type='data',
                  pin_class=VGDtypes.Bool,
                  has_input=False)
    ]

    output_pins = [
        NodeOutput(pin_name='', pin_type='data', pin_class=VGDtypes.Bool)
    ]

    def run_node(self):

        self.output(0, self.input(0))


class StringNode(Node):
    package_name = 'Input Nodes'

    node_title = 'String'
    node_description = '输入节点'

    input_pins = [
        NodeInput(pin_name='',
                  pin_type='data',
                  pin_class=VGDtypes.String,
                  has_input=False)
    ]

    output_pins = [
        NodeOutput(pin_name='', pin_type='data', pin_class=VGDtypes.String)
    ]

    def run_node(self):
        self.output(0, self.input(0))


class StringArray(Node):

    package_name = 'Input Nodes'

    node_title = 'StringArray'
    node_description = '输入节点'

    input_pins = [
        NodeInput(pin_name='',
                  pin_type='data',
                  pin_class=VGDtypes.Array,
                  has_input=False,
                  pin_widget=StringArrayWdg)
    ]

    output_pins = [
        NodeOutput(pin_name='', pin_type='data', pin_class=VGDtypes.Array)
    ]

    def run_node(self):

        self.output(0, self.input(0))


class FileNode(Node):

    package_name = 'Input Nodes'

    node_title = 'Select File (Read)'
    node_description = '文件路径输入节点'

    input_pins = [
        NodeInput(pin_name='',
                  pin_type='data',
                  pin_class=VGDtypes.File,
                  has_input=False,
                  pin_widget=ReadFileWdg)
    ]

    output_pins = [
        NodeOutput(pin_name='filepath',
                   pin_type='data',
                   pin_class=VGDtypes.String)
    ]

    def run_node(self):
        # 点击按钮可以设置文件路径，或者运行时进行选择
        # 弹出一个文件框，选择文件路径，然后设置到输出节点
        # filepath, filetype = QFileDialog.getOpenFileName(
        #     self._scene._view, '选择读取的文件', os.getcwd(), 'input file (*.*)')

        # if filepath == '':
        #     raise ValueError('未选择输入文件！')

        filepath = self.input(0)
        print(filepath)

        if not os.path.exists(filepath):
            raise ValueError(u'输入文件路径不存在！')

        self.output(0, self.input(0))


class SaveFileNode(Node):

    package_name = 'Input Nodes'

    node_title = 'Select File (Write)'
    node_description = '文件路径输入节点'

    input_pins = [
        NodeInput(pin_name='',
                  pin_type='data',
                  pin_class=VGDtypes.File,
                  has_input=False,
                  pin_widget=WriteFileWdg)
    ]

    output_pins = [
        NodeOutput(pin_name='filepath',
                   pin_type='data',
                   pin_class=VGDtypes.String)
    ]

    def run_node(self):
        # 点击按钮可以设置文件路径，或者运行时进行选择
        # 弹出一个文件框，选择文件路径，然后设置到输出节点
        filepath, filetype = QFileDialog.getSaveFileName(
            self._scene._view, '选择保存文件', os.getcwd(), 'input file (*.*)')

        if filepath == '':
            raise ValueError(u'未选要保存入文件！')

        self.output(0, filepath)
