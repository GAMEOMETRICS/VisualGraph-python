#This key is not known by any other names.coding:utf-8

from dataclasses import replace
from distutils.debug import DEBUG
import sys
from xml.etree.ElementTree import TreeBuilder
from PySide6.QtWidgets import QWidget, QLabel, QLineEdit, QVBoxLayout, QApplication, QGraphicsItem, QGraphicsObject, QComboBox
from PySide6.QtGui import QMouseEvent, QKeyEvent, QFontMetrics, QFont, QPainter, QBrush, QPen, QColor, QPolygonF, QFontMetrics, QIntValidator, QDoubleValidator
from PySide6.QtCore import Qt, QRectF, QPointF, Signal, QObject, QFileInfo, QFile
from vg_dtypes import VGDtypes
from vg_config import GroupConfig
from tools.VariableManager import Variable

import json
import os
import re

import time
import logging


class EditableLabel(QWidget):

    textchanged_signal = Signal(int)

    def __init__(self, text='', parent=None):

        super().__init__(parent)

        self.text = text

        self.label = QLabel(self)
        self.label.setText(self.text)

        self.line_edit = QLineEdit(self)

        self.vlayout = QVBoxLayout(self)
        self.vlayout.setContentsMargins(0, 0, 0, 0)

        self.vlayout.addWidget(self.label)
        self.vlayout.addWidget(self.line_edit)

        self.setLayout(self.vlayout)
        self.line_edit.setHidden(True)

        self.is_edit_mode = False
        self.label.mouseDoubleClickEvent = self.labelClicked

        self.setStyleSheet(
            'QWidget{ background-color:#00000000; }  QLabel { font-family:Arial; font-size:20px; color:#ddd; background-color:#00000000; } QLineEdit{ font-size:18px; color:#fff; }'
        )

        self.line_edit.returnPressed.connect(self.update_edit_label)
        self.line_edit.editingFinished.connect(self.update_edit_label)
        self.line_edit.textChanged.connect(self.change_le_width)

        self.fm = QFontMetrics(QFont('Arail', 16))

    def change_le_width(self, text):
        self.line_edit.setFixedWidth(self.fm.boundingRect(text).width() + 10)

    def labelClicked(self, event: QMouseEvent):

        if event.button() == Qt.LeftButton:
            self.enable_edit_mode()

        # return super().mouseDoubleClickEvent(event)

    def keyPressEvent(self, event):

        # if event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return:
        #     self.update_edit_label()

        if event.key() == Qt.Key_Escape:
            self.cancel_edit()

        super().keyPressEvent(event)

    def enable_edit_mode(self):

        if self.is_edit_mode:
            return

        self.is_edit_mode = True
        # 隐藏Label
        self.label.setHidden(True)
        self.line_edit.setText(self.label.text())
        self.line_edit.setHidden(False)
        self.line_edit.setFocus(Qt.MouseFocusReason)
        self.line_edit.selectAll()

    def update_edit_label(self):

        self.label.setText(self.line_edit.text())

        self.is_edit_mode = False
        self.line_edit.setHidden(True)
        self.label.setHidden(False)

        self.textchanged_signal.emit(
            self.fm.boundingRect(self.line_edit.text()).width())

    def cancel_edit(self):
        self.is_edit_mode = False
        self.line_edit.setHidden(True)
        self.label.setHidden(False)

    def get_text(self):
        return self.label.text()


class ItemSizeGrip(QGraphicsObject):

    resize_signal = Signal(QGraphicsItem.GraphicsItemChange, QPointF)

    def __init__(self,
                 min_width=50,
                 min_height=50,
                 color=GroupConfig.group_title_bak_color,
                 parent=None):
        super().__init__(parent)

        self._color = color
        self._brush = QBrush(QColor(self._color))

        self._min_pos = [min_width, min_height]

        self.setCursor(Qt.SizeFDiagCursor)

        self.setFlags(QGraphicsItem.ItemIsMovable
                      | QGraphicsItem.ItemIsSelectable
                      | QGraphicsItem.ItemSendsGeometryChanges)

    def set_top_left_pos(self, pos):
        self._min_pos = pos

    def set_pos(self, pos):
        self.setPos(pos[0], pos[1])

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, 10, 10)

    def paint(self, painter: QPainter, option, widget):

        painter.setPen(Qt.NoPen)
        painter.setBrush(self._brush)

        # 画出三角形
        polygon = QPolygonF()
        polygon.append(QPointF(10, 0))
        polygon.append(QPointF(10, 10))
        polygon.append(QPointF(0, 10))

        painter.drawPolygon(polygon)

    def itemChange(self, change, value):

        if change == QGraphicsItem.ItemPositionChange:

            if value.x() <= self._min_pos[0]:
                value = QPointF(self._min_pos[0], value.y())

            if value.y() <= self._min_pos[1]:
                value = QPointF(value.x(), self._min_pos[1])

            self.resize_signal.emit(change, value)

        return super().itemChange(change, value)


class AttrWidgetFactory:

    INTEGER_INPUT = 'II'
    FLOAT_INPUT = 'FI'
    STRING_INPUT = 'SI'
    SELECTOR = 'SELECTOR'

    @staticmethod
    def bindWidget(widget_type, data, handler, parent=None):

        if widget_type == AttrWidgetFactory.INTEGER_INPUT or widget_type == AttrWidgetFactory.FLOAT_INPUT or widget_type == AttrWidgetFactory.STRING_INPUT:
            return AttrWidgetFactory.bindInputWidget(widget_type, data,
                                                     handler, parent)

        elif widget_type == AttrWidgetFactory.SELECTOR:
            return AttrWidgetFactory.bindSelectorWidget(
                widget_type, data, handler, parent)

    '''
        生成几种常用的widget，并且绑定值发生改变之后的函数

        data = {
            'value':width
        }

    '''

    @staticmethod
    def bindInputWidget(widget_type, data, handler, parent=None):

        widget = QLineEdit(parent=parent)

        if widget_type == AttrWidgetFactory.INTEGER_INPUT:
            widget.setValidator(QIntValidator())
        elif widget_type == AttrWidgetFactory.FLOAT_INPUT:
            widget.setValidator(QDoubleValidator())

        widget.setText(str(data['value']))
        func = data['func']
        widget.editingFinished.connect(lambda: (handler(widget.text(), func)))

        return widget

    '''
        combox的数据
        data = {
            'items':[{ 
                'icon':QICON,
                'value':Str},
            ],'current':str,'hasIcon':False}
    
    '''

    def bindSelectorWidget(widget_type, data, handler, parent=None):

        widget = QComboBox(parent)

        items = data['items']
        current_item = data['current']
        has_icon = data['hasIcon']
        func = data['func']
        selected_index = 0
        for i, item in enumerate(items):

            if has_icon:
                widget.addItem(item['icon'], item['value'])
            else:
                widget.addItem(item['value'])

            if item['value'] == current_item:
                selected_index = i

        widget.setCurrentIndex(selected_index)

        widget.currentIndexChanged.connect(
            lambda x: handler(items[x]['value'], func))

        return widget


# 定义属性,属性是对一个对象属性的描述，及其widget
'''
  attr_name:变量名
  attr_type:String
  attr_widget:QLineEdit

'''


class VGAttr:
    def __init__(self, attr_name, value, widget_type, data):
        self.attr_name = attr_name
        self.attr_value = value
        self.widget_type = widget_type
        self.data = data

    def bindWidget(self, handler, parent):
        return AttrWidgetFactory.bindWidget(self.widget_type, self.data,
                                            handler, parent)

    def getAttrName(self):
        return self.attr_name

    def getAttrValue(self):
        return self.attr_value


class VGAttrSet:
    def __init__(self):
        self.attrs: list[VGAttr] = []

    def addAttr(self, attr: VGAttr):
        self.attrs.append(attr)

    def getAttrs(self):
        return self.attrs

    def getAttrCount(self):
        return len(self.attrs)

    def getAttrAt(self, index: int) -> VGAttr:
        return self.attrs[index]


class VariableAttrSet(VGAttrSet):
    def __init__(self, variable: Variable):

        super().__init__()

        #'attr:name,type,group'
        #'value'
        attr_name = VGAttr('Variable Name',
                           variable.getName(),
                           AttrWidgetFactory.STRING_INPUT,
                           data={
                               'value': variable.getName(),
                               'func': variable.setName
                           })
        attr_type = VGAttr('Variable Type',
                           variable.getType(),
                           AttrWidgetFactory.SELECTOR,
                           data={
                               'hasIcon': True,
                               'current': variable.getType().__name__,
                               'items': VGDtypes.get_dtypes_icons(),
                               'func': variable.setType
                           })
        attr_group = VGAttr('Group',
                            variable.getGroup(),
                            AttrWidgetFactory.SELECTOR,
                            data={
                                'hasIcon': False,
                                'current': variable.getGroup(),
                                'items': [{
                                    'value': 'Default'
                                }],
                                'func': variable.setGroup
                            })

        self.addAttr(attr_name)
        self.addAttr(attr_type)
        self.addAttr(attr_group)


# 输入输出流的信号转发
class EmittingStream(QObject):
    def __init__(self, queue):
        super().__init__()
        self.queue = queue

    def write(self, text):
        self.queue.put(str(text))


class StdReceiver(QObject):

    std = Signal(list)

    def __init__(self, queue):
        super().__init__()

        self.queue = queue
        self.emit_time = time.time()
        self.buffs = []

    def printStr(self):
        while True:
            current_time = time.time()

            if (self.queue.empty() and len(self.buffs) > 0) or (
                    current_time - self.emit_time > 2 and len(self.buffs) > 0):
                self.std.emit(self.buffs)
                self.buffs = []
                self.emit_time = current_time

            text = self.queue.get()
            self.buffs.append(text)


class PrintHelper:

    DEBUG_MODE = True

    @staticmethod
    def print(text, color='#fff'):
        data = {}
        data['color'] = color
        data['text'] = text

        print(json.dumps(data))

    @staticmethod
    def printError(text):
        text = f'ERROR:  {text}'
        PrintHelper.print(text, color='#f44')

    @staticmethod
    def printWarning(text):
        text = f'WARNNING:  {text}'
        PrintHelper.print(text, color='#fa0')

    @staticmethod
    def debugPrint(text):
        if PrintHelper.DEBUG_MODE:
            text = f'DEBUG:  {text}'
            PrintHelper.print(text, '#9fe')

    def printInfo(text):
        text = f'INFO: {text}'
        PrintHelper.print(text, '#c4c4c4')






if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    widget = EditableLabel('hhhhhhhhhhhhhhh')
    widget.show()
    widget.move(100, 100)
    widget.resize(300, 45)
    sys.exit(app.exec())
