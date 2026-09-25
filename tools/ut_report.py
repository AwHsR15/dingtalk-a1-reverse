"""Decode 0x000C SDK telemetry records from an existing HCI capture, offline.

Record layout verified against SDK 8.5.8.3 ParseNotifyUtReport at 0x231408.
Default output omits event values, which may contain recording identifiers.
"""
import argparse
import json
from pathlib import Path


def decode(payload):
    if len(payload) < 10 or payload[:2] != b'\x5a\x5a':
        raise ValueError('Invalid telemetry header')
    size = int.from_bytes(payload[2:4], 'big')
    if len(payload) < size + 10 or payload[size + 8:size + 10] != b'\x5a\x5a':
        raise ValueError('Truncated report or invalid footer')
    count = int.from_bytes(payload[size + 4:size + 8], 'big') & 255
    if not count or size % count or size // count < 20:
        raise ValueError('Invalid telemetry record count/stride')
    records = []
    for offset in range(4, size + 4, size // count):
        record = payload[offset:offset + 20]
        records.append(dict(sequence=int.from_bytes(record[:2], 'big'),
            device_timestamp=int.from_bytes(record[2:8], 'big'),
            event=f'{int.from_bytes(record[8:12], "big"):08x}',
            value=int.from_bytes(record[12:20], 'big')))
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture', type=Path)
    parser.add_argument('--names', type=Path,
        default=Path(__file__).resolve().parent.parent / 'native_event_names_8.5.8.3.json')
    parser.add_argument('--include-values', action='store_true')
    args = parser.parse_args()
    from protocol_analyze import collect, parse_header
    names = json.loads(args.names.read_text(encoding='utf-8'))['events']
    for timestamp, handle, raw in collect(args.capture):
        frame = parse_header(raw)
        if not frame or frame['cmd'] != 12:
            continue
        for record in decode(frame['payload']):
            record['name'] = names.get(record['event'], 'UNKNOWN')
            record['host_timestamp'] = str(timestamp)
            if not args.include_values:
                record.pop('value')
            print(json.dumps(record))


if __name__ == '__main__':
    main()
