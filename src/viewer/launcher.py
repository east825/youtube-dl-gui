#!/usr/bin/env python
# vim: fileencoding=utf-8

"""
Program main entry point.
"""

from __future__ import unicode_literals
from __future__ import print_function

import sys
import logging
import os
import argparse
import resources.icons

from util import *

from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.phonon import Phonon

SUPPORTED_FORMATS = ['*.avi', '*.mpeg']

__version__ = (0, 1)

logging.basicConfig(level=logging.DEBUG, format='%(message)s')
# LOG = logging.getLogger('viewer')
# LOG.setLevel(logging.DEBUG)
# LOG.propagate = False
# LOG.addHandler(logging.StreamHandler())

# noinspection PyArgumentList
class VideoPlayer(QWidget):
    def __init__(self, QWidget_parent=None, Qt_WindowFlags_flags=0):
        # super(QWidget, self).__init__(QWidget_parent, Qt_WindowFlags_flags)
        QWidget.__init__(self, QWidget_parent, )
        # Phonon setup
        # self.media = Phonon.MediaObject(self)
        # self.media.stateChanged.connect(lambda s: logging.debug('State ', s))
        # self.video = Phonon.VideoWidget(self)
        # self.video.setMinimumSize(400, 400)
        # self.audio = Phonon.AudioOutput(Phonon.VideoCategory, self)
        # self.file_path = None
        # Phonon.createPath(self.media, self.video)
        # Phonon.createPath(self.media, self.audio)
        self.player = Phonon.VideoPlayer(self)

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
        self.file_path = os.path.abspath(filename)
        self.player.play(Phonon.MediaSource(self.file_path))

    @property
    def supported_formats(self):
        return SUPPORTED_FORMATS

    @property
    def file_dir(self):
        if self.file_path is not None:
            return os.path.basename(self.file_path)
        return os.curdir


class MainWindow(QMainWindow):
    def __init__(self, path):
        super(MainWindow, self).__init__()
        self.setWindowTitle('Player')
        self.setMinimumSize(800, 600)
        self.player = VideoPlayer(self)
        self.setCentralWidget(self.player)

        new_file_action = QAction(QIcon(':document-new'), '&New', self)
        new_file_action.triggered.connect(self.open_new_file)
        new_file_action.setShortcut(QKeySequence.New)

        main_toolbar = self.addToolBar('MainToolbar')
        main_toolbar.addAction(new_file_action)

        file_menu = self.menuBar().addMenu('&File')
        file_menu.addAction(new_file_action)

        if path is not None:
            self.player.play_file(path)



    def _button_clicked(self):
        path = QFileDialog.getOpenFileName(self, self.button.text())
        logging.debug('Path selected:  %s', path)
        if path:
            self.media.setCurrentSource(Phonon.MediaSource(path))
            self.media.play()

    def _media_state_changed(self, new_state, old_state):
        logging.debug('New state: "%s"', new_state)
        logging.debug('Old state: %s', old_state)

    def open_new_file(self):
        pattern = 'Video files ({})'.format(' '.join(self.player.supported_formats))
        dir = self.player.file_dir
        path = u(QFileDialog.getOpenFileName(self, 'Select video file', dir, pattern))
        if path:
            logging.debug('File chosen: "%s"', path)
            self.player.play_file(path)


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