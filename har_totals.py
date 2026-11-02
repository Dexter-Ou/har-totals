#!/usr/bin/env python3
"""Bounded HAR aggregate report; never emits source text fields."""
import argparse
import json
import math
import sys

MAX_BYTES = 16 * 1024 * 1024
MAX_ENTRIES = 10000
MAX_NUMBER = 10**12

class InvalidHAR(ValueError):
    pass

def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InvalidHAR()
        result[key] = value
    return result

def number(value, integer=False, minimum=0):
    if type(value) not in ((int,) if integer else (int, float)):
        raise InvalidHAR()
    if not minimum <= value <= MAX_NUMBER or not math.isfinite(value):
        raise InvalidHAR()
    return value

def summarize(raw):
    if len(raw) > MAX_BYTES:
        raise InvalidHAR()
    try:
        data = json.loads(raw.decode('utf-8-sig'), object_pairs_hook=unique_object,
                          parse_constant=lambda _: (_ for _ in ()).throw(InvalidHAR()))
        entries = data['log']['entries']
        if type(entries) is not list or len(entries) > MAX_ENTRIES:
            raise InvalidHAR()
        buckets = {k: 0 for k in ('no_response', '1xx', '2xx', '3xx', '4xx', '5xx')}
        times = []
        known_bytes = 0
        unknown_sizes = 0
        for entry in entries:
            duration = number(entry['time'])
            response = entry['response']
            status = number(response['status'], integer=True)
            if status != 0 and not 100 <= status <= 599:
                raise InvalidHAR()
            size = number(response['bodySize'], integer=True, minimum=-1)
            buckets['no_response' if status == 0 else str(status // 100) + 'xx'] += 1
            times.append(duration)
            if size == -1:
                unknown_sizes += 1
            else:
                known_bytes += size
        return {'format': 'har-totals-v1', 'entry_count': len(entries),
                'status_counts': buckets, 'sum_entry_time_ms': math.fsum(times),
                'max_entry_time_ms': max(times, default=None),
                'known_response_body_bytes': known_bytes,
                'unknown_response_body_size_count': unknown_sizes}
    except (KeyError, TypeError, ValueError, UnicodeError, RecursionError, OverflowError):
        raise InvalidHAR() from None

def main():
    parser = argparse.ArgumentParser(description='Aggregate HAR counts, durations and body sizes offline. No source text fields in report.')
    parser.add_argument('input', help='UTF-8 HAR file; maximum 16 MiB and 10000 entries')
    args = parser.parse_args()
    try:
        with open(args.input, 'rb') as source:
            report = summarize(source.read(MAX_BYTES + 1))
    except (OSError, InvalidHAR):
        print('HAR Totals: unreadable, unsupported, oversized or invalid input.', file=sys.stderr)
        return 2
    print(json.dumps(report, sort_keys=True, allow_nan=False))
    return 0

if __name__ == '__main__':
    sys.exit(main())
