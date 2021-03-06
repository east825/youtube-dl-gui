# vim: fileencoding=utf-8

from __future__ import unicode_literals
from __future__ import print_function
import logging
import os

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from youtube.util import shrinked

ORGANIZATION_NAME = 'MyApps'
APPLICATION_NAME = 'youtube-dl-gui'

DEFAULT_DOWNLOAD_DIR = '.'
DEFAULT_NAME_FORMAT = '%(title)s'

LOG = logging.getLogger('youtube.settings')
PKG_PATH = os.path.dirname(__file__)

def get_download_dir():
    var = QSettings().value('Downloader/DefaultDirectory', DEFAULT_DOWNLOAD_DIR)
    return unicode(var.toString())


def get_name_format():
    var = QSettings().value('Downloader/NameFormat', DEFAULT_NAME_FORMAT)
    return unicode(var.toString())


def get_installation_directory():
    var = QSettings().value('InstallationDirectory', os.path.dirname(PKG_PATH))
    return unicode(var.toString())


def reset_to_defaults():
    settings = QSettings()
    settings.setValue('Downloader/DefaultDirectory', DEFAULT_DOWNLOAD_DIR)
    settings.setValue('Downloader/NameFormat', DEFAULT_NAME_FORMAT)
    settings.sync()
    return settings


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setWindowTitle('Settings')

        name_format = get_name_format()
        self.name_format_edit = QLineEdit(name_format)
        self.name_format_edit.setMinimumWidth(300)
        self.name_format_edit.setPlaceholderText('File name format')
        name_format_label = QLabel('Name &format:')
        name_format_label.setBuddy(self.name_format_edit)

        download_dir = get_download_dir()
        self.download_dir_edit = QLineEdit(download_dir)
        self.download_dir_edit.setPlaceholderText('Default download directory')
        download_dir_label = QLabel('Download &directory:')
        download_dir_label.setBuddy(self.download_dir_edit)
        dir_picker_button = QToolButton(self)
        dir_picker_button.setText('…')

        def show_dir_picker():
            path = QFileDialog.getExistingDirectory(self,
                                                    'Choose download directory',
                                                    self.download_dir_edit.text())
            self.download_dir_edit.setText(path)


        dir_picker_button.clicked.connect(show_dir_picker)

        grid = QGridLayout()
        grid.addWidget(name_format_label, 0, 0)
        grid.addWidget(self.name_format_edit, 0, 1, 1, 2)
        grid.addWidget(download_dir_label, 1, 0)
        grid.addWidget(self.download_dir_edit, 1, 1)
        grid.addWidget(dir_picker_button, 1, 2)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        hbox = QVBoxLayout()
        hbox.addLayout(grid)
        hbox.addWidget(button_box)

        self.setLayout(hbox)

    def accept(self):
        # TODO: add settings validation
        settings = QSettings()
        settings.setValue('Downloader/NameFormat', self.name_format_edit.text())
        settings.setValue('Downloader/DefaultDirectory',
                          self.download_dir_edit.text())
        super(SettingsDialog, self).accept()