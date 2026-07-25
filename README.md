# PCK File Unpacker

Tools for extracting assets from Godot Engine `.pck` and `.pck` files. Zombie Diary uses a custom PCK format with GST2 encryption.

## Format Overview

### Standard Godot PCK Format
- **Magic:** `GDPC` (0x47445043)
- **Version:** 4 bytes (little-endian)
- **Padding:** 64-112 bytes (varies)
- **File entries:** At offset 0x50 or 0x70
- **Encryption:** Optional AES-256-CFB (configure at export time)

### Zombie Diary GST2 Custom Format
- **Custom PCK variant** with GDPC magic
- **GST2 header** at offset 0x70:
  - `GST2` magic (4 bytes)
  - Version (4 bytes)
  - Entry count (4 bytes)  
  - Data offset (4 bytes)
- **XOR encryption:** Uses GST2 header bytes as 16-byte key
- **File entries** at offset 0x80

## Tools

| File | Description |
|------|-------------|
| [cleanroom.py](cleanroom.py) | Unified decrypter (AES-256-CFB + GST2 XOR auto-detect) |
| [cleanroom_zd.py](cleanroom_zd.py) | ZD-specific decrypter (streaming for large files) |

## Extraction Scripts

| File | Description |
|------|-------------|
| [extract_ctex.py](extract_ctex.py) | Extract WEBP/JPEG from .ctex files (texture extraction) |
| [extract_jpeg.py](extract_jpeg.py) | JPEG extraction from .ctex files |
| [extract_mp3str.py](extract_mp3str.py) | MP3 audio extraction from .mp3str files |

## Quick Start

```bash
# Decrypt ZD PCK (auto-detects format)
python cleanroom.py --pck ZD.pck --output decrypted.pck

# Extract assets
python extract_ctex.py -i decrypted.pck -o extracted/
python extract_jpeg.py -i decrypted.pck -o extracted/
python extract_mp3str.py -i decrypted.pck -o extracted/
```

## Extraction Results (Zombie Diary)

| Format | Files | Status |
|--------|-------|--------|
| WEBP (.webp) | 410 | ✅ Extracted |
| JPEG (.jpg) | 111 | ✅ Extracted |
| MP3 (.mp3) | 46 | ✅ Extracted |
| **Total** | **567** | **Completed** |

**Remaining:** 58 .ctex files (need additional analysis)

## GST2 XOR Key (ZD-specific)

```
475354320100000000050000d0020000
= GST2\x01\x00\x00\x00\x00\x05\x00\x00\xd0\x02\x00\x00
```

## License

MIT License - for educational and reverse-engineering purposes.