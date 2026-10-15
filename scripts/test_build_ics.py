#!/usr/bin/env python3
"""Parse generated iCalendar back independently; standard library only."""
from datetime import date, datetime, timedelta, timezone
import json
from pathlib import Path
import re
import unittest

from build_ics import build_calendar

ROOT = Path(__file__).resolve().parents[1]


def text_value(value):
    return re.sub(r'\\([nN,;\\])', lambda m: '\n' if m[1] in 'nN' else m[1], value)


def parse_calendar(raw):
    if not raw.endswith(b'\r\n') or b'\n' in raw.replace(b'\r\n', b''):
        raise ValueError('Calendar must use CRLF')
    physical = raw[:-2].split(b'\r\n')
    if any(len(line) > 75 for line in physical):
        raise ValueError('Line exceeds 75 octets')
    lines = []
    for line in physical:
        decoded = line.decode('utf-8')
        if decoded.startswith((' ', '\t')):
            lines[-1] += decoded[1:]
        else:
            lines.append(decoded)
    if lines[0] != 'BEGIN:VCALENDAR' or lines[-1] != 'END:VCALENDAR':
        raise ValueError('Missing calendar wrapper')
    if 'VERSION:2.0' not in lines or not any(x.startswith('PRODID:') for x in lines):
        raise ValueError('Missing calendar properties')
    events, current = [], None
    for line in lines[1:-1]:
        if line == 'BEGIN:VEVENT':
            if current is not None:
                raise ValueError('Nested event')
            current = {}
        elif line == 'END:VEVENT':
            if current is None:
                raise ValueError('Unexpected event end')
            for key in ('UID', 'DTSTAMP', 'DTSTART;VALUE=DATE', 'DTEND;VALUE=DATE', 'SUMMARY'):
                if key not in current:
                    raise ValueError('Missing ' + key)
            datetime.strptime(current['DTSTAMP'], '%Y%m%dT%H%M%SZ')
            events.append(current)
            current = None
        elif current is not None:
            key, value = line.split(':', 1)
            if key in current:
                raise ValueError('Duplicate property')
            current[key] = value
    if current is not None:
        raise ValueError('Unclosed event')
    return events


class CalendarTests(unittest.TestCase):
    def setUp(self):
        self.source = json.loads((ROOT / 'events.json').read_text())['events']
        self.stamp = datetime(2026, 10, 15, tzinfo=timezone.utc)

    def assert_matches_source(self, raw):
        parsed = parse_calendar(raw)
        self.assertEqual(len(parsed), len(self.source))
        self.assertEqual(len({e['UID'] for e in parsed}), len(parsed))
        for expected, actual in zip(self.source, parsed):
            self.assertEqual(text_value(actual['SUMMARY']), expected['title'])
            self.assertEqual(text_value(actual['LOCATION']), expected['location'])
            self.assertEqual(actual['DTSTART;VALUE=DATE'], expected['date'].replace('-', ''))
            exclusive = date.fromisoformat(expected.get('endDate') or expected['date']) + timedelta(days=1)
            self.assertEqual(actual['DTEND;VALUE=DATE'], exclusive.strftime('%Y%m%d'))
            self.assertEqual(actual.get('URL'), expected['sessionUrl'] or expected['conferenceUrl'] or None)
            self.assertIn(expected['conference'], text_value(actual['DESCRIPTION']))
            if not expected['sessionUrl']:
                self.assertIn('Materials coming soon', text_value(actual['DESCRIPTION']))

    def test_generated_feed(self):
        self.assert_matches_source(build_calendar(self.source, self.stamp))

    def test_committed_feed(self):
        self.assert_matches_source((ROOT / 'events.ics').read_bytes())

    def test_uid_stable_across_rebuilds_and_reordering(self):
        first = parse_calendar(build_calendar(self.source, self.stamp))
        second = parse_calendar(build_calendar(list(reversed(self.source)), self.stamp + timedelta(days=1)))
        self.assertEqual([e['UID'] for e in first], list(reversed([e['UID'] for e in second])))

    def test_text_escaping_unicode_folding_and_date_boundaries(self):
        event = dict(self.source[0], title='Café, SQL; \\ demo\n' + '日' * 70,
                     date='2026-12-31', endDate='2026-12-31', location='Room, A; B\\C\nD')
        parsed = parse_calendar(build_calendar([event], self.stamp))[0]
        self.assertEqual(text_value(parsed['SUMMARY']), event['title'])
        self.assertEqual(text_value(parsed['LOCATION']), event['location'])
        self.assertEqual(parsed['DTEND;VALUE=DATE'], '20270101')

    def test_reject_reversed_date_range(self):
        with self.assertRaises(ValueError):
            build_calendar([dict(self.source[0], endDate='2026-01-01')], self.stamp)


if __name__ == '__main__':
    unittest.main()
