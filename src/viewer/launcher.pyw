#!/usr/bin/env python
# vim: fileencoding=utf-8

"""
Program main entry point.
"""

from __future__ import unicode_literals
from __future__ import print_function
import mimetypes

import sys
import logging
import os
import argparse
import resources.icons
from datetime import time
from datetime import timedelta

from dialogs import StringListDialog
from util import show_stub_message_box, show_about_dialog

from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.phonon import Phonon

__version__ = (0, 1)

logging.basicConfig(level=logging.DEBUG, format='%(message)s')
# LOG = logging.getLogger('viewer')
# LOG.setLevel(logging.DEBUG)
# LOG.propagate = False
# LOG.addHandler(logging.StreamHandler())

# noinspection PyArgumentList
class VideoPlayer(QWidget):
    state_changed = pyqtSignal('Phonon::State', name='state_changed')
    time_changed = pyqtSignal(timedelta, timedelta, name='time_changed')

    def __init__(self, QWidget_parent=None):
        # super(QWidget, self).__init__(QWidget_parent, Qt_WindowFlags_flags)
        QWidget.__init__(self, QWidget_parent, )
        self.player = Phonon.VideoPlayer(self)
        # self.player.mediaObject().stateChanged.connect(self.update_status)
        self.player.mediaObject().stateChanged.connect(self.state_changed)
        self.player.mediaObject().tick.connect(self.update_time)
        # one tick per second
        self.player.mediaObject().setTickInterval(1000)


        vbox = QVBoxLayout()
        vbox.addWidget(self.player, 1)
        vbox.addWidget(Phonon.SeekSlider(self.player.mediaObject(), self))

        hbox = QHBoxLayout()
        hbox.addWidget(QPushButton(icon=QIcon(':MD-resume'), clicked=self.on_resume))
        hbox.addWidget(QPushButton(icon=QIcon(':MD-stop'), clicked=self.on_stop))
        hbox.addStretch()
        hbox.addWidget(Phonon.VolumeSlider(self.player.audioOutput(), self))

        vbox.addLayout(hbox)
        self.setLayout(vbox)

        self.file_path = None

    def on_resume(self):
        logging.debug('Play button clicked')
        if self.player.isPlaying():
            self.player.pause()
        else:
            self.player.play()

    def on_stop(self):
        logging.debug('Stop button clicked')
        self.player.stop()

    def play_file(self, filename):
        self.player.play(Phonon.MediaSource(self.file_path))
        self.file_path = os.path.abspath(filename)

    def supported_formats(self):
        mtypes = Phonon.BackendCapabilities.availableMimeTypes()
        mtypes = map(unicode, mtypes)
        logging.debug('Mime types available: %s', mtypes)
        extensions = []
        for mtype in mtypes:
            if mtype.startswith('video'):
                extensions.extend(mimetypes.guess_all_extensions(mtype))
        logging.debug('Video files extensions: %s', extensions)
        return extensions

    def file_dir(self):
        if self.file_path is not None:
            return os.path.basename(self.file_path)
        return os.curdir

    def update_time(self, msec):
        current = timedelta(seconds=(msec / 1000))
        total_time = self.player.mediaObject().totalTime()
        total = timedelta(seconds=(total_time / 1000))
        logging.debug('Time is %s/%s (%d ms)', current, total, msec)
        self.time_changed.emit(current, total)


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
        new_file_action.setToolTip('Open existing video file')
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
            self.player.play_file(path)

    def open_new_file(self):
        globs = ['*' + e for e in self.player.supported_formats()]
        pardir = self.player.file_dir()
        path = unicode(QFileDialog.getOpenFileName(self, 'Select video file', pardir,
                                                   'Video files ({})'.format(' '.join(globs))))
        if path:
            logging.debug('File chosen: "%s"', path)
            self.player.play_file(path)

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
        logging.debug('New state: %s', new_state)
        if new_state == Phonon.PlayingState:
            self.setWindowTitle('"{}" - Playing'.format(self.player.file_path))
        elif new_state == Phonon.PausedState:
            self.setWindowTitle('"{}" - Paused'.format(self.player.file_path))


    def download_video(self):
        show_stub_message_box(self)

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