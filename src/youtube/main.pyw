#!/usr/bin/env python
# vim: fileencoding=utf-8

"""
Program main entry point.
"""

from __future__ import unicode_literals
from __future__ import print_function
import os

import sys
import logging
import argparse
from PyQt4.QtCore import QSettings

from PyQt4.QtGui import *
from PyQt4.phonon import Phonon

from player import VideoPlayer, PHONON_STATES
from util import show_about_dialog, create_action
from youtube.dialogs import DownloadDialog

# noinspection PyUnresolvedReferences
import resources.icons
from youtube.settings import SettingsDialog, get_download_dir


__version__ = (0, 1)

logging.basicConfig(level=logging.DEBUG,
                    format='%(levelname)s:%(name)s: %(message)s')
LOG = logging.getLogger('youtube.launcher')
LOG.setLevel(logging.DEBUG)
LOG.propagate = False
LOG.addHandler(logging.StreamHandler())

# noinspection PyArgumentList

class MainWindow(QMainWindow):
    def __init__(self, path):
        super(MainWindow, self).__init__()
        self.setWindowIcon(QIcon(':youtube'))
        self.setWindowTitle('youtube-dl-gui')
        self.setMinimumSize(800, 600)
        self.player = VideoPlayer(self)
        # self.player.state_changed.connect(self.update_status)
        self.player.state_changed.connect(self.update_title)
        self.player.time_changed.connect(self.update_status_bar)

        self.setCentralWidget(self.player)

        new_file_action = create_action(
            text='&New',
            icon=QIcon(':document-new'),
            tooltip='Open existing file',
            shortcut=QKeySequence.New,
            triggered=self.show_new_file_dialog,
            parent=self
        )

        download_video_action = create_action(
            text='&Download',
            icon=QIcon(':download'),
            tooltip='Download video from YouTube',
            shortcut='Ctrl+D',
            triggered=self.show_download_dialog,
            parent=self
        )

        show_setting_action = create_action(
            text='&Settings',
            icon=QIcon(':settings'),
            tooltip='Show setting dialog',
            shortcut='Ctrl+Alt+S',
            triggered=self.show_settings_dialog,
            parent=self
        )

        about_action = create_action(
            text='&About',
            icon=QIcon(':about'),
            triggered=self.show_about,
            parent=self
        )

        main_toolbar = self.addToolBar('MainToolbar')
        main_toolbar.addAction(download_video_action)
        main_toolbar.addAction(new_file_action)
        main_toolbar.addSeparator()
        main_toolbar.addAction(show_setting_action)

        file_menu = self.menuBar().addMenu('&File')
        file_menu.addAction(new_file_action)
        file_menu.addAction(download_video_action)

        settings_menu = self.menuBar().addMenu('&Settings')
        settings_menu.addAction(show_setting_action)

        self.menuBar().addMenu('About').addAction(about_action)

        if path is not None:
            self.player.play(path)

    def show_new_file_dialog(self):
        globs = ['*' + e for e in self.player.supported_extensions()]
        if self.player.path:
            directory = os.path.dirname(self.player.path)
        else:
            directory = get_download_dir()
        path = unicode(QFileDialog.getOpenFileName(
            self, 'Select video file',
            directory,
            'Video files ({})'.format(' '.join(globs))
        ))
        if path:
            logging.debug('File chosen: "%s"', path)
            self.player.play(path)

    def update_status_bar(self, time, total):
        # TODO: how convert timedelta to time instance for further formatting?
        self.statusBar().showMessage('Time: {:s}/{:s}'.format(time, total))

    def update_title(self, new_state):
        logging.debug('Player new state: %s', PHONON_STATES[new_state])
        if new_state == Phonon.PlayingState:
            self.setWindowTitle('"{}" - Playing'.format(self.player.path))
        elif new_state == Phonon.PausedState:
            self.setWindowTitle('"{}" - Paused'.format(self.player.path))

    def show_download_dialog(self):
        d = DownloadDialog(self)
        d.downloaded.connect(self.player.play)
        d.exec_()
        LOG.debug('Exiting download_video()')

    def show_settings_dialog(self):
        SettingsDialog().exec_()

    def show_about(self):
        show_about_dialog(self)


def main():
    parser = argparse.ArgumentParser(description='Viewer launcher')
    parser.add_argument('path', nargs='?', help='File to play')
    args = parser.parse_args()
    # don't use window registry by any means
    QSettings().setDefaultFormat(QSettings.IniFormat)
    app = QApplication(sys.argv)
    app.setOrganizationName('MyApps')
    app.setApplicationName('youtube-dl-gui')
    widget = MainWindow(args.path)
    widget.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()