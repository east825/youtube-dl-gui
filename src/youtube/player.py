# vim: fileencoding=utf-8

from __future__ import unicode_literals
from __future__ import print_function

from datetime import timedelta
import logging
import mimetypes
import os
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.phonon import Phonon

LOG = logging.getLogger('youtube.player')

PHONON_STATES = {
    Phonon.LoadingState: 'LodingsState',
    Phonon.StoppedState: 'StoppedState',
    Phonon.PlayingState: 'PlayeringState',
    Phonon.BufferingState: 'BufferingState',
    Phonon.PausedState: 'PausedState',
    Phonon.ErrorState: 'ErrorState'
}

class VideoPlayer(QWidget):
    state_changed = pyqtSignal('Phonon::State', name='state_changed')
    time_changed = pyqtSignal(timedelta, timedelta, name='time_changed')

    def __init__(self, QWidget_parent=None):
        # super(QWidget, self).__init__(QWidget_parent, Qt_WindowFlags_flags)
        QWidget.__init__(self, QWidget_parent, )
        self.player = Phonon.VideoPlayer()
        # self.player.mediaObject().stateChanged.connect(self.update_status)
        self.player.mediaObject().stateChanged.connect(self.state_changed)
        self.player.mediaObject().tick.connect(self.update_time)
        # one tick per second
        self.player.mediaObject().setTickInterval(1000)


        vbox = QVBoxLayout()
        vbox.addWidget(self.player, 1)
        vbox.addWidget(Phonon.SeekSlider(self.player.mediaObject(), self))

        hbox = QHBoxLayout()
        hbox.addWidget(QPushButton(icon=QIcon(':MD-fast-backward'), clicked=self.on_backward))
        hbox.addWidget(QPushButton(icon=QIcon(':MD-resume'), clicked=self.on_resume))
        hbox.addWidget(QPushButton(icon=QIcon(':MD-stop'), clicked=self.on_stop))
        hbox.addWidget(QPushButton(icon=QIcon(':MD-fast-forward'), clicked=self.on_forward))
        hbox.addStretch()
        hbox.addWidget(Phonon.VolumeSlider(self.player.audioOutput(), self))

        vbox.addLayout(hbox)
        self.setLayout(vbox)

        self.path = None

    def on_resume(self):
        LOG.debug('Play button clicked')
        if self.player.isPlaying():
            self.player.pause()
        else:
            self.player.play()

    def on_stop(self):
        LOG.debug('Stop button clicked')
        self.player.stop()

    def on_backward(self):
        cur = self.player.currentTime()
        self.player.seek(cur - min(cur, 5000))

    def on_forward(self):
        cur = self.player.currentTime()
        total = self.player.totalTime()
        self.player.seek(cur + min(total - cur, 5000))

    def play(self, path):
        self.path = os.path.abspath(path)
        self.player.play(Phonon.MediaSource(self.path))

    def supported_formats(self):
        mtypes = Phonon.BackendCapabilities.availableMimeTypes()
        mtypes = map(unicode, mtypes)
        LOG.debug('Mime types available: %s', mtypes)
        extensions = []
        for mtype in mtypes:
            if mtype.startswith('video'):
                extensions.extend(mimetypes.guess_all_extensions(mtype))
        LOG.debug('Video files extensions: %s', extensions)
        return extensions

    def file_dir(self):
        if self.path is not None:
            return os.path.basename(self.path)
        return os.curdir

    def update_time(self, msec):
        current = timedelta(seconds=(msec / 1000))
        total_time = self.player.mediaObject().totalTime()
        total = timedelta(seconds=(total_time / 1000))
        LOG.debug('Time is %s/%s (%d ms)', current, total, msec)
        self.time_changed.emit(current, total)

