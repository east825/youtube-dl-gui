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


# noinspection PyUnresolvedReferences
import resources.icons

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
                                     clicked=self.rewind_backward,
                                     shortcut='Ctrl+Left'))
        hbox.addWidget(create_button(icon=QIcon(':MD-resume'),
                                     clicked=self.resume,
                                     shortcut='Space'))
        hbox.addWidget(create_button(icon=QIcon(':MD-stop'),
                                     clicked=self.stop,
                                     shortcut='Shift+Space'))
        hbox.addWidget(create_button(icon=QIcon(':MD-fast-forward'),
                                     clicked=self.rewind_forward,
                                     shortcut='Ctrl+Right'))

        hbox.addStretch()

        mute_button = create_button(icon=QIcon(':MD-volume-3'),
                                    checkable=True,
                                    toggled=self.mute,
                                    shortcut='Ctrl+M')
        # hide button borders until mouse pointer hovers it
        mute_button.setAutoRaise(True)
        audio_output = self.player.audioOutput()
        self.volume_slider = Phonon.VolumeSlider(audio_output, self)
        self.volume_slider.setMuteVisible(False)

        def set_volume_icon(ignored):
            level = audio_output.volume()
            if audio_output.isMuted() or level == 0:
                mute_button.setIcon(QIcon(':MD-volume-0-alt'))
            elif level <= 0.33:
                mute_button.setIcon(QIcon(':MD-volume-1'))
            elif level <= 0.66:
                mute_button.setIcon(QIcon(':MD-volume-2'))
            else:
                mute_button.setIcon(QIcon(':MD-volume-3'))

        set_volume_icon(audio_output.volume())
        audio_output.volumeChanged.connect(set_volume_icon)
        audio_output.mutedChanged.connect(set_volume_icon)

        hbox.addWidget(mute_button)
        hbox.addWidget(self.volume_slider)

        vbox.addLayout(hbox)
        self.setLayout(vbox)

        self.path = None

        QShortcut('Space', self, activated=self.resume)
        QShortcut('Shift+Space', self, activated=self.stop)
        QShortcut('Ctrl+M', self, activated=self.mute)
        QShortcut('Ctrl+Left', self, activated=self.rewind_backward)
        QShortcut('Ctrl+Right', self, activated=self.rewind_forward)


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

