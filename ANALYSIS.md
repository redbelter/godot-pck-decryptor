|# ZD.pck Format Analysis

## File Information

| File | Size | Version |
|------|------|---------|
| ZD.exe | 104.5 MB (104,521,728 bytes) | Windows PE32+ x86-64 (MPRESS packed) |
| ZD.pck | 1,380 MB (1,447,035,884 bytes) | GDPC v3 + GST2 |

**Total extracted assets:** 567 files (WEBP: 410, JPEG: 111, MP3: 46)

## Format Overview

ZD.pck uses a **custom GDPC format** with **GST2 XOR encryption**. It differs from standard Godot PCK in the following ways:

| Aspect | Standard Godot | ZD.pck (GST2) |
|--------|----------------|-----------------|
| **Header structure** | 64-byte padding | GST2 header at 0x70 |
| **GST2 header** | None | Present at offset 0x70 |
| **Encryption** | Optional AES-256-CFB | GST2 XOR (16-byte key) |
| **Key location** | In executable template | Embedded in PCK (GST2 header) |

## GST2 Format Structure

```
Offset 0x0:   GDPC magic (0x47445043)
Offset 0x4:   Version (4 bytes)
Offset 0x8:   Unknown1 (4 bytes)
Offset 0xC:   Unknown2 = 0x06 (ZD format marker)
Offset 0x10:  File count (4 bytes)
Offset 0x18:  Section offset = 0x70
Offset 0x70:  GST2 header (16 bytes) - XOR key
  - "GST2" magic (4 bytes)
  - Version (4 bytes)
  - Entry count (4 bytes)
  - Data offset (4 bytes)
Offset 0x80:  File entries (encrypted with GST2 XOR)
Offset 0x2d0: Encrypted content
```

## Extraction Process

1. **Read GST2 key** from offset 0x70 (16 bytes)
2. **Decrypt data** starting at offset 0x80 using XOR with GST2 key
3. **Parse decrypted entries** to find file paths and offsets
4. **Extract file data** from decrypted content

## Key Differences from Standard Godot

The GST2 format replaces the standard Godot PCK structure with:
- GST2 header embedded in PCK (no external key needed)
- 16-byte XOR key instead of 32-byte AES key
- Custom entry structure with 48-byte entries
- No standard encryption flag - entire region XOR-encrypted

| This makes ZD.pck **simpler to decrypt** (no need to unpack executable) but **less secure** (key is embedded in file). |

## Remaining Files Analysis

The ZD.pck contains 58 remaining .ctex files that need additional analysis. These fall into two categories:

| Type | Count | Description |
|------|-------|-------------|
| Metadata files | ~5 | Small files with JSON metadata, already extracted |
| Texture files | ~53 | Large files (3MB+) with GST2 header, need extraction |

### Why Some Files Remain

The 58 remaining .ctex files likely need analysis because:

1. **They're metadata files** - Small .ctex files contain only resource metadata (path + JSON metadata), not actual texture data
2. **Different compression format** - Some may use a different texture compression than standard WEBP/JPEG
3. **Need PCK extraction** - These files are stored inside ZD.pck, not in the extracted_files folder

To extract these files, use the `godot_unpacker.py` tool with the `-o` option to extract to a new directory.
