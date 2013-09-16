# vim: fileencoding=utf-8

from __future__ import unicode_literals
from __future__ import print_function

import logging
import os

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from youtubedl_util import video_formats
from youtubedl_util import YouTubeDLError, download

VALID_URL_RE = r'^(https?://)?(www\.)?youtube\.com/watch\?v=\w+.*$'

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
    downloaded = pyqtSignal(unicode)

    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setWindowTitle('Download Video')

        self.settings = QSettings()

        grid = QGridLayout()

        url_label = QLabel('&URL:')
        self.url_edit = QLineEdit()
        self.url_edit.setFocus()
        self.url_edit.setMinimumWidth(300)
        self.url_edit.setPlaceholderText('Enter YouTube URL here')
        self.url_edit.setValidator(QRegExpValidator(QRegExp(VALID_URL_RE)))
        self.url_edit.textEdited.connect(self.show_formats)
        url_label.setBuddy(self.url_edit)
        grid.addWidget(url_label, 0, 0)
        grid.addWidget(self.url_edit, 0, 1)

        self.format_label = QLabel('&Formats:')
        self.format_combo = QComboBox()
        self.format_label.setBuddy(self.format_combo)

        self.path_edit = QLineEdit()
        self.path_label = QLabel('&Path')
        self.path_label.setBuddy(self.path_edit)

        grid.addWidget(self.format_label, 1, 0)
        grid.addWidget(self.format_combo, 1, 1)
        grid.addWidget(self.path_label, 2, 0)
        grid.addWidget(self.path_edit, 2, 1)


        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.ok_button = buttons.button(QDialogButtonBox.Ok)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        vbox = QVBoxLayout()
        vbox.addLayout(grid)
        vbox.addWidget(buttons)
        self.setLayout(vbox)

        self.hide_components(True)


    @property
    def url(self):
        return unicode(self.url_edit.text()).strip()

    @property
    def path(self):
        return unicode(self.path_edit.text()).strip()

    def hide_components(self, hide):
        self.format_label.setHidden(hide)
        self.format_combo.setHidden(hide)
        self.path_label.setHidden(hide)
        self.path_edit.setHidden(hide)
        self.ok_button.setEnabled(not hide)
        if not hide:
            path = unicode(self.settings.value('Downloader/NameFormat').toString())
            dirname = unicode(self.settings.value('Downloader/DefaultDirectory').toString())
            if dirname and os.path.exists(dirname):
                dirname = os.path.abspath(dirname)
                path = os.path.join(dirname, path)
            self.path_edit.setText(path)

    def show_formats(self, text):
        self.url_edit.setStyleSheet('background: none')
        if not self.url:
            self.hide_components(True)
            return
        try:
            formats = video_formats(self.url)
            self.format_combo.clear()
            for fmt in formats:
                line = '{}: {}'.format(fmt.extension, fmt.quality)
                self.format_combo.addItem(line, QVariant(fmt))
            self.hide_components(False)
        except (YouTubeDLError, ValueError) as e:
            if isinstance(e, YouTubeDLError):
                QMessageBox.warning(self, 'youtube-dl error', 'Error')
            self.url_edit.setStyleSheet('background: #E76666')
            self.hide_components(True)

    def accept(self):
        idx = self.format_combo.currentIndex()
        if idx == -1:
            return
        fmt = self.format_combo.itemData(idx).toPyObject()
        mgr = download(self.url, fmt, path=self.path)
        progress = QProgressDialog('Downloading...', 'Stop', 0, 100, self)

        def on_canceled():
            mgr.terminate()
            thread.wait()

        progress.canceled.connect(on_canceled)
        progress.show()

        dlg = self

        class ProgressUpdater(QThread):
            progress_updated = pyqtSignal(int)

            def run(self):
                try:
                    for i in mgr.progress():
                        self.progress_updated.emit(int(i))
                except YouTubeDLError as e:
                    QMessageBox.warning(dlg, 'youtube-dl error', e.message)
                finally:
                    LOG.debug('Closing progress dialog')
                    progress.canceled.emit()

        thread = ProgressUpdater()
        thread.progress_updated.connect(progress.setValue)

        def on_finished():
            if mgr.path:
                self.downloaded.emit(mgr.path)
                # dispose resources
            thread.deleteLater()

        thread.finished.connect(on_finished)

        # thread will run in background managing non-modal progress dialog
        thread.start()
        super(DownloadDialog, self).accept()


