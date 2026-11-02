import copy
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest
import har_totals as h


def fixture():
    return {'log': {'entries': [
        {'time': 12.5, 'request': {'url': 'PRIVATE_PLACEHOLDER'}, 'response': {'status': 200, 'bodySize': 120, 'content': {'text': 'PRIVATE_PLACEHOLDER'}}},
        {'time': 7.5, 'response': {'status': 404, 'bodySize': -1}},
        {'time': 0, 'response': {'status': 0, 'bodySize': 0}}]}}

class TotalsTest(unittest.TestCase):
    def report(self, data):
        return h.summarize(json.dumps(data).encode())

    def test_known_arithmetic_and_unknown_sizes(self):
        r = self.report(fixture())
        self.assertEqual((r['entry_count'], r['sum_entry_time_ms'], r['max_entry_time_ms'], r['known_response_body_bytes'], r['unknown_response_body_size_count']), (3, 20, 12.5, 120, 1))
        self.assertEqual(r['status_counts'], {'no_response': 1, '1xx': 0, '2xx': 1, '3xx': 0, '4xx': 1, '5xx': 0})
        self.assertNotIn('PRIVATE_PLACEHOLDER', json.dumps(r))

    def test_empty_is_not_fake_latency(self):
        r = self.report({'log': {'entries': []}})
        self.assertIsNone(r['max_entry_time_ms'])
        self.assertEqual(r['entry_count'], 0)

    def test_all_status_buckets(self):
        d = fixture();d['log']['entries'] = [{'time': 1, 'response': {'status': s, 'bodySize': 0}} for s in (0, 100, 200, 300, 400, 599)]
        self.assertEqual(set(self.report(d)['status_counts'].values()), {1})

    def test_invalid_shapes(self):
        for d in (None, [], {}, {'log': []}, {'log': {'entries': {}}}, {'log': {'entries': [None]}}):
            with self.subTest(d=d), self.assertRaises(h.InvalidHAR):self.report(d)

    def test_invalid_numeric_fields(self):
        for field, values in [('time', [-1, True, '2', None, float('inf'), float('nan'), 10**13]), ('status', [99, 600, True, 200.0]), ('bodySize', [-2, True, 1.5])]:
            for value in values:
                d = fixture(); e = d['log']['entries'][0]
                (e if field == 'time' else e['response'])[field] = value
                with self.subTest(field=field, value=value), self.assertRaises(h.InvalidHAR):self.report(d)

    def test_duplicate_keys_and_bad_encoding(self):
        for raw in (b'{"log":{},"log":{}}', b'\xff', b'{', b'{"log":{"entries":[]},"x":NaN}'):
            with self.assertRaises(h.InvalidHAR):h.summarize(raw)

    def test_utf8_bom(self):
        raw = json.dumps(fixture()).encode()
        self.assertEqual(h.summarize(b"\xef\xbb\xbf" + raw), h.summarize(raw))

    def test_limits(self):
        with self.assertRaises(h.InvalidHAR):h.summarize(b' ' * (h.MAX_BYTES+1))
        with self.assertRaises(h.InvalidHAR):self.report({'log': {'entries': [None]*(h.MAX_ENTRIES+1)}})

    def test_cli_fresh_start_input_unchanged_and_generic_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=pathlib.Path(tmp)/'input.har';raw=json.dumps(fixture()).encode();p.write_bytes(raw)
            command=[sys.executable, str(pathlib.Path(h.__file__)), str(p)]
            run=subprocess.run(command,capture_output=True,text=True)
            self.assertEqual(run.returncode,0);self.assertEqual(json.loads(run.stdout)['entry_count'],3)
            self.assertEqual(p.read_bytes(),raw);self.assertEqual(run.stderr,'')
            p.write_text('PRIVATE_PLACEHOLDER')
            run=subprocess.run(command,capture_output=True,text=True)
            self.assertEqual(run.returncode,2);self.assertEqual(run.stdout,'')
            self.assertNotIn('PRIVATE_PLACEHOLDER',run.stderr);self.assertNotIn(str(p),run.stderr)

if __name__ == '__main__':unittest.main()
