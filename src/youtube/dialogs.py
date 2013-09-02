# vim: fileencoding=utf-8

from __future__ import unicode_literals
from __future__ import print_function

import logging

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from youtubedl_util import video_formats
from youtubedl_util import YouTubeDLError, download, VALID_URL_RE
from itertools import imap

LOG = logging.getLogger('youtube.dialogs')


class StringListDialog(QDialog):
    def __init__(self, parent, items):
        QDialog.__init__(self, parent)
        layout = QVBoxLayout()
        list_widget = QListWidget()
        for label in map(unicode, items):
            list_widget.addItem(label)
        layout.addWidget(list_widget, 1)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        layout.addWidget(buttons)
        self.setLayout(layout)


class DownloadDialog(QDialog):
    downloaded = pyqtSignal(unicode, name='downloaded')
    # TODO: function local signals?
    progress_updated = pyqtSignal(int, name='progress_updated')

    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setWindowTitle('Download Video')

        grid = QGridLayout()

        url_label = QLabel('&URL:')
        self.url_edit = QLineEdit()
        self.url_edit.setValidator(QRegExpValidator(QRegExp(VALID_URL_RE.pattern)))
        url_label.setBuddy(self.url_edit)
        grid.addWidget(url_label, 0, 0)
        grid.addWidget(self.url_edit, 0, 1)

        fmt_label = QLabel('Available &Formats:')
        self.fmt_combo = QComboBox()
        fmt_label.setBuddy(self.fmt_combo)
        grid.addWidget(fmt_label, 1, 0)
        grid.addWidget(self.fmt_combo, 1, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        vbox = QVBoxLayout()
        vbox.addLayout(grid)
        vbox.addWidget(buttons)
        self.setLayout(vbox)

        self.url_edit.textEdited.connect(self._show_formats)

        self.__formats = []
        self.__progress = None

        self.progress_updated.connect(self._update_progress)

    @property
    def url(self):
        return unicode(self.url_edit.text()).strip()

    def _show_formats(self, text):
        LOG.debug('Entering show_formats()')
        if not self.url:
            return
        self.fmt_combo.clear()
        try:
            self.__formats = video_formats(self.url)
            for fmt in self.__formats:
                self.fmt_combo.addItem('{}: {}'.format(fmt.extension, fmt.quality))
        except YouTubeDLError as e:
            QMessageBox.warning(self, 'youtube-dl error', e.message)

    def _update_progress(self, n):
        if self.__progress is None:
            LOG.error("update_progress() was called when progress doesn't exist")
            return
        self.__progress.setValue(n)

    def accept(self):
        LOG.debug('Entering accept()')
        idx = self.fmt_combo.currentIndex()
        if idx == -1:
            return
        fmt = self.__formats[idx]
        mgr = download(self.url, fmt)
        progress = QProgressDialog('Downloading...', 'Stop', 0, 100, self)
        def on_canceled():
            mgr.terminate()
            thread.wait()

        progress.canceled.connect(on_canceled)
        progress.show()
        self.__progress = progress

        dlg = self

        class ProgressThread(QThread):
            def run(self):
                try:
                    for i in imap(int, mgr.progress()):
                        LOG.debug('%d%%', i)
                        dlg.progress_updated.emit(i)
                except YouTubeDLError as e:
                    QMessageBox.warning(dlg, 'youtube-dl error', e.message)
                finally:
                    LOG.debug('Closing progress dialog')
                    progress.canceled.emit()

        thread = ProgressThread()

        def on_finished():
            if mgr.path:
                self.downloaded.emit(mgr.path)
            # dispose resources
            thread.deleteLater()
        thread.finished.connect(on_finished)

        # thread will run in background managing non-modal progress dialog
        thread.start()
        super(DownloadDialog, self).accept()





