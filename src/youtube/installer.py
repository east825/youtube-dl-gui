# vim: fileencoding=utf-8

from __future__ import unicode_literals
from __future__ import print_function
import os

import sys
import platform

from PyQt4.QtCore import *
from PyQt4.QtGui import *
import time
from youtube.util import create_button

YOUTUBE_DL_DOWNLOAD_URL = ''


def get_default_installation_dir():
    app_name = unicode(QApplication.applicationName())
    org_name = unicode(QApplication.organizationName())
    system_name = platform.system()
    if system_name == 'Windows':
        base_dir = 'C:\\Program Files'
    else:
        base_dir = os.path.expanduser('/usr/local/lib')
    path = os.path.join(base_dir, org_name, app_name)
    return path


class InstallationDirectoryPage(QWizardPage):
    def __init__(self, parent=None):
        super(InstallationDirectoryPage, self).__init__(parent)
        self.setTitle('Choose installation directory')
        grid = QGridLayout()
        grid.addWidget(QLabel('Installation directory:'), 0, 0)

        self.path_edit = QLineEdit(get_default_installation_dir())
        self.registerField('InstallationDirectory*', self.path_edit)
        self.path_edit.textChanged.connect(self.completeChanged)
        grid.addWidget(self.path_edit, 0, 1)

        self.dir_picker = QToolButton(self)
        self.dir_picker.setText('…')
        self.dir_picker.pressed.connect(self.show_dir_picker)
        grid.addWidget(self.dir_picker, 0, 2)

        self.setLayout(grid)

    def initializePage(self):
        super(InstallationDirectoryPage, self).initializePage()
        self.path_edit.setText(get_default_installation_dir())


    def show_dir_picker(self):
        path = QFileDialog.getExistingDirectory(self,
                                                'Choose installation directory',
                                                self.path_edit.text())
        self.path_edit.setText(path)

    def isComplete(self):
        return True
        path = unicode(self.path_edit.text())
        if not os.path.isdir(path):
            return False
        return super(InstallationDirectoryPage, self).isComplete()


class YotubeDLDownloadPage(QWizardPage):
    def __init__(self, parent=None):
        super(YotubeDLDownloadPage, self).__init__(parent)
        self.setTitle('Download youtube-dl')
        self.setSubTitle('You can optionally download actual version of '
                         'youtube-dl if you wish')

        main_grid = QGridLayout()
        main_grid.addWidget(QLabel('Download youtube-dl:'), 0, 0)

        self.download_check = QCheckBox()
        self.download_check.toggled.connect(self.show_extension)
        hbox = QHBoxLayout()
        hbox.addWidget(self.download_check)
        hbox.addStretch(1)
        main_grid.addLayout(hbox, 0, 1)

        # extension components
        self.download_button = create_button(
            text='Download',
            clicked=self.download,
            parent=self
        )
        self.progress = QProgressBar(self)

        # extension layout setup
        main_grid.addItem(QSpacerItem(0, 20), 1, 0)
        main_grid.addWidget(self.download_button, 2, 0)
        main_grid.addWidget(self.progress, 2, 1)
        self.setLayout(main_grid)
        self.show_extension(False)

    def show_extension(self, visible):
        self.download_button.setVisible(visible)
        self.progress.setVisible(visible)


    def download(self):
        install_dir = unicode(self.field('InstallationDirectory').toString())
        for i in range(100):
            QApplication.processEvents(QEventLoop.AllEvents, 100)
            time.sleep(0.1)
            self.progress.setValue(i + 1)


class FinalPage(QWizardPage):
    def __init__(self, parent=None):
        super(FinalPage, self).__init__(parent)
        self.setTitle('Installation completed')
        self.setSubTitle('Thank you for installing youtube-dl-gui')
        self.launch_check = QCheckBox()
        self.readme_check = QCheckBox()
        form = QFormLayout()
        form.addRow('Launch youtube-dl-gui:', self.launch_check)
        form.addRow('Show README:', self.readme_check)
        self.setLayout(form)



def main():
    app = QApplication(sys.argv)
    app.setOrganizationName('MyApps')
    app.setApplicationName('youtube-dl-gui')
    wizard = QWizard()
    wizard.setWindowTitle('youtube-dl-gui installation')
    wizard.addPage(InstallationDirectoryPage())
    wizard.addPage(YotubeDLDownloadPage())
    wizard.addPage(FinalPage())
    wizard.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
