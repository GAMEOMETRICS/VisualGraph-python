#coding:utf-8
'''
定义一个graph Runner

'''

from PySide6.QtCore import QObject,Signal
from time import sleep

class VGRunner(QObject):

    progress = Signal(int)
    finished = Signal()

    def __init__(self,func,*args,**kwds):
        super().__init__()
        self.func = func 
        self.args = args 
        self.kwds = kwds

    def run(self):
        try:
            self.func(*self.args,**self.kwds)
        except ValueError as e:
            print(e)
        finally:
            self.finished.emit()




