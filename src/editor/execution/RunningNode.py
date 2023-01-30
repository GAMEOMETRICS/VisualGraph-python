#coding:utf-8

import logging
from typing import Callable, overload
from PySide6.QtCore import Signal,QObject
from tools.vg_tools import PrintHelper
from execution.RunningPort import RunningPin
from typing import Any

from vg_node_port import Pin,NodePort
from vg_node import Node

class RunningNode(QObject):
    '''
        Node创建Running Node， 创建时，如果widget是可见的，就将value设置为widget的值。
    '''
    # 开始运行信号
    running_start = Signal()
    # 运行错误
    running_error = Signal()
    # 运行完成
    running_finished = Signal()
    # 输入节点值设置
    inport_value_set = Signal(int,Any)
    # 输出节点值设置
    outport_value_set = Signal(int,Any)
    # 运行进度 progress/total
    running_progress = Signal(int,int)
    # 变量值改变
    variable_value_changed = Signal(str,Any)

    # 一些设置,用于初始化graph NODE
    stored = True
    package_name = ''
    node_title = ''
    node_description = ''

    # 这里的pin是静态变量Pin用于定义每一个Node的port
    input_pins:list[Pin] = None
    output_pins:list[Pin] = None

    def __init__(self,node_title):

        super().__init__()
        # 自我检查参数
        self.is_validate()

        self.node_title = node_title
        self.in_pins:list[RunningPin] = []
        self.out_pins:list[RunningPin] = []
        self.connected_nodes = []
        self.edges = []

        self.run_node:Callable = None

    def is_validate(self):

        if self.node_title == '':
            PrintHelper.printError(f'Node {self.node_title} init: node title could not be empty')
            return False

        if self.node_title is None:
            PrintHelper.printError(f'Node {self.node_title} init: node title could not be None')
            return False

        if self.input_pins is None:
            self.input_pins = []

        if len(self.output_pins) is None:
            self.output_pins = []

        return True

    def init_graphNode(self):

        # 这里直接创建Node
        node_cls = type(self.__class__,(Node,),{
            'stored':self.stored,
            'package_name':self.package_name,
            'node_title':self.node_title,
            'node_description':self.node_description,
            'input_pins':self.input_pins,
            'output_pins':self.output_pins
        })

        graph_node = node_cls()

        return graph_node

    def init_in_and_out_pins(self,in_pins,out_pins):

        # 这里的pin是running pin，用于各个存储各个实例
        self.input_running_pins:list[RunningPin] = in_pins
        self.output_running_pins:list[RunningPin] = out_pins

        for pin in self.in_pins:
            pin.set_parent_node(self)

        for pin in self.out_pins:
            pin.set_parent_node(self)

    def add_connected_node(self,running_node):
        self.connected_nodes.append(running_node)

    def add_edge(self,edge):
        self.edges.append(edge)

    def get_input_pin(self,index):
        return self.input_running_pins[index]

    def get_output_pin(self,index):
        return self.output_running_pins[index]

    # running in back
    def run_node_in_back(self):
        self.running_start.emit()
        self.run_node()
        self.running_finished.emit()

    # TODO 需要确认 graph执行前 已经将running的值设置好了，主要是input pins的
    def input(self,i):
        # 这里需要将widget value设置好
        pin = self.get_input_pin(i)

        if pin.pin_type != 'data':
            self.running_error.emit()
            raise ValueError(f'Node {self.node_title} {i+1}th input pin is not a data pin.')

        # 首先获得widget的默认值
        pin_value = pin.get_pin_value()
        # 如果这个值没有设置，那么就需要从之前的node获取
        if pin_value is None:
            connected_pins:list[RunningPin] = pin.get_connected_pins()
            # 如果没有连接node，抛出错误
            if len(connected_pins)==0:
                self.running_error.emit()
                raise ValueError(f'{self.node_title} {i+1}-th input pin should have an connected node.')
            # 只能有一个前项node
            elif len(connected_pins) == 1:
                connected_pin = connected_pins[0]
                # 从connected pin获得值，如果该pin没有设置值，那么就需要运行这个node，进行值的设置
                if not connected_pin.is_valued():
                    pre_node:RunningNode = connected_pin.get_parent_node()
                    pre_node.run_node_in_back()
                # 从连接的pin获得值
                pin_value = connected_pin.get_pin_value()
            # 多个前项node，说明设置错误了
            else:
                self.running_error.emit()
                raise ValueError(f'{self.node_title} {i+1}-th input pin should have value.')

    def output(self,i,value):
        pin = self.get_output_pin(i)
        if pin.pin_type != 'data':
            self.running_error.emit()
            raise ValueError(
                f'Node {self.node_title} {i+1}th output pin is not a data pin.')

        return pin.set_pin_value(value)

    def exec_input(self,i):

        pin = self.get_input_pin(i)
        if pin.pin_type != 'exec':
            raise ValueError(
                f'{self.node_title} {i+1}-th input pin is not a execution pin.'
            )

        return pin.get_pin_value()

    def exec_output(self,i):

        pin = self.get_output_pin(i)

        if pin.pin_type != 'exec':
            raise ValueError(f'{self.node_title} {i+1}-th output pin is not a execution pin.')
        else:
            pins:list[RunningPin] =  pin.get_connected_pins()

            if pins is not None and len(pins)==1:
                # 获得连接的node然后运行
                pin = pins [0]
                # 执行端口设置为真
                pin.set_pin_value(True)
                connected_node:RunningNode = pin.get_parent_node()
                connected_node.run_node_in_back()

    # TODO确保执行之前每一个node都设置了variableManager,只进行读取操作
    def set_variableManager(self,variableManager):
        self.variableManager = variableManager

    def getVariableValue(self, name):
        pin_name = self.get
        return self.variableManager.getVariableValue(name)

    def setVariableValue(self, name,value):
        self.variable_value_changed.emit(name,value)

    def new_session(self,session_id):

        self._session_id = session_id

        for pin in self.input_running_pins:
            pin.new_session()

    

