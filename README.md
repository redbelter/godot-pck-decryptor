# Godot PCK Unpacker

A unified tool for extracting assets from Godot Engine PCK files. Supports both standard Godot PCK and Zombie Diary's custom GST2 format.

## Features

- **Auto-detect format** - Standard Godot (AES-256-CFB) or ZD GST2 (XOR)
- **Extract all assets** - Images (WEBP/JPEG), audio (MP3), and raw files
- **No encryption key needed** for ZD format - key embedded in file
- **Cross-platform** - Pure Python, no dependencies

## Quick Start

```bash
# Extract all assets from ZD.pck
python godot_unpacker.py ZD.pck -o output/

# Extract only images
python godot_unpacker.py ZD.pck --images -o images/

# Extract only audio
python godot_unpacker.py game.pck --audio -o audio/

# Show PCK info
python godot_unpacker.py ZD.pck --info
```

## Supported Formats

| Format | Algorithm | Key Storage | Key |
|--------|-----------|-------------|-----|
| Standard PCK | AES-256-CFB | In executable | 32 bytes |
| ZD GST2 | XOR | In PCK header | 16 bytes |

## Extraction Results (Zombie Diary)

- **WEBP**: 410 files
- **JPEG**: 111 files
- **MP3**: 46 files
- **Total**: 567 files extracted

## Files

| File | Description |
|------|-------------|
| `godot_unpacker.py` | Unified unpacker (auto-detect) |
| `cleanroom.py` | Decryption tool (AES + XOR) |
| `cleanroom_zd.py` | ZD-specific decrypter |
| `create_report.py` | Generate extraction report |
| `create_discord_report.py` | Discord-friendly report |

## License

MIT