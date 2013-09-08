# vim: fileencoding=utf-8

from __future__ import unicode_literals
from __future__ import print_function

from datetime import timedelta
import logging
import mimetypes
import os
from pprint import pformat
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.phonon import Phonon
from youtube.util import create_button, create_action

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
    state_changed = pyqtSignal('Phonon::State')
    time_changed = pyqtSignal(timedelta, timedelta)

    def __init__(self, QWidget_parent=None):
        QWidget.__init__(self, QWidget_parent)
        self.player = Phonon.VideoPlayer()
        self.player.mediaObject().stateChanged.connect(self.state_changed)
        self.player.mediaObject().tick.connect(self.update_time)
        # one tick per second
        self.player.mediaObject().setTickInterval(1000)

        vbox = QVBoxLayout()
        vbox.addWidget(self.player, 1)
        vbox.addWidget(Phonon.SeekSlider(self.player.mediaObject(), self))

        hbox = QHBoxLayout()
        hbox.addWidget(create_button(icon=QIcon(':MD-fast-backward'),
                                     clicked=self.rewind_forward,
                                     shortcut='Ctrl+Left'))
        hbox.addWidget(create_button(icon=QIcon(':MD-resume'),
                                     clicked=self.resume,
                                     shortcut='Ctrl+P'))
        hbox.addWidget(create_button(icon=QIcon(':MD-stop'),
                                     clicked=self.stop,
                                     shortcut='Ctrl+Shift+P'))
        hbox.addWidget(create_button(icon=QIcon(':MD-fast-forward'),
                                     clicked=self.rewind_forward,
                                     shortcut='Ctrl+Right'))
        hbox.addWidget(create_button(icon=QIcon(':MD-volume-0'),
                                     checkable=True,
                                     toggled=self.mute,
                                     shortcut='Ctrl+M'))

        hbox.addStretch()

        volume_icon = QLabel(self)
        audio_output = self.player.audioOutput()
        self.volume_slider = Phonon.VolumeSlider(audio_output, self)
        self.volume_slider.setMuteVisible(False)

        def change_volume_icon(ignored):
            level = audio_output.volume()
            if audio_output.isMuted() or level == 0:
                volume_icon.setPixmap(QPixmap(':MD-volume-0-alt'))
            elif level <= 0.33:
                volume_icon.setPixmap(QPixmap(':MD-volume-1'))
            elif level <= 0.66:
                volume_icon.setPixmap(QPixmap(':MD-volume-2'))
            else:
                volume_icon.setPixmap(QPixmap(':MD-volume-3'))

        change_volume_icon(audio_output.volume())
        audio_output.volumeChanged.connect(change_volume_icon)
        audio_output.mutedChanged.connect(change_volume_icon)

        hbox.addWidget(volume_icon)
        hbox.addWidget(self.volume_slider)

        vbox.addLayout(hbox)
        self.setLayout(vbox)

        self.path = None

    def resume(self):
        LOG.debug('Play button clicked')
        if self.player.isPlaying():
            self.player.pause()
        else:
            self.player.play()

    def stop(self):
        LOG.debug('Stop button clicked')
        self.player.stop()

    def rewind_backward(self):
        cur = self.player.currentTime()
        self.player.seek(cur - min(cur, 5000))

    def rewind_forward(self):
        cur = self.player.currentTime()
        total = self.player.totalTime()
        self.player.seek(cur + min(total - cur, 5000))

    def mute(self):
        audio = self.player.audioOutput()
        audio.setMuted(not audio.isMuted())

    def play(self, path):
        if path is not None:
            LOG.debug('Path to video file: %s', path)
            self.player.play(Phonon.MediaSource(path))
        else:
            LOG.debug('No existing file specified for playback')
            self.player.play()
        self.path = os.path.abspath(unicode(path))

    @staticmethod
    def supported_formats(video_only=True):
        mtypes = Phonon.BackendCapabilities.availableMimeTypes()
        mtypes = map(unicode, mtypes)
        LOG.debug('Mime types available: %s', pformat(mtypes))
        if video_only:
            return [mt for mt in mtypes if mt.startswith('video')]
        return mtypes

    @staticmethod
    def supported_extensions(video_only=True):
        extensions = []
        for mt in VideoPlayer.supported_formats(video_only):
            extensions.extend(mimetypes.guess_all_extensions(mt))
        LOG.debug('Video files extensions: %s', extensions)
        return extensions

    def update_time(self, msec):
        current = timedelta(seconds=(msec / 1000))
        total_time = self.player.mediaObject().totalTime()
        total = timedelta(seconds=(total_time / 1000))
        LOG.debug('Time is %s/%s (%d ms)', current, total, msec)
        self.time_changed.emit(current, total)

