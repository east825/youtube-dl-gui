# vim: fileencoding=utf-8

from __future__ import unicode_literals
from __future__ import print_function
from datetime import timedelta
import os

from pprint import pformat
import sys
import re
import subprocess as sp
from collections import namedtuple
import logging


LOG = logging.getLogger('youtube.youtubedl_util')

VALID_URL_REGEX = re.compile(r'^(https?://)(www\.)?youtube\.com/watch\?v=\w+', re.I)

FORMAT_LINE_REGEX = re.compile(
    r'(?P<id>\d+)'              # unique id (itag)
    r'\s+:\s+'
    r'(?P<extension>\w+)'       # video extension
    r'\s+\[(?P<quality>\w+)\]'  # quality, e.g 360x640 or 720p
    r'(?!.*audio)', # not an audio stream
    re.IGNORECASE
)

PROGRESS_LINE_REGEX = re.compile(
    r'\[download\]\s+'
    r'(?P<percent>\d+\.\d+)%\s+'
    r'of (?P<size>\S+)\s+'
    r'at (?P<speed>\S+)\s+'
    r'ETA (?P<eta>\S+)',
    re.IGNORECASE
)

DESTINATION_LINE_REGEX = re.compile('\[download]\]\s+Destination: (?P<path>.*)')
ALREADY_DOWNLOADED_LINE_REGEX = re.compile(
    '\[download\]\s+(?P<path>.*)\s+has already been downloaded')

VideoFormat = namedtuple('VideoFormat', ['id', 'extension', 'quality'])


class YouTubeDLError(Exception):
    pass


def _check_valid_url(url):
    # TODO: more meaningful check for list param
    if not VALID_URL_REGEX.match(url) or 'list=' in url:
        raise ValueError('Not a valid YouTube video URL: {}'.format(url))


def _extract_error(lines):
    if isinstance(lines, basestring):
        lines = lines.splitlines()
    for line in lines:
        if line.startswith('ERROR:'):
            _, errmsg = line.split(maxsplit=1)
            return errmsg


def check_available():
    try:
        sp.check_call(['youtube-dl', '-h'])
        return True
    except (OSError, sp.CalledProcessError) as e:
        LOG.debug(e.args)
        return False


def video_formats(url):
    LOG.debug('Entering video_formats()')
    _check_valid_url(url)
    try:
        output = sp.check_output(['youtube-dl', '-F', url])
    except sp.CalledProcessError:
        raise YouTubeDLError(_extract_error(output))
    formats = []
    for line in map(str.strip, output.splitlines()):
        LOG.debug(line)
        m = FORMAT_LINE_REGEX.match(line)
        if m:
            formats.append(VideoFormat(**m.groupdict()))
    LOG.debug(pformat(formats))
    return formats


class DownloadManager(object):
    def __init__(self, *args, **kwargs):
        self.__args = args
        self.__kwargs = kwargs
        self.__kwargs['stdout'] = sp.PIPE
        self.path = None
        self.already_downloaded = False
        self.process = None

    def run(self):
        for _ in self.progress():
            pass
        return self.path

    def __iter__(self):
        return self.progress()

    def terminate(self):
        try:
            if self.process.poll() is None:
                self.process.terminate()
        except OSError:
            pass

    def progress(self, size=False, eta=False, speed=False):
        def gen_progress(p):
            while True:
                # can't use 'for line in p.stdout', because
                # it returns all lines at ones and waits the
                # process to terminate first
                line = p.stdout.readline().strip()
                LOG.debug(line)
                if not line:
                    break
                m = PROGRESS_LINE_REGEX.match(line)
                if m:
                    info = [float(m.group('percent'))]
                    if size:
                        info.append(m.group('size'))
                    if speed:
                        info.append(m.group('speed'))
                    if eta:
                        hours, minutes = m.group('eta').split(':')
                        if not hours.isdigit() or not minutes.isdigit():
                            info.append(None)
                        else:
                            info.append(timedelta(hours=int(hours), minutes=int(minutes)))
                    yield info[0] if len(info) == 1 else tuple(info)
                m = ALREADY_DOWNLOADED_LINE_REGEX.match(line)
                if m:
                    LOG.debug('File already downloaded')
                    self.already_downloaded = True
                    self.path = os.path.join(os.getcwd(), m.group('path').strip())
                m = DESTINATION_LINE_REGEX.match(line)
                if m:
                    LOG.debug('Destination extracted')
                    self.path = os.path.join(os.getcwd(), m.group('path').strip())
                elif line.startswith('ERROR:'):
                    raise YouTubeDLError(_extract_error(line))

        p = sp.Popen(*self.__args, **self.__kwargs)
        self.process = p
        return gen_progress(p)


def download(url, fmt=None):
    _check_valid_url(url)
    args = ['youtube-dl', '--newline']
    if fmt is not None:
        if isinstance(fmt, VideoFormat):
            args.extend(['-f', fmt.id])
        else:
            args.extend(['-f', str(fmt)])
    args.append(url)
    return DownloadManager(args)


if __name__ == '__main__':
    import sys

    print('Available: ', check_available())
    # pprint(video_formats(sys.argv[1]))
    # for p, size in download(sys.argv[1], 5, progress=True):
    #     n = int(80 * (p / 100))
    #     print('\r{}{} {}'.format('#' * n, ' ' * (80 - n), size), end='')



