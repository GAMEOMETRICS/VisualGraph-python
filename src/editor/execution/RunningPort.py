#coding:utf-8
from PySide6.QtCore import Signal,QObject

class RunningPin(QObject):

    def __init__(self,pin_name,pin_class,pin_type,pin_value):

        super().__init__()

        self.pin_name = pin_name
        self.pin_class = pin_class
        self.pin_type = pin_type
        self.pin_value = pin_value

        self.edges = []
        self.connected_pins = []

        self.is_value_set = False

        self.parent_node = None
    
    def clear(self):
        self.edges = []
        self.connected_pins = []
    
    def get_pin_name(self):
        return self.pin_name

    def get_pin_value(self):
        return self.pin_value

    def set_pin_value(self,value):
        self.is_value_set = True
        self.pin_value = value

    def set_parent_node(self,node):
        self.parent_node = node

    def get_parent_node(self):
        return self.parent_node

    def get_connected_pins(self):
        return self.connected_pins

    def add_connected_pin(self,running_pin):
        return self.connected_pins.append(running_pin)

    def is_valued(self):
        return self.is_value_set

    def add_edge(self,running_edge,connected_pin):
        self.edges.append(running_edge)
        self.connected_pins.append(connected_pin)
        # 并且需要通知父节点add edge,以及add node
        self.get_parent_node().add_edge(running_edge)
        self.get_parent_node().add_connected_node(
            connected_pin.get_parent_node())

    def new_session(self,session_id):
        self._session_id = session_id

        if len(self.edges)>0:
            self.is_value_set = False 
            self.pin_value = None 
