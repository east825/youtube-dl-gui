# vim: fileencoding=utf-8

import platform

from PyQt4.QtGui import *
from PyQt4.QtCore import QT_VERSION_STR
from PyQt4.QtCore import PYQT_VERSION_STR

class StringListDialog(QDialog):
    def __init__(self, parent, items):
        QDialog.__init__(self, parent)
        layout = QVBoxLayout()
        list_widget = QListWidget()
        for label in map(unicode, items):
            list_widget.addItem(label)
        layout.addWidget(list_widget, 1)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        layout.addWidget(buttons)
        self.setLayout(layout)