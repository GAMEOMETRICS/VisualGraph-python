#coding:utf-8

from execution.RunningPort import RunningPin

class RunningEdge:

    def __init__(self,source_pin,des_pin):

        super().__init__()

        self.source_pin = source_pin
        self.des_pin = des_pin
        self.update_pin_edge()
    
    def update_pin_edge(self):
        self.source_pin.add_edge(self,self.des_pin)
        self.des_pin.add_edge(self,self.source_pin)
    
    def get_source_pin(self):
        return self.source_pin

    def get_des_pin(self):
        return self.des_pin
    
    def set_source_pin(self,source_pin:RunningPin):
        self.source_pin = source_pin
    
    def set_des_pin(self,des_pin:RunningPin):
        self.des_pin = des_pin

    
