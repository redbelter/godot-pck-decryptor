# Zombie Diary Asset Extraction Knowledge Status

**Date:** Saturday, July 25, 2026
**Working Directory:** `<decode_directory>`

## Project Overview

This project extracts assets from the Zombie Diary game's PCK archive (ZD.pck) which uses XOR encryption with a GST2 header pattern.

## Extraction Results

### Assets Successfully Extracted

| Format | Count | Description |
|--------|-------|-------------|
| WEBP (.webp) | 410 | Web Picture Format - compressed textures |
| JPEG (.jpg) | 111 | Joint Photographic Experts Group - compressed textures |
| MP3 (.mp3) | 46 | Audio files (streaming audio) |
| **Total** | **567** | Successfully extracted to readable formats |

### Remaining Files

| Format | Count | Description |
|--------|-------|-------------|
| .ctex | 58 | Files requiring additional analysis |

## File Format Analysis

### .ctex Texture Files
- **Format:** Godot Engine resource files with GST2 header
- **Encryption:** Uses GST2 header as XOR key pattern
- **Detected formats after extraction:**
  - WEBP (Web Picture Format) - RIFF/VP8L format
  - JPEG (Joint Photographic Experts Group)

### Audio Files
- **.sample files:** Godot sample resource metadata (not raw audio)
- **.mp3str files:** Contains actual MP3 audio data after a small header

### Extraction Methods

1. **WEBP Extraction:**
   - Files contain RIFF header with "WEBPVP8L" signature
   - Extract from RIFF offset to end of file
   - 410 files successfully extracted

2. **JPEG Extraction:**
   - Files contain SOI (0xFFD8) and EOI (0xFFD9) markers
   - Extract from SOI to EOI
   - 111 files successfully extracted

3. **MP3 Extraction:**
   - .mp3str files contain MP3 data after small header
   - MP3 signature at offset 0x89-0xA9
   - 46 files successfully extracted

## Remaining Files Analysis

The 58 remaining .ctex files do not contain standard WEBP or JPEG signatures in the expected locations. These files:
- Have GST2 header pattern
- Contain compressed/encoded data that doesn't match standard image formats
- May use:
  - Different compression method
  - Custom encoding
  - Raw pixel data format

## Output Files

### Extracted Assets Directory
`<decode_directory>\extracted_assets\`

- **textures/**: 410 .webp + 111 .jpg files
- **audio/**: 46 .mp3 files
- **raw_data/**: Unprocessed data for further analysis

### Report Files
- `DISCORD_REPORT.txt`: Summary for Discord
- `extracted_assets_index.txt`: File listing
- `extracted_assets_report.json`: Detailed JSON report
- `EXTRACTION_SUMMARY.txt`: Human-readable summary

## Next Steps

1. **Analyze remaining 58 .ctex files:**
   - Determine compression format
   - Identify header structure
   - Develop extraction method

2. **Verify extracted files:**
   - Open WEBP files in image viewers
   - Play MP3 files in audio players
   - Confirm no corruption during extraction

3. **Documentation:**
   - Create asset map for game development
   - Catalog all character, item, and background assets

## Technical Notes

### GST2 Header Structure
```
Offset 0x70-0x7F: GST2 magic + size info
Offset 0x80-0x8F: Encryption header
Offset 0x90+: Image data (varies by file type)
```

### XOR Key Pattern
- GST2 header bytes are used for XOR encryption
- Key size: 16 bytes
- Data is XOR'd with repeating key pattern

## Files Created

- `extract_ctex.py`: Texture extraction tool
- `extract_jpeg.py`: JPEG extraction tool
- `extract_mp3str.py`: MP3 extraction tool
- `create_report.py`: Report generation tool
- `create_discord_report.py`: Discord-friendly report

## Contact/Notes

Project status: **ACTIVE** - Most assets extracted successfully. Remaining files require additional analysis.