#coding:utf-8

import sys
from PySide6.QtWidgets import QApplication,QWidget,QVBoxLayout
from widgets.BaseWidgets import AddButton,MinusButton

if __name__ == "__main__":

    app = QApplication([])
    app.setStyle('fusion')

    qw = QWidget()

    layout = QVBoxLayout(qw)
    layout.addWidget(AddButton(25))
    layout.addWidget(MinusButton(25))

    qw.show()

    sys.exit(app.exec())