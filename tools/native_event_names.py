"""Extract SDK event names by emulating two pure ARM64 lookup functions.

No device connection, JNI initialization, or SDK networking is performed.
Requires pyelftools and unicorn; --runtime may point to an isolated pip target.
The bounded search is not a claim that every event value has been enumerated.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("library", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--runtime", type=Path)
    args = parser.parse_args()
    if args.runtime:
        sys.path.insert(0, str(args.runtime))
    from elftools.elf.elffile import ELFFile
    from unicorn import Uc, UC_ARCH_ARM64, UC_MODE_ARM
    from unicorn.arm64_const import UC_ARM64_REG_X0, UC_ARM64_REG_LR, UC_ARM64_REG_PC

    with args.library.open("rb") as source:
        elf = ELFFile(source)
        if elf['e_machine'] != 'EM_AARCH64':
            raise ValueError('Expected ARM64 SDK')
        segments = [s for s in elf.iter_segments() if s['p_type'] == 'PT_LOAD']
        end = max(s['p_vaddr'] + s['p_memsz'] for s in segments)
        size = (end + 4095) & ~4095
        emulator = Uc(UC_ARCH_ARM64, UC_MODE_ARM)
        emulator.mem_map(0, size + 4096)
        for segment in segments:
            emulator.mem_write(segment['p_vaddr'], segment.data())
        relocations = elf.get_section_by_name('.rela.dyn')
        if relocations:
            for relocation in relocations.iter_relocations():
                if relocation['r_info_type'] == 1027:  # R_AARCH64_RELATIVE; load base 0
                    emulator.mem_write(relocation['r_offset'],
                        int(relocation['r_addend']).to_bytes(8, 'little'))
        symbols = {s.name: s['st_value'] for s in elf.get_section_by_name('.dynsym').iter_symbols()}

        def lookup(name, argument):
            emulator.reg_write(UC_ARM64_REG_X0, argument)
            emulator.reg_write(UC_ARM64_REG_LR, size)
            emulator.emu_start(symbols[name], size, count=2000)
            if emulator.reg_read(UC_ARM64_REG_PC) != size:
                raise RuntimeError('Lookup exceeded instruction budget')
            address = emulator.reg_read(UC_ARM64_REG_X0)
            return bytes(emulator.mem_read(address, 160)).split(b'\0')[0].decode('ascii')

        modules = {str(i): lookup('dt_ut_module_to_string', i) for i in range(14)}
        events = {}
        for module in range(14):
            for value in list(range(256)) + [65535]:
                key = module << 24 | value
                name = lookup('dt_ut_event_to_string', key)
                if name != 'UNKNOWN':
                    events[f'{key:08x}'] = name
    result = dict(sdk_sha256=hashlib.sha256(args.library.read_bytes()).hexdigest(),
        coverage='modules 0..13; low event values 0..255 and 65535; not exhaustive',
        modules=modules, events=events)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(f'{len(modules)} modules, {len(events)} named values (including boundary markers)')


if __name__ == '__main__':
    main()
