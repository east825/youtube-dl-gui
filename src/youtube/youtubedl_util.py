# vim: fileencoding=utf-8

from __future__ import unicode_literals
from __future__ import print_function
from datetime import timedelta
import os

from pprint import pformat
import sys
import platform
import re
import subprocess as sp
from collections import namedtuple
import logging
from urllib import urlencode
from urlparse import parse_qs, urlunparse, urljoin, urlunsplit, urlsplit
from youtube.settings import get_installation_directory

CONSOLE_ENCODING = 'cp1251' if platform.system() == 'Windows' else sys.stdout.encoding

LOG = logging.getLogger('youtube.youtubedl_util')

FORMAT_LINE_RE = re.compile(
    r'(?P<id>\d+)'              # unique id (itag)
    r'\s+:\s+'
    r'(?P<extension>\w+)'       # video extension
    r'\s+\[(?P<quality>\w+)\]'  # quality, e.g 360x640 or 720p
    r'(?!.*audio)', # not an audio stream
    re.IGNORECASE
)

PROGRESS_LINE_RE = re.compile(
    r'\[download\]\s+'
    r'(?P<percent>\d+\.\d+)%\s+'
    r'of (?P<size>\S+)\s+'
    r'at (?P<speed>\S+)\s+'
    r'ETA (?P<eta>\S+)',
    re.IGNORECASE
)

DESTINATION_LINE_RE = re.compile(r'\[download\]\s+Destination: (?P<path>.*)')
ALREADY_DOWNLOADED_LINE_RE = re.compile(r'\[download\]\s+(?P<path>.*)\s+has already been downloaded')
ERROR_LINE_RE = re.compile(r'ERROR:\s+(?P<message>.*)')

VideoFormat = namedtuple('VideoFormat', ['id', 'extension', 'quality'])


class YouTubeDLError(Exception): pass


def prepare_url(url):
    scheme, netloc, path, query, _ = urlsplit(url)
    qs_params = parse_qs(query, keep_blank_values=False)
    if not netloc.endswith('youtube.com') or 'v' not in qs_params:
        raise ValueError('Not a valid YouTube video URL: {}'.format(url))
    video_id = qs_params['v'][0]
    # filter out fragment and all params except video id ('v')
    sanitized = urlunsplit((scheme, netloc, path, urlencode({'v': video_id}), ''))
    LOG.debug('Prepared URL: %s', sanitized)
    return sanitized


def _extract_error(lines):
    if isinstance(lines, basestring):
        lines = lines.splitlines()
    for line in lines:
        if line.startswith('ERROR:'):
            _, errmsg = line.split(':', maxsplit=1)
            return errmsg.lstrip()


def check_available():
    try:
        sp.check_call(['youtube-dl', '-h'])
        return True
    except (OSError, sp.CalledProcessError) as e:
        LOG.debug(e.args)
        return False


def video_formats(url):
    LOG.debug('Entering video_formats()')
    url = prepare_url(url)
    try:
        output = sp.check_output(['youtube-dl', '-F', url])
    except sp.CalledProcessError as e:
        raise Exception(_extract_error(e.output))
    formats = []
    for line in map(str.strip, output.splitlines()):
        LOG.debug(line)
        m = FORMAT_LINE_RE.match(line)
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
                line = p.stdout.readline()
                if not line:
                    LOG.debug("No more lines in process' stdout ")
                    break
                line = line.rstrip().decode(CONSOLE_ENCODING)
                LOG.debug(line)
                m = ALREADY_DOWNLOADED_LINE_RE.match(line)
                if m:
                    dest = m.group('path').strip()
                    LOG.debug('File already downloaded. Destination: %s', dest)
                    self.already_downloaded = True
                    self.path = os.path.join(os.getcwd(), dest)
                m = DESTINATION_LINE_RE.match(line)
                if m:
                    dest = m.group('path').strip()
                    LOG.debug('Destination extracted: %s', dest)
                    self.path = os.path.join(os.getcwd(), dest)
                m = ERROR_LINE_RE.match(line)
                if m:
                    message = m.group('message')
                    LOG.error('Error found: %s', message)
                    raise YouTubeDLError(message)
                m = PROGRESS_LINE_RE.match(line)
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

        p = sp.Popen(*self.__args, **self.__kwargs)
        self.process = p
        return gen_progress(p)


def download(url, fmt=None, path=None):
    url = prepare_url(url)
    binary = os.path.join(get_installation_directory(), 'bin', 'youtube-dl')
    # search in path if doesn't exist
    if not os.path.exists(binary):
        LOG.debug('Using system-wide youtube-dl (if any)')
        binary = 'youtube-dl'
    else:
        LOG.debug('Using downloaded youtube-dl at "%s"', binary)
    args = [binary, '--newline']
    if fmt is not None:
        if isinstance(fmt, VideoFormat):
            args.extend(['-f', fmt.id])
        else:
            args.extend(['-f', str(fmt)])
    if path:
        args.extend(['-o', path])
    args.append(url)
    return DownloadManager(args)



