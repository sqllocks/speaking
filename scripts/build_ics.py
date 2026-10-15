#!/usr/bin/env python3
"""Build events.ics from events.json using only the standard library.

Dates are all-day calendar dates in Eastern Time. No talk times are assumed.
DTEND is exclusive under RFC 5545; JSON endDate is inclusive.
"""
import argparse
from datetime import date, datetime, timedelta, timezone
import json
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

ROOT = Path(__file__).resolve().parents[1]


def escape(value):
    return value.replace('\\', '\\\\').replace('\r\n', '\n').replace('\r', '\n').replace('\n', '\\n').replace(';', '\\;').replace(',', '\\,')


def fold(line):
    """Fold at 75 UTF-8 octets without splitting a character (RFC 5545)."""
    parts, current = [], ''
    for char in line:
        if len((current + char).encode('utf-8')) > 75:
            parts.append(current)
            current = ' '
        current += char
    parts.append(current)
    return '\r\n'.join(parts)


def build_calendar(events, stamp=None):
    stamp = stamp or datetime.now(timezone.utc)
    lines = ['BEGIN:VCALENDAR', 'VERSION:2.0',
             'PRODID:-//SQLBites//Speaking Calendar//EN', 'CALSCALE:GREGORIAN',
             'X-WR-CALNAME:SQLBites Speaking Calendar', 'X-WR-TIMEZONE:America/New_York']
    for event in events:
        start = date.fromisoformat(event['date'])
        end = date.fromisoformat(event.get('endDate') or event['date'])
        if end < start:
            raise ValueError('endDate precedes date: ' + event['title'])
        identity = json.dumps([event['date'], event['conference'], event['title']], ensure_ascii=False)
        uid = str(uuid5(NAMESPACE_URL, 'https://speaking.sqlbites.net/events.json#' + identity))
        description = event['conference'] + '\n' + event['title']
        if event.get('conferenceUrl'):
            description += '\nConference: ' + event['conferenceUrl']
        description += '\nMaterials: ' + (event.get('sessionUrl') or 'Materials coming soon')
        lines.extend(['BEGIN:VEVENT', 'UID:' + uid + '@speaking.sqlbites.net',
                      'DTSTAMP:' + stamp.astimezone(timezone.utc).strftime('%Y%m%dT%H%M%SZ'),
                      'DTSTART;VALUE=DATE:' + start.strftime('%Y%m%d'),
                      'DTEND;VALUE=DATE:' + (end + timedelta(days=1)).strftime('%Y%m%d'),
                      'SUMMARY:' + escape(event['title']),
                      'LOCATION:' + escape(event.get('location') or ''),
                      'DESCRIPTION:' + escape(description)])
        url = event.get('sessionUrl') or event.get('conferenceUrl')
        if url:
            lines.append('URL:' + url)
        lines.append('END:VEVENT')
    lines.append('END:VCALENDAR')
    return ('\r\n'.join(fold(line) for line in lines) + '\r\n').encode('utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT / 'events.json')
    parser.add_argument('--output', type=Path, default=ROOT / 'events.ics')
    args = parser.parse_args()
    events = json.loads(args.source.read_text(encoding='utf-8'))['events']
    args.output.write_bytes(build_calendar(events))
    print(f'Wrote {len(events)} events to {args.output}')


if __name__ == '__main__':
    main()
