import unittest
from ut_report import decode


class TelemetryTest(unittest.TestCase):
    def report(self, count=1):
        record = (7).to_bytes(2, 'big') + (1700000000).to_bytes(6, 'big')
        record += bytes.fromhex('0b00000d') + (3).to_bytes(8, 'big')
        return b'\x5a\x5a' + (20 * count).to_bytes(2, 'big') + record * count + count.to_bytes(4, 'big') + b'\x5a\x5a'

    def test_exact_field_boundaries(self):
        self.assertEqual(decode(self.report()), [dict(sequence=7, device_timestamp=1700000000,
            event='0b00000d', value=3)])

    def test_multiple_records(self):
        self.assertEqual(len(decode(self.report(12))), 12)

    def test_invalid_reports(self):
        valid = self.report()
        for data in [valid[:-1], b'bad', valid[:-6] + b'\0' * 4 + b'\x5a\x5a',
                     valid[:-6] + (3).to_bytes(4, 'big') + b'\x5a\x5a']:
            with self.assertRaises(ValueError):
                decode(data)


if __name__ == '__main__':
    unittest.main()
