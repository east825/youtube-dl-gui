# vim: fileencoding=utf-8

import platform

from PyQt4.QtGui import QMessageBox
from PyQt4.QtCore import PYQT_VERSION_STR
from PyQt4.QtCore import QT_VERSION_STR

u = unicode

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

