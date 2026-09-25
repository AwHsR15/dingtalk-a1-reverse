#!/usr/bin/env python3
"""Offline A1 stream audit. Emits metadata only; no device IDs, keys or audio bytes.

Usage: python tools/audio_stream_metadata.py <local btsnoop file>
The known 0x117 offsets and fixed frame layout are checked, not assumed universal.
"""
import json
import sys
from collections import Counter
from protocol_analyze import collect, parse_header, NTF_HANDLE


def audit(path):
    messages, stats = collect(path, return_stats=True)
    active, reports = {}, []
    for _, handle, raw in messages:
        msg = parse_header(raw)
        if handle != NTF_HANDLE or not msg:
            continue
        payload = msg['payload']
        if msg['cmd'] == 0x116 and payload.startswith(b'{'):
            try:
                header = json.loads(payload)
                attrs = header.get('attrs', '').split('@')
                frame_bytes = int(attrs[3])
                if frame_bytes <= 0:
                    continue
            except (ValueError, TypeError, AttributeError, IndexError):
                continue
            result = dict(file_version=header.get('file_ver'),
                          stream_type=header.get('stream_type'),
                          frame_bytes=frame_bytes, packets=0, frames=0,
                          combined_packets=0, malformed_lengths=0,
                          nonintegral_frames=0, comparisons=0,
                          contiguous_groups=0, discontinuities=0,
                          four_byte_magic_matches=0,
                          payload_lengths=Counter(), index_deltas=Counter())
            reports.append(result)
            active[str(header.get('fid'))] = [result, None]
        elif msg['cmd'] == 0x117 and len(payload) >= 28:
            state = active.get(str(int.from_bytes(payload[4:8], 'big')))
            if not state:
                continue
            result, previous = state
            seq = int.from_bytes(payload[16:20], 'big')
            size = int.from_bytes(payload[20:24], 'big')
            result['packets'] += 1
            result['payload_lengths'][size] += 1
            if size <= 0 or 28 + size > len(payload):
                result['malformed_lengths'] += 1
                continue
            frame_bytes = result['frame_bytes']
            if size % frame_bytes:
                result['nonintegral_frames'] += 1
                continue
            count = size // frame_bytes
            result['frames'] += count
            result['combined_packets'] += int(count > 1)
            for offset in range(28, 28 + size, frame_bytes):
                word = int.from_bytes(payload[offset:offset + 4], 'little')
                result['four_byte_magic_matches'] += int(word >> 22 == 0x2a5)
            if previous is not None:
                delta = seq - previous
                result['index_deltas'][delta] += 1
                result['comparisons'] += 1
                result['contiguous_groups'] += int(delta == count)
                result['discontinuities'] += int(delta != count)
            state[1] = seq
    return dict(reassembly=stats, streams=reports,
                limitation='Known header-matched streams only; continuity does not prove full recording or decodability.')


if __name__ == '__main__':
    print(json.dumps(audit(sys.argv[1]), ensure_ascii=False, indent=2))
