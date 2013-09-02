#!/usr/bin/env python
# vim: fileencoding=utf-8

"""
Program main entry point.
"""

from __future__ import unicode_literals
from __future__ import print_function

import sys
import logging
import argparse

from PyQt4.QtGui import *
from PyQt4.phonon import Phonon

from player import VideoPlayer, PHONON_STATES
from dialogs import StringListDialog
from util import show_stub_message_box, show_about_dialog
from youtube.dialogs import DownloadDialog

# noinspection PyUnresolvedReferences
import resources.icons


__version__ = (0, 1)

logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(name)s: %(message)s')
LOG = logging.getLogger('youtube.launcher')
LOG.setLevel(logging.DEBUG)
LOG.propagate = False
LOG.addHandler(logging.StreamHandler())

# noinspection PyArgumentList

class MainWindow(QMainWindow):
    def __init__(self, path):
        super(MainWindow, self).__init__()
        self.setWindowIcon(QIcon(':youtube'))
        self.setWindowTitle('YouTube Player')
        self.setMinimumSize(800, 600)
        self.player = VideoPlayer(self)
        # self.player.state_changed.connect(self.update_status)
        self.player.state_changed.connect(self.update_title)
        self.player.time_changed.connect(self.update_status_bar)


        self.setCentralWidget(self.player)

        new_file_action = QAction(QIcon(':document-new'), '&New', self)
        new_file_action.setToolTip('Open existing file')
        new_file_action.setShortcut(QKeySequence.New)
        new_file_action.triggered.connect(self.open_new_file)

        download_video_action = QAction(QIcon(':download'), '&Download', self)
        download_video_action.setToolTip('Download video from YouTube')
        download_video_action.triggered.connect(self.download_video)

        show_setting_action = QAction(QIcon(':settings'), '&Settings', self)
        show_setting_action.setToolTip('Show setting dialog')
        show_setting_action.triggered.connect(self.show_settings)

        show_formats_action = QAction('&Show supported formats', self)
        show_formats_action.setToolTip('Show formats supported by Phonon backend')
        show_formats_action.triggered.connect(self.show_formats)

        main_toolbar = self.addToolBar('MainToolbar')
        main_toolbar.addAction(download_video_action)
        main_toolbar.addAction(new_file_action)
        main_toolbar.addSeparator()
        main_toolbar.addAction(show_setting_action)

        file_menu = self.menuBar().addMenu('&File')
        file_menu.addAction(new_file_action)
        file_menu.addAction(download_video_action)

        settings_menu = self.menuBar().addMenu('&Settings')
        settings_menu.addAction(show_formats_action)
        settings_menu.addAction(show_setting_action)

        about_action = self.menuBar().addAction('&About')
        about_action.setIcon(QIcon(':about'))
        about_action.triggered.connect(self.show_about)

        if path is not None:
            self.player.play(path)

    def open_new_file(self):
        globs = ['*' + e for e in self.player.supported_formats()]
        pardir = self.player.file_dir()
        path = unicode(QFileDialog.getOpenFileName(self, 'Select video file', pardir,
                                                   'Video files ({})'.format(' '.join(globs))))
        if path:
            logging.debug('File chosen: "%s"', path)
            self.player.play(path)

    def show_formats(self):
        # QMessageBox.
        formats = Phonon.BackendCapabilities.availableMimeTypes()
        dialog = StringListDialog(self, formats)
        dialog.setWindowTitle('Supported formats')
        dialog.exec_()

    def update_status_bar(self, time, total):
        # TODO: how convert timedelta to time instance for further formatting?
        self.statusBar().showMessage('Time: {:s}/{:s}'.format(time, total))

    def update_title(self, new_state):
        logging.debug('Player new state: %s', PHONON_STATES[new_state])
        if new_state == Phonon.PlayingState:
            self.setWindowTitle('"{}" - Playing'.format(self.player.path))
        elif new_state == Phonon.PausedState:
            self.setWindowTitle('"{}" - Paused'.format(self.player.path))


    def download_video(self):
        d = DownloadDialog(self)
        d.downloaded.connect(lambda x: self.player.play(x))
        d.exec_()
        LOG.debug('Exiting download_video()')

    def show_settings(self):
        show_stub_message_box(self)

    def show_about(self):
        show_about_dialog(self)



def main():
    parser = argparse.ArgumentParser(description='Viewer launcher')
    parser.add_argument('path', nargs='?', help='File to play')
    args = parser.parse_args()
    app = QApplication(sys.argv)
    widget = MainWindow(args.path)
    widget.setWindowTitle('Downloader')
    widget.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()