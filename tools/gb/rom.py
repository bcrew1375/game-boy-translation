from pathlib import Path
import hashlib
ROM_BANK = 0x4000

def parse_address(value: str) -> int:
    if ':' not in value:
        return int(value, 0)
    b, a = value.split(':', 1)
    bank, addr = int(b, 16), int(a, 16)
    if bank == 0:
        if not 0 <= addr <= 0x3fff: raise ValueError('bank 00 address must be 0000-3FFF')
        return addr
    if not 0x4000 <= addr <= 0x7fff: raise ValueError('banked ROM address must be 4000-7FFF')
    return bank * ROM_BANK + addr - 0x4000

def header(path: str):
    data = Path(path).read_bytes()
    if len(data) < 0x150: raise ValueError('file too small for Game Boy header')
    title = data[0x134:0x143].split(b'\0',1)[0].decode('ascii','replace')
    cgb = data[0x143]
    target = 'CGB required' if cgb == 0xC0 else ('DMG + CGB' if cgb == 0x80 else 'DMG')
    return {'path': path, 'size_bytes': len(data), 'banks': (len(data)+ROM_BANK-1)//ROM_BANK,
            'title': title, 'target': target, 'cgb_flag': f'0x{cgb:02X}',
            'cartridge_type': f'0x{data[0x147]:02X}', 'rom_size_code': f'0x{data[0x148]:02X}',
            'ram_size_code': f'0x{data[0x149]:02X}', 'sha256': hashlib.sha256(data).hexdigest()}
