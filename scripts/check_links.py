#!/usr/bin/env python3
"""Check all nonempty sessionUrl values and local session HTML href/src links.

Empty sessionUrl is permitted for Topic TBD; no target has been supplied.
Query strings and fragments do not change the file resolved by GitHub Pages.
External links in session pages are outside the scope of this offline check.
"""
from html.parser import HTMLParser
import json
from pathlib import Path
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
HOST = (ROOT / 'CNAME').read_text().strip()


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in ('href', 'src') and value is not None:
                self.links.append(value)


def resolve(link, source, required=False):
    url = urlsplit(link)
    if url.netloc:
        if url.hostname != HOST or url.scheme not in ('http', 'https', ''):
            if required:
                raise ValueError('sessionUrl is outside this repository: ' + link)
            return None
        target = ROOT / unquote(url.path).lstrip('/')
    elif url.scheme:
        if required:
            raise ValueError('unsupported sessionUrl: ' + link)
        return None
    else:
        path = unquote(url.path)
        target = ROOT / path.lstrip('/') if path.startswith('/') else source.parent / (path or source.name)
    target = target.resolve()
    if not target.is_relative_to(ROOT):
        raise ValueError('link escapes repository: ' + link)
    if target.is_dir():
        target /= 'index.html'
    if not target.is_file():
        raise ValueError('missing file: ' + link + ' -> ' + str(target.relative_to(ROOT)))
    return target


def main():
    errors, checked, pending = [], 0, 0
    for event in json.loads((ROOT / 'events.json').read_text())['events']:
        if not event['sessionUrl']:
            pending += 1
            continue
        try:
            resolve(event['sessionUrl'], ROOT / 'index.html', required=True)
            checked += 1
        except ValueError as exc:
            errors.append(event['title'] + ': ' + str(exc))
    for page in sorted((ROOT / 'sessions').glob('*/index.html')):
        parser = Links()
        parser.feed(page.read_text())
        for link in parser.links:
            try:
                if resolve(link, page) is not None:
                    checked += 1
            except ValueError as exc:
                errors.append(str(page.relative_to(ROOT)) + ': ' + str(exc))
    for error in errors:
        print(error, file=sys.stderr)
    print(f'Checked {checked} repository links; {pending} calendar entries await materials; {len(errors)} errors.')
    return bool(errors)


if __name__ == '__main__':
    sys.exit(main())
