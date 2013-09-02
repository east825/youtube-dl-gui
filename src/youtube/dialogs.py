# vim: fileencoding=utf-8

from __future__ import unicode_literals
from __future__ import print_function

import logging
import threading
from PyQt4.QtCore import QRegExp, pyqtSignal

from PyQt4.QtGui import *
from youtube.youtubedl_util import YouTubeDLError, download, VALID_URL_REGEX

from youtubedl_util import video_formats

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

    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setWindowTitle('Download Video')

        grid = QGridLayout()

        url_label = QLabel('&URL:')
        self.url_edit = QLineEdit()
        self.url_edit.setValidator(QRegExpValidator(QRegExp(VALID_URL_REGEX.pattern)))
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

        self.url_edit.textEdited.connect(self.show_formats)

        self.__formats = []

    @property
    def url(self):
        return  unicode(self.url_edit.text()).strip()

    def show_formats(self, text):
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


    def accept(self):
        LOG.debug('Entering accept()')
        idx = self.fmt_combo.currentIndex()
        if idx == -1:
            return
        fmt = self.__formats[idx]
        mgr = download(self.url, fmt)
        progress = QProgressDialog('Downloading...', 'Stop', 0, 100, self)
        progress.canceled.connect(lambda: mgr.terminate())
        progress.show()

        dlg = self
        class ProgressThread(threading.Thread):
            def __init__(self):
                super(ProgressThread, self).__init__()

            def run(self):
                for i in mgr.progress():
                    LOG.debug('%d%%', int(i))
                    progress.setValue(int(i))
                progress.close()
                if mgr.path:
                    QApplication.processEvents()
                    dlg.downloaded.emit(mgr.path)

        thread = ProgressThread()
        thread.start()
        super(DownloadDialog, self).accept()






