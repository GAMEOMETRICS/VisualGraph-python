#coding:utf-8
'''
visual graph的入口

'''

import sys
from PySide6.QtGui import QIcon
from PySide6.QtCore import QThread
from PySide6.QtWidgets import QApplication
from vg_editor import VisualGraphWindow
from tools.vg_tools import EmittingStream, PrintHelper,StdReceiver
from tools.QssLoader import QSSLoadTool,resource_path


if __name__ == "__main__":

   
    app = QApplication([])
    app.setStyle('fusion')
    QSSLoadTool.setStyleSheetFile(app,'./src/editor/qss/main.qss')

    try:
        editor = VisualGraphWindow()
        editor.setWindowIcon(QIcon(resource_path('./src/editor/icons/icon.ico'))) 
        editor.show()
    except ValueError as e:
        PrintHelper.printError(e)

    sys.exit(app.exec())
