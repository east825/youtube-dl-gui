# vim: fileencoding=utf-8

from __future__ import print_function
from __future__ import unicode_literals

import sys
import re
import subprocess as sp
from collections import namedtuple
import logging

logging.basicConfig(level=logging.DEBUG)

FORMAT_LINE_REGEX = re.compile(
    r'(?P<id>\d+)'              # unique id (itag)
    r'\s+:\s+'
    r'(?P<extension>\w+)'       # video extension
    r'\s+\[(?P<quality>\w+)\]'  # quality, e.g 360x640 or 720p
    r'(?!.*audio)',             # not an audio stream
    re.IGNORECASE
)

PROGRESS_LINE_REGEX = re.compile(
    r'\[download\]\s+'
    r'(?P<percent>\d+\.\d+)%\s+'
    r'of (?P<size>\d+(?:\.\d+)?\w+)',
    re.IGNORECASE
)

VideoFormat = namedtuple('VideoFormat', ['id', 'extension', 'quality'])


def check_available():
    try:
        return sp.check_call(['youtube-dl', '-h']) == 0
    except (OSError, sp.CalledProcessError) as e:
        logging.debug(e.args)
        return False


def video_formats(url):
    p = sp.Popen(['youtube-dl', '-F', url], stdout=sp.PIPE)
    formats = []
    for line in map(str.strip, p.stdout):
        m = FORMAT_LINE_REGEX.match(line)
        if m:
            formats.append(VideoFormat(**m.groupdict()))
    return formats


def download(url, fmt=None, progress=False):
    def gen_progress(p):
        while True:
            # can't use 'for line in p.stdout', because
            # it returns all lines at ones and waits the
            # process to terminate first
            line = p.stdout.readline().strip()
            logging.debug(line)
            if not line:
                break
            m = PROGRESS_LINE_REGEX.match(line)
            if m:
                yield (float(m.group('percent')), m.group('size'))

    args = ['youtube-dl', url]
    if fmt is not None:
        if isinstance(fmt, VideoFormat):
            args.extend(['-f', fmt.id])
        else:
            args.extend(['-f', str(fmt)])
    if progress is True:
        return gen_progress(sp.Popen(args + ['--newline'], stdout=sp.PIPE))
    else:
        return sp.call(args, stdout=sys.stdout)


if __name__ == '__main__':
    import sys
    logging.getLogger().setLevel(logging.WARN)
    # print('Available: ', check_available())
    # pprint(video_formats(sys.argv[1]))
    for p, size in download(sys.argv[1], 5, progress=True):
        n = int(80 * (p / 100))
        print('\r{}{} {}'.format('#' * n, ' ' * (80 - n), size), end='')



