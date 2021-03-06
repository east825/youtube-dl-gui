# vim: fileencoding=utf-8

from __future__ import unicode_literals
from __future__ import print_function
import subprocess
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
LOG = logging.getLogger('youtube.installer')

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from youtube.settings import ORGANIZATION_NAME, APPLICATION_NAME, reset_to_defaults

# noinspection PyUnresolvedReferences
import resources.icons

YOUTUBE_PKG_PATH = os.path.join(os.path.dirname(__file__), 'youtube')
ON_WINDOWS = platform.system() == 'Windows'

if ON_WINDOWS:
    YOUTUBE_DL_DOWNLOAD_URL = 'https://yt-dl.org/downloads/2013.09.16/youtube-dl.exe'
else:
    YOUTUBE_DL_DOWNLOAD_URL = 'https://yt-dl.org/downloads/2013.09.16/youtube-dl'


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


def show_error_box(parent, message, title='Error'):
    return QMessageBox.warning(parent, title, message)


def debug_delay(seconds):
    if __debug__:
        time.sleep(seconds)

class InstallStartPage(QWizardPage):
    def __init__(self, parent=None):
        super(InstallStartPage, self).__init__(parent)
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
        super(InstallStartPage, self).initializePage()
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
        return super(InstallStartPage, self).isComplete()


class InstallProgressPage(QWizardPage):
    def __init__(self, parent=None):
        super(InstallProgressPage, self).__init__(parent)
        vbox = QVBoxLayout()
        self.info = QLabel()
        vbox.addWidget(self.info)
        self.progress = QProgressBar()
        vbox.addWidget(self.progress)
        vbox.addStretch()
        self.setLayout(vbox)

    def initializePage(self):
        QTimer.singleShot(0, self.install)

    def update_progress_info(self, msg, value):
        self.info.setText(msg)
        self.progress.setValue(value)

    def install(self):
        dest = unicode(self.field('InstallationDirectory').toString())
        try:
            self.update_progress_info('Copying application files...', 0)
            if not os.path.exists(dest):
                os.makedirs(dest)
            shutil.copytree(YOUTUBE_PKG_PATH, os.path.join(dest, 'youtube'),
                            ignore=shutil.ignore_patterns('*.pyc', '*.pyo'))
            debug_delay(1)

            self.update_progress_info('Creating *.pth file...', 20)
            pth_file = os.path.join(site.getsitepackages()[-1], 'youtube-dl-gui.pth')
            with open(pth_file, 'w') as fd:
                fd.write(dest.encode('utf-8'))
            debug_delay(1)

            self.update_progress_info('Saving default settings...', 35)
            settings = QSettings()
            settings.setValue('InstallationDirectory', dest)
            reset_to_defaults()
            debug_delay(1)
        except OSError as e:
            show_error_box(self, "Can't copy application files ({})".format(e.strerror))
            QApplication.instance().exit(2)

        if self.field('DownloadYouTubeDL').toBool():
            # TODO: think about something more meaningful
            self.update_progress_info('Downloading youtube-dl...', 50)
            exec_dir = os.path.join(dest, 'bin')
            try:
                os.mkdir(exec_dir)
            except OSError as e:
                show_error_box(self,"Can't create directory '{}' ({})".format(exec_dir,e.strerror))
                return
            try:
                r = urllib2.urlopen(YOUTUBE_DL_DOWNLOAD_URL)
                total = int(r.headers['Content-Length'])
                read = 0
                with open(os.path.join(exec_dir, 'youtube-dl'), 'wb') as fd:
                    while read < total:
                        QApplication.processEvents(QEventLoop.AllEvents, 100)
                        block = r.read(4096)
                        read += len(block)
                        fd.write(block)
                        step = int((float(read) / total) * 50) + 50
                        self.progress.setValue(step)
                        debug_delay(0.01)
            except URLError as e:
                msg = 'Can\'t download youtube-dl executable ({})'.format(e.reason)
                show_error_box(self, msg)
        else:
            self.update_progress_info('Installation completed', 100)
        self.wizard().next()


class InstallFinalPage(QWizardPage):
    def __init__(self, parent=None):
        super(InstallFinalPage, self).__init__(parent)
        self.setTitle('Installation completed')
        self.setSubTitle('Thank you for installing {}'.format(APPLICATION_NAME))
        self.launch_check = QCheckBox()
        self.launch_check.setChecked(True)
        self.registerField('LaunchApplication', self.launch_check)
        # self.readme_check = QCheckBox()
        form = QFormLayout()
        form.addRow('Launch {}:'.format(APPLICATION_NAME), self.launch_check)
        # form.addRow('Show README:', self.readme_check)
        self.setLayout(form)


class UninstallProgressPage(QWizardPage):
    def __init__(self, parent=None):
        super(UninstallProgressPage, self).__init__(parent)
        self.setTitle('Uninstall {}'.format(APPLICATION_NAME))
        self.info = QLabel()
        self.progress = QProgressBar()
        vbox = QVBoxLayout()
        vbox.addWidget(self.info)
        vbox.addWidget(self.progress)
        vbox.addStretch()
        self.setLayout(vbox)
        self.complete = False

    def initializePage(self):
        QTimer.singleShot(0, self.uninstall)

    def uninstall(self):
        settings = QSettings()
        app_dir = unicode(settings.value('InstallationDirectory').toString())
        settings_file = unicode(settings.fileName())
        pth_file = os.path.join(site.getsitepackages()[-1], 'youtube-dl-gui.pth')
        targets = [
            ('program directory', app_dir),
            ('settings', settings_file),
            ('*.pth file', pth_file),
        ]
        for i, resource in enumerate(targets):
            name, path = resource
            if not os.path.exists(path):
                continue
            self.info.setText('Deleting {}...'.format(name))
            try:
                QApplication.instance().processEvents(QEventLoop.AllEvents, 100)
                remove(path)
                debug_delay(1)
                LOG.debug("'%s' removed successfully", path)
            except OSError as e:
                show_error_box("Can't delete '{}' ({})".format(path, e.strerror))
            self.progress.setValue((i + 1.0) / len(targets) * 100)
        self.complete = True
        # made 'Finish' button visible
        self.completeChanged.emit()
        self.info.setText('Program uninstalled successfully')

    def isComplete(self):
        if not self.complete:
            return False
        return super(UninstallProgressPage, self).isComplete()


class InstallWizard(QWizard):
    def __init__(self):
        super(InstallWizard, self).__init__()
        if not os.path.exists(YOUTUBE_PKG_PATH):
            show_error_box(self,'Installer should be started from directory containing "youtube" package')
            # alternative way to close application
            # QTimer.singleShot(0, lambda: self.done(2))
            QTimer.singleShot(0, lambda: QApplication.instance().exit(1))
        self.setWindowTitle('{} installation'.format(APPLICATION_NAME))
        self.addPage(InstallStartPage())
        self.addPage(InstallProgressPage())
        self.addPage(InstallFinalPage())

    def accept(self):
        app_dir = unicode(self.field('InstallationDirectory').toString())
        if self.field('LaunchApplication').toBool():
            subprocess.Popen(['python', os.path.join(app_dir, 'youtube', 'main.py')])
        return super(InstallWizard, self).accept()


def main():
    app = QApplication(sys.argv)
    app.setOrganizationName(ORGANIZATION_NAME)
    app.setApplicationName(APPLICATION_NAME)
    QSettings().setDefaultFormat(QSettings.IniFormat)
    install_dir = unicode(QSettings().value('InstallationDirectory').toString())
    if os.path.exists(install_dir):
        wizard = QWizard()
        wizard.setWindowTitle('{} removal'.format(APPLICATION_NAME))
        wizard.addPage(UninstallProgressPage())
    else:
        wizard = InstallWizard()
    wizard.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
