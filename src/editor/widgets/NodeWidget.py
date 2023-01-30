#coding:utf-8
'''
    定义Node的widget

'''
from abc import abstractmethod
from PySide6.QtWidgets import QWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QLabel
from PySide6.QtGui import QIntValidator, QDoubleValidator
from PySide6.QtCore import Signal,Qt
import pandas as pd

class NodeWidget(QWidget):
    def __init__(self, parent=None):

        super().__init__(parent)

        self.content_w = self.setup_widget()
        self.vlayout = QVBoxLayout(self)
        self.vlayout.setContentsMargins(0, 0, 0, 0)
        self.label = QLabel('Port:')
        self.vlayout.addWidget(self.label)
        self.vlayout.addWidget(self.content_w)

        self.nwidth = 10
        self.nheight = 20
        # 不能设置固定高估 否则不能改
        # self.setFixedHeight(30)
        # self.setAttribute(Qt.WA_TranslucentBackground, True)

    @abstractmethod
    def preview(self):
        '''Preview的方法，点击preview之后自动运行'''
        pass

    def set_preview_port(self, port):
        self.preview_port = port
        self.label.setText(f'   Port:{port._port_label}')

    @abstractmethod
    def setup_widget(self) -> QWidget:
        '''设置widget'''
        return QWidget()

    def get_widget_width(self):
        return self.nwidth

    def get_widget_height(self):
        return self.nheight

    @abstractmethod
    def clear(self):
        pass


class TablePreviewWidget(NodeWidget):

    previewSig = Signal(int, int)

    def preview(self):

        # 清空table
        self.tableW.clear()

        # 获取对应的值
        table_v = self.preview_port.get_value_from_connected_port()

        if table_v is None:
            print('请先运行graph,然后点击预览按钮！')
            return

        assert (type(table_v).__name__ == 'DataFrame')
        headers = table_v.columns
        num_of_column = len(headers)

        # 初始化Table
        self.tableW.setColumnCount(num_of_column)
        self.tableW.setHorizontalHeaderLabels(headers)

        if table_v.shape[0] < self.maximum_per_page:
            self.sample_per_page = table_v.shape[0]
            self.multi = False
        else:
            self.sample_per_page = self.fixed_per_page
            self.multi = True

        self.tableW.setRowCount(self.sample_per_page)

        table_height = 40
        for index, row in table_v[self.page * self.sample_per_page:
                        (self.page + 1) * self.sample_per_page].iterrows():

            table_height += self.tableW.rowHeight(index)

            for col, h in enumerate(headers):
                self.tableW.setItem(index, col, QTableWidgetItem(str(row[h])))
                self.tableW.resizeRowsToContents()
                self.tableW.resizeColumnsToContents()

        table_width = 30
        for i in range(num_of_column):
            table_width += self.tableW.columnWidth(i)

        self.tableW.setFixedSize(table_width,table_height)
        self.setFixedSize(table_width,table_height)

        # 如果multi，则加入翻页按钮

    def clear(self):
        self.tableW.clear()


    def setup_widget(self) -> QWidget:
        self.tableW = QTableWidget(self)
        self.page = 0
        self.sample_per_page = 100
        self.fixed_per_page = 10
        self.maximum_per_page = 30
        self.multi = True
        # self.tableW.horizontalHeader().setStretchLastSection(True)
        return self.tableW
