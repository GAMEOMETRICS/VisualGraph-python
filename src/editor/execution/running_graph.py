#coding:utf-8
import logging
from PySide6.QtCore import QObject,Signal
from vg_dtypes import VGDtypes
from tools.VariableManager import Variable, VariableManager
from nodes.ActionNode import BeginNode


class RunningGraph(QObject):

    finished = Signal()

    def __init__(self, running_nodes, vars):

        super().__init__()
        self.variableManager = VariableManager()
        self.init_variManager(vars)
        self.clear_graph()
        # self.running_nodes = running_nodes

        self._begin_node = None
        self._has_begin_node = False

        for node in running_nodes:
            self.add_running_node(node)

    def init_variManager(self,vars):
        for var in vars:
            self.variableManager.addVariable(Variable.fromJson(var))

    def add_running_node(self, node):
        node.snew_session.connect(self.new_session)
        node.set_variableManager(self.variableManager)
        node.variable_value_changed.connect(self.changeVarValue)
        self.running_nodes.append(node)
        self.finished.connect(node.finish_thread)

        if isinstance(node, BeginNode):
            self._begin_node = node
            self._has_begin_node = True

    def has_begin_node(self):
        return self._has_begin_node

    def run_graph(self):
        self.new_session(0)
        self._begin_node.run_node_in_back()
        self.finished.emit()

    def clear_graph(self):
        self.running_nodes = []
        self.variableManager.resetAllVariables()

    def new_session(self, session_id):
        for node in self.running_nodes:
            node.new_session(session_id)
            # logging.info(f'new session,{node.node_title}')

    def changeVarValue(self, name, value):
        # logging.info(f'change variable {name},{value}')
        self.variableManager.setVariableValue(name, value)
