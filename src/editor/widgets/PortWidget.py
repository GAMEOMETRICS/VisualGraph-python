#coding:utf-8
'''
    定义port对应的widget

'''
from abc import abstractmethod
from PySide6.QtWidgets import QWidget,QVBoxLayout,QLineEdit,QCheckBox,QPushButton,QHBoxLayout,QFileDialog
from PySide6.QtGui import QIntValidator,QDoubleValidator
from PySide6.QtCore import Qt
import os
from vg_config import NodeConfig
from widgets.BaseWidgets import AddButton,MinusButton


class PortWidget(QWidget):

    def __init__(self,parent=None):

        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground,True)
        self.widget_height = NodeConfig.port_icon_size
        self.setFixedWidth(60)

    @abstractmethod
    def getValueFromWidget(self):
        pass

    @abstractmethod
    def setWidgetValue(self,value):
        pass

# 只有一个输入框的情况
class InputWidget(PortWidget):

    def __init__(self, parent=None,constraint='str | float | int'):
        super().__init__(parent)

        self.vlayout = QVBoxLayout(self)
        self.vlayout.setContentsMargins(0,0,0,0)
        self.inputW = QLineEdit(parent=self)
        self.setFixedWidth(60)
        self.constraint = constraint
        if constraint == 'float':
            self.inputW.setValidator(QDoubleValidator())

        elif constraint == 'int':
            self.inputW.setValidator(QIntValidator())

        self.vlayout.addWidget(self.inputW)


    def getValueFromWidget(self):
        if self.constraint == 'float':
            return float(self.inputW.text())

        elif self.constraint == 'int':
            return int(self.inputW.text())

        return self.inputW.text()

    def setWidgetValue(self, value):
        return self.inputW.setText(str(value))

class IntInputWdg(InputWidget):

    def __init__(self, parent=None):
        super().__init__(parent, constraint='int')

class FloatInputWdg(InputWidget):

    def __init__(self, parent=None):
        super().__init__(parent, constraint='float')


class StringInputWdg(InputWidget):
    def __init__(self, parent=None):
        super().__init__(parent, constraint='str')


# check box的情况
class CheckboxWdg(PortWidget):
    def __init__(self, parent=None, constraint='str | float | int'):
        super().__init__(parent)

        self.vlayout = QVBoxLayout(self)
        self.vlayout.setContentsMargins(0, 0, 0, 0)
        self.checkWdg = QCheckBox(parent=self)
        # self.checkWdg.setFixedSize(25,25)
        self.setFixedWidth(30)
        self.setStyleSheet('height:25px;width:25px;')

        if constraint == 'float':
            self.checkWdg.setValidator(QDoubleValidator())

        elif constraint == 'int':
            self.checkWdg.setValidator(QIntValidator())

        self.vlayout.addWidget(self.checkWdg)

    def getValueFromWidget(self):
        return self.checkWdg.isChecked()

    def setWidgetValue(self, value):
        if isinstance(value,bool):
            self.checkWdg.setChecked(value)

# 数组列表
# TODO 需要将widget的改变变成pin的添加
class ArrayWdg(PortWidget):

    def __init__(self,subWidget_cls,parent=None):

        super().__init__(parent)
        self.subWdg_cls = subWidget_cls
        if not issubclass(subWidget_cls, PortWidget):
            raise ValueError(u'Array Widget 的 subwidget不是PortWidget的子类！')

        self.setFixedWidth(60)
        self.widget_height = NodeConfig.port_icon_size+10

        # 整体布局
        self.all_layout = QVBoxLayout(self)
        self.all_layout.setContentsMargins(0,0,0,0)

        # 上部分的widget部分
        self.upper_layout = QVBoxLayout()
        self.upper_layout.setContentsMargins(0, 0, 0, 0)
        self.inputWs:list[QWidget] = []
        self.addSubWidget()

        self.lower_layout = QHBoxLayout()
        self.lower_layout.setContentsMargins(0,0,0,0)

        self.add_btn = AddButton(15)
        self.remove_btn = MinusButton(15)

        self.lower_layout.addWidget(self.add_btn)
        self.lower_layout.addWidget(self.remove_btn)

        self.all_layout.addLayout(self.upper_layout)
        self.all_layout.addLayout(self.lower_layout)
        self.all_layout.setAlignment(Qt.AlignTop)

        # 添加wdg
        self.add_btn.clicked.connect(self.addSubWidget)
        self.remove_btn.clicked.connect(self.removeSubWidget)


    def getValueFromWidget(self):
        values = []
        for wdg in self.inputWs:
            values.append(wdg.getValueFromWidget())
        return values

    def setWidgetValue(self, value):

        if not isinstance(value,list):
            raise ValueError('ArrayWidget设置value时不是list类型！')

        toadd = len(value)-len(self.inputWs)
        for _ in range(toadd):
            self.addSubWidget()

        for i,v in enumerate(value):
            # load的时候需要根据list的size进行
            self.inputWs[i].setWidgetValue(v)


    def addSubWidget(self):
        subwdg = self.subWdg_cls(self)
        subwdg.setFixedHeight(NodeConfig.port_icon_size)
        self.upper_layout.addWidget(subwdg)
        self.inputWs.append(subwdg)
        self.widget_height += NodeConfig.port_icon_size+5

    # remove最后一个对象
    def removeSubWidget(self):
        if len(self.inputWs)>1:
            focus_index = -1
            for i, w in enumerate(self.inputWs):
                if w.hasFocus():
                    focus_index = i
            wdg = self.inputWs[focus_index]
            self.inputWs.remove(wdg)
            self.upper_layout.removeWidget(wdg)
            wdg.setParent(None)
            wdg.destroy(True)
            self.widget_height-=NodeConfig.port_icon_size+5

class IntegerArrayWdg(ArrayWdg):

    def __init__(self, parent=None):
        super().__init__(IntInputWdg, parent)

class FloatArrayWdg(ArrayWdg):

    def __init__(self,parent=None):
        super().__init__(FloatInputWdg,parent)

class StringArrayWdg(ArrayWdg):

    def __init__(self,parent=None):
        super().__init__(StringInputWdg,parent)

# 输入FileWidget
class FileInputWdg(PortWidget):

    def __init__(self, ftype='read | write', parent=None):
        super().__init__(parent)

        self.setFixedWidth(40)

        self.ftype = ftype

        self.vlayout = QVBoxLayout(self)
        self.vlayout.setContentsMargins(0, 0, 0, 0)
        self.select_btn = QPushButton('+',self)
        self.vlayout.addWidget(self.select_btn)

        self.filepath = ''
        self.select_btn.clicked.connect(self.selectFile)
        self.select_btn.setStyleSheet('font-weight:bold;font-size:18px;')

    def getValueFromWidget(self):

        if self.filepath =='':
            self.selectFile()

        return self.filepath

    def setWidgetValue(self, value):
        self.filepath = value

    def selectFile(self):
        if self.ftype == 'read':
            self.filepath, filetype = QFileDialog.getOpenFileName(
                self, '选择读取文件', os.getcwd(), 'input file (*.*)')

            if self.filepath == '':
                raise ValueError('未选要读取的文件！')

        elif self.ftype == 'write':

            self.filepath, filetype = QFileDialog.getSaveFileName(
            self, '选择保存文件', os.getcwd(), 'input file (*.*)')
            if self.filepath == '':
                raise ValueError('未选要保存的文件地址！')


class ReadFileWdg(FileInputWdg):

    def __init__(self, parent=None):
        super().__init__(ftype='read', parent=parent)


class WriteFileWdg(FileInputWdg):
    def __init__(self, parent=None):
        super().__init__(ftype='write', parent=parent)