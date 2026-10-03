from pathlib import Path
import hashlib
ROM_BANK = 0x4000

def parse_bank_address(value: str) -> tuple[int, int]:
    if ':' not in value:
        raise ValueError('address must use bank:CPU-address notation')
    bank_text, address_text = value.split(':', 1)
    bank, address = int(bank_text, 16), int(address_text, 16)
    bank_address_to_offset(bank, address)
    return bank, address

def bank_address_to_offset(bank: int, address: int) -> int:
    if bank == 0:
        if not 0 <= address <= 0x3fff:
            raise ValueError('bank 00 address must be 0000-3FFF')
        return address
    if bank < 0 or not 0x4000 <= address <= 0x7fff:
        raise ValueError('banked ROM address must be 4000-7FFF')
    return bank * ROM_BANK + address - 0x4000

def parse_address(value: str) -> int:
    if ':' not in value:
        return int(value, 0)
    return bank_address_to_offset(*parse_bank_address(value))

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
