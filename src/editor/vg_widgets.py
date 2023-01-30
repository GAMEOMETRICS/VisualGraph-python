#coding:utf-8

from PySide6.QtWidgets import QLineEdit, QWidget, QComboBox,QVBoxLayout,QTextBrowser,QMenu
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from tools.QssLoader import QSSLoadTool


class LoggerWidget(QWidget):

    def __init__(self,parent=None):

        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(2,2,2,0)
        self.setAttribute(Qt.WA_StyledBackground)
        self.setObjectName('logger')
        QSSLoadTool.setStyleSheetFile(self,'./src/editor/qss/log.qss')

        self.browser = QTextBrowser(self)
        self.browser.setStyleSheet('font-size:16px;color:#c4c4c4;font-family:Consolas;')
        self.browser.setContextMenuPolicy(Qt.CustomContextMenu)
        self.browser.customContextMenuRequested.connect(self.showCustomMenu)

        self.verticalBar = self.browser.verticalScrollBar()

        self.layout.addWidget(self.browser)

        self.init_menu()

    def init_menu(self):
        self.menu = QMenu(self)
        self.selectAllAction = QAction('Select All',self.menu)
        self.selectAllAction.triggered.connect(self.select_all)

        self.copyAction = QAction('Copy',self.menu)
        self.copyAction.triggered.connect(self.copy_selected)

        self.clearAction = QAction('Clear',self.menu)
        self.clearAction.triggered.connect(self.clear_log)


        self.menu.addAction(self.selectAllAction)
        self.menu.addAction(self.copyAction)
        self.menu.addAction(self.clearAction)


    def log(self,text,color='#c4c4c4'):
        self.browser.append(f'<span style="color:{color};">{text.strip()}</span>')
        self.verticalBar.setValue(self.verticalBar.maximum())

    def showCustomMenu(self,qPoint):
        self.menu.exec(self.mapToGlobal(qPoint))

    def select_all(self):
        self.browser.selectAll()

    def clear_log(self):
        self.browser.clear()

    def copy_selected(self):
        self.browser.copy()
