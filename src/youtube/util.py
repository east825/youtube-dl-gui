# vim: fileencoding=utf-8

import platform

from PyQt4.QtGui import *
from PyQt4.QtCore import PYQT_VERSION_STR, QStringList
from PyQt4.QtCore import QT_VERSION_STR

u = unicode


def py2q_list(xs):
    return list(xs)


def q2py_list(xs):
    return map(unicode, xs)


ABOUT_MSG = """\
<html>
<h3>YouTube video player</h3>
<p>Python version: "{py_version}"<p>
<p>PyQt4 version: "{pyqt_version}"<p>
<p>Qt version: "{qt_version}"<p>
</html>
""".format(py_version=platform.python_version(),
           pyqt_version=PYQT_VERSION_STR,
           qt_version=QT_VERSION_STR)


def show_stub_message_box(parent):
    QMessageBox.information(parent, 'Not supported yet', 'This feature not supported')


def show_about_dialog(parent):
    QMessageBox.about(parent, 'About', ABOUT_MSG)


def create_button(text=None, icon=None, clicked=None,
                  checkable=False, toggled=None,
                  shortcut=None, parent=None):
    """Create QPushButton using specified parameters."""
    button = QPushButton(parent)
    if text is not None:
        button.setText(text)
    if icon is not None:
        button.setIcon(icon)
    button.setCheckable(checkable)
    if clicked is not None:
        button.clicked.connect(clicked)
    if toggled is not None:
        button.toggled.connect(toggled)
    return button


def create_action(text, icon=None, triggered=None,
                  checkable=False, toggled=None,
                  tooltip=None, shortcut=None,
                  parent=None):
    """Create QAction using specified parameters."""
    action = QAction(text, parent)
    if icon is not None:
        action.setIcon(icon)
    action.setCheckable(checkable)
    if toggled is not None:
        action.toggled.connect(toggled)
    if triggered is not None:
        action.triggered.connect(triggered)
    if shortcut is not None:
        action.setShortcut(shortcut)
    if tooltip is not None:
        action.setToolTip(tooltip)
    return action




