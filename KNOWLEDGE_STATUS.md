# Extraction Status (Zombie Diary)

**Last Updated:** Saturday, July 25, 2026

## Files Extracted

| Format | Count | Description |
|--------|-------|-------------|
| WEBP | 410 | Web Picture Format - compressed textures |
| JPEG | 111 | Joint Photographic Experts Group - compressed textures |
| MP3 | 46 | Audio files (streaming audio) |
| **Total** | **567** | Successfully extracted |

## Remaining Analysis

| Format | Count | Status |
|--------|-------|--------|
| .ctex | 58 | Need additional analysis for format |

## Tools Used

- `godot_unpacker.py` - Unified PCK unpacker with GST2 support
- `cleanroom.py` - Decryption tool with auto-detection
- `cleanroom_zd.py` - Optimized ZD decrypter

## Extraction Verification

✅ Decryption verified with sample PCK
✅ JPEG extraction working (SOI/EOI markers detected)
✅ MP3 extraction working (frame sync detection)
✅ WEBP extraction working (RIFF/WEBP signatures detected)
