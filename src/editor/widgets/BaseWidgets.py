#coding:utf-8
'''
一些基础的组件

'''
from PySide6.QtWidgets import QPushButton,QApplication
from PySide6.QtCore import Qt

from tools.QssLoader import QSSLoadTool

class AddButton(QPushButton):

    def __init__(self,size,parent=None):

        super().__init__(parent=parent)
        self.setAttribute(Qt.WA_StyledBackground)
        self.setObjectName('AddButton')
        QSSLoadTool.setStyleSheetFile(self,'./src/editor/qss/base.qss')
        self.setFixedSize(size,size)


class MinusButton(QPushButton):
    def __init__(self, size, parent=None):

        super().__init__(parent=parent)
        self.setAttribute(Qt.WA_StyledBackground)
        self.setObjectName('MinusButton')
        QSSLoadTool.setStyleSheetFile(self, './src/editor/qss/base.qss')
        self.setFixedSize(size, size)
