# vim: fileencoding=utf-8

from __future__ import unicode_literals
from __future__ import print_function
import sys
import site

import os
import platform
import shutil

import urllib2
from urllib2 import URLError
from urlparse import urlsplit

import time

import logging
logging.basicConfig(level=logging.DEBUG)

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from youtube.settings import ORGANIZATION_NAME, APPLICATION_NAME
from youtube.util import create_button

import resources.icons


YOUTUBE_PKG_PATH = os.path.join(os.path.dirname(__file__), 'youtube')
ON_WINDOWS = platform.system() == 'Windows'

if ON_WINDOWS:
    YOUTUBE_DL_DOWNLOAD_URL = 'https://yt-dl.org/downloads/2013.11.09/youtube-dl.exe'
else:
    YOUTUBE_DL_DOWNLOAD_URL = 'https://yt-dl.org/downloads/2013.11.09/youtube-dl'


def get_default_installation_dir():
    app_name = APPLICATION_NAME
    org_name = ORGANIZATION_NAME
    if ON_WINDOWS:
        base_dir = 'C:\\Program Files'
    else:
        base_dir = os.path.expanduser('/usr/local/lib')
    path = os.path.join(base_dir, org_name, app_name)
    return path


def is_real_dir(path):
    return os.path.isdir(path) and not os.path.islink(path)


def is_empty_dir(path):
    return is_real_dir(path) and not os.listdir(path)


def remove(path):
    if is_real_dir(path):
        shutil.rmtree(path)
    else:
        os.remove(path)


class StartPage(QWizardPage):
    def __init__(self, parent=None):
        super(StartPage, self).__init__(parent)
        self.setTitle('Choose installation directory')

        label = QLabel('&Installation directory:')
        self.path_edit = QLineEdit(get_default_installation_dir())
        self.registerField('InstallationDirectory', self.path_edit)
        self.path_edit.textChanged.connect(self.completeChanged)
        label.setBuddy(self.path_edit)
        self.dir_picker = QToolButton(self)
        self.dir_picker.setText('…')
        self.dir_picker.pressed.connect(self.show_dir_picker)

        grid = QGridLayout()
        grid.addWidget(label, 0, 0)
        grid.addWidget(self.path_edit, 0, 1)
        grid.addWidget(self.dir_picker, 0, 2)

        label = QLabel('Download youtube-dl')
        download_checkbox = QCheckBox()
        download_checkbox.setChecked(True)
        self.registerField('DownloadYouTubeDL', download_checkbox)
        label.setBuddy(download_checkbox)

        left_aligned = QHBoxLayout()
        left_aligned.addWidget(download_checkbox)
        left_aligned.addWidget(label)
        left_aligned.addStretch(1)

        main_layout = QVBoxLayout()
        main_layout.addLayout(grid)
        main_layout.addStretch()
        main_layout.addLayout(left_aligned)
        self.setLayout(main_layout)

    def initializePage(self):
        super(StartPage, self).initializePage()
        self.path_edit.setText(get_default_installation_dir())


    def show_dir_picker(self):
        path = QFileDialog.getExistingDirectory(self,
                                                'Choose installation directory',
                                                self.path_edit.text())
        if path:
            self.path_edit.setText(path)

    def isComplete(self):
        path = unicode(self.path_edit.text())
        if os.path.exists(path) and not is_empty_dir(path):
            return False
        return super(StartPage, self).isComplete()


class YotubeDLDownloadPage(QWizardPage):
    def __init__(self, parent=None):
        super(YotubeDLDownloadPage, self).__init__(parent)
        self.setTitle('Download youtube-dl')
        self.setSubTitle(
            'You can optionally download newest version of youtube-dl if it isn\'t installed yes')

        main_grid = QGridLayout()
        main_grid.addWidget(QLabel('Download youtube-dl:'), 0, 0)
        download_checkbox = QCheckBox()
        left_aligned = QHBoxLayout()
        left_aligned.addWidget(download_checkbox)
        left_aligned.addStretch(1)
        main_grid.addLayout(left_aligned, 0, 1)
        main_grid.addItem(QSpacerItem(0, 20), 1, 0)

        extension = QWidget()
        ext_grid = QGridLayout()
        self.progress = QProgressBar(self)
        download_button = create_button(
            text='Download',
            clicked=self.download,
        )
        ext_grid.addWidget(download_button, 0, 0)
        ext_grid.addWidget(self.progress, 0, 1)
        extension.setLayout(ext_grid)

        main_grid.addWidget(extension, 2, 0, 1, 2)
        self.setLayout(main_grid)

        download_checkbox.toggled.connect(extension.setVisible)
        extension.hide()

    def download(self):
        install_dir = unicode(self.field('InstallationDirectory').toString())
        for i in range(100):
            QApplication.processEvents(QEventLoop.AllEvents, 100)
            time.sleep(0.1)
            self.progress.setValue(i + 1)
        self.wizard().next()


class ProgressPage(QWizardPage):
    def __init__(self, parent=None):
        super(ProgressPage, self).__init__(parent)
        vbox = QVBoxLayout()
        self.info = QLabel()
        vbox.addWidget(self.info)
        self.progress = QProgressBar()
        vbox.addWidget(self.progress)
        vbox.addStretch()
        self.setLayout(vbox)

    def show_error_box(self, msg):
        return QMessageBox.warning(self, 'Error', msg)

    def initializePage(self):
        QTimer.singleShot(0, self.install)

    def install(self):
        dest = unicode(self.field('InstallationDirectory').toString())
        self.info.setText('Copying application files...')
        try:
            if not os.path.exists(dest):
                os.makedirs(dest)
            shutil.copytree(YOUTUBE_PKG_PATH, os.path.join(dest, 'youtube'),
                            ignore=shutil.ignore_patterns('*.py[co]'))
            pth_file = os.path.join(site.getsitepackages()[-1], 'youtube-dl-gui.pth')
            with open(pth_file, 'w') as fd:
                fd.write(dest.encode('utf-8'))
        except OSError as e:
            self.show_error_box(
                "Can't copy application files ({})".format(e.strerror))
            QApplication.instance().exit(2)

        # TODO: think about something more meaningful
        self.progress.setValue(50)
        if self.field('DownloadYouTubeDL').toBool():
            self.info.setText('Downloading youtube-dl...')
            exec_dir = os.path.join(dest, 'bin')
            try:
                os.mkdir(exec_dir)
            except OSError as e:
                self.show_error_box(
                    "Can't create directory '{}' ({})".format(exec_dir,
                                                              e.strerror))
                return
            try:
                r = urllib2.urlopen(YOUTUBE_DL_DOWNLOAD_URL)
                file_name = os.path.basename(
                    urlsplit(YOUTUBE_DL_DOWNLOAD_URL).path)
                total = int(r.headers['Content-Length'])
                read = 0
                with open(os.path.join(exec_dir, file_name), 'wb') as fd:
                    while read < total:
                        QApplication.processEvents(QEventLoop.AllEvents, 100)
                        block = r.read(4096)
                        read += len(block)
                        fd.write(block)
                        step = int((float(read) / total) * 50) + 50
                        self.progress.setValue(step)
            except URLError as e:
                msg = 'Can\'t download youtube-dl executable ({})'.format(
                    e.reason)
                self.show_error_box(msg)
        self.wizard().next()


class FinalPage(QWizardPage):
    def __init__(self, parent=None):
        super(FinalPage, self).__init__(parent)
        self.setTitle('Installation completed')
        self.setSubTitle('Thank you for installing {}'.format(APPLICATION_NAME))
        self.launch_check = QCheckBox()
        self.registerField('LaunchApplication', self.launch_check)
        # self.readme_check = QCheckBox()
        form = QFormLayout()
        form.addRow('Launch {}:'.format(APPLICATION_NAME), self.launch_check)
        # form.addRow('Show README:', self.readme_check)
        self.setLayout(form)


def main():
    app = QApplication(sys.argv)
    app.setOrganizationName(ORGANIZATION_NAME)
    app.setApplicationName(APPLICATION_NAME)
    wizard = QWizard()
    wizard.setWindowTitle('{} installation'.format(APPLICATION_NAME))
    # wizard.setPixmap(QWizard.LogoPixmap, QPixmap(':youtube'))
    wizard.addPage(StartPage())
    wizard.addPage(ProgressPage())
    # wizard.addPage(YotubeDLDownloadPage())
    wizard.addPage(FinalPage())
    wizard.show()
    if not os.path.exists(YOUTUBE_PKG_PATH):
        QMessageBox.warning(
            wizard,
            'Error',
            'Installer should be started from directory containing "youtube" package'
        )
        app.exit(1)
    else:
        sys.exit(app.exec_())


if __name__ == '__main__':
    main()
