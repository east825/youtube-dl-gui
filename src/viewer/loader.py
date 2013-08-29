# vim: fileencoding=utf-8

from __future__ import unicode_literals
from __future__ import print_function
import os

import tempfile
import mimetypes
from pprint import pprint
from urllib import urlopen
from urlparse import urlparse, parse_qs, unquote

VIDEO_INFO_URL = 'http://www.youtube.com/get_video_info?&video_id={id}'

def _get_param(url, name):
    parts = urlparse(url)
    params = parse_qs(parts.query)
    if name not in params:
        return None
    return params[name][0]

def load_video(url, formats=('.mp4', '.webm')):
    video_id = _get_param(url, 'v')
    if not video_id:
        raise ValueError('URL "{}" must contain "v" query parameter'.format(url))

    info = urlopen(VIDEO_INFO_URL.format(id=video_id)).read().decode('utf-8')
    info = parse_qs(unquote(info))
    pprint(info)
    urls = info['url']
    if 'type' in info:
        types = info['type']
    else:
        types = map(lambda x: x[x.index(','):], info['quality'])
    
    mtypes = filter(None, [mimetypes.types_map.get(f) for f in formats])
    pprint(mtypes)
    targets = []
    for url, type in zip(urls, types):
        print(url, type)
        if filter(lambda x: type.startswith(x), mtypes):
            type = type[:type.index(';')]
            targets.append((url, mimetypes.guess_extension(type)))
    pprint(targets)
    for url, ext in targets:
        fd, path = tempfile.mkstemp(prefix='youtube_', suffix=ext)
        with os.fdopen(fd, 'wb') as f:
            resp = urlopen(url)
            # print(resp.info().items())
            f.write(resp.read())
            yield path


if __name__ == '__main__':
    url = 'http://www.youtube.com/watch?v=Ume5iG30q1k&' \
        'feature=c4-overview-vl&list=PL6A40AB04892E2A1F'
    for path in load_video(url):
        print(path)
