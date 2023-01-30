#coding:utf-8
'''
把这个替换掉
'''

from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QFontMetrics
from PySide6.QtCore import  QFileInfo, QFile
import re
import os 
import sys

class QSSLoadTool:
    @staticmethod
    def setStyleSheetFile(w: QWidget, filePath: str):
        filePath = resource_path(filePath)
        abs_filepath = QFileInfo(filePath).absoluteFilePath()
        qss_file = QFile(abs_filepath)
        qss_file.open(QFile.ReadOnly)
        # 需要将QByteArray转成str utf-8的编码
        qss_str = str(qss_file.readAll(), 'utf-8')
        qss_str = QSSLoadTool.replace_url_file(qss_str)
        w.setStyleSheet(qss_str)

    @staticmethod
    def replace_url_file(qss_str: str) -> str:
        p = re.compile("url *[(](.*?)[)]", re.S)
        c_l = re.findall(p, qss_str)
        for item in c_l:
            if not item.startswith(":"):
                new_item = resource_path(item).replace("'", '').replace(
                    '\\', '/').replace('/./', '/')
                qss_str = qss_str.replace(item, new_item)
        return qss_str


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    path = os.path.join(base_path, relative_path)
    return path
