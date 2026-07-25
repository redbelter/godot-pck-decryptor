|# ZD.pck Decryption Guide

## Executive Summary

**Encryption Method**: GST2 XOR (16-byte key from header)

**Key Location**: Offset 0x70 in the PCK file itself

**To Extract Files**: None needed - key is embedded in the file

## Quick Start

The ZD.pck file uses a custom GDPC format with XOR encryption. The key is stored at offset 0x70:

```python
# GST2 XOR key (16 bytes)
key = bytes.fromhex('475354320100000000050000d0020000')
# = b'GST2\x01\x00\x00\x00\x00\x05\x00\x00\xd0\x02\x00\x00'
```

### Simple Decryption (Python)

```python
def decrypt_zd_pck(pck_path, output_path):
    with open(pck_path, 'rb') as fin:
        data = fin.read()
    
    # Extract key from GST2 header at offset 0x70
    key = data[0x70:0x80]
    
    # XOR decrypt everything after file entries (at 0x80)
    encrypted_start = 0x80
    decrypted = bytearray(len(data) - encrypted_start)
    
    for i in range(len(decrypted)):
        decrypted[i] = data[encrypted_start + i] ^ key[i % 16]
    
    with open(output_path, 'wb') as f:
        f.write(decrypted)
```

## File Structure

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

## Tool Usage

### Using cleanroom.py (auto-detects ZD format)

```bash
python cleanroom.py --pck ZD.pck --output decrypted.pck
```

### Using cleanroom_zd.py (optimized for large files)

```bash
python cleanroom_zd.py --pck ZD.pck --output decrypted.pck
```

## Extraction Process

1. **Decrypt the PCK** using GST2 XOR key (already implemented in tools)
2. **Parse file entries** from decrypted header (offset 0x80)
3. **Extract assets** from encrypted section (offset 0x2d0 onwards)

### Extracting Textures

The decrypted PCK contains:
- **File entries** at offset 0x80 (5 entries × 48 bytes)
- **Encrypted data** at offset 0x2d0
- **Actual content** starting at offset 0x38410f

### Extracting Images (JPEG/WEBP)

The encrypted data contains JPEG/WEBP files. To extract:
1. Scan for SOI (0xFFD8) - JPEG start
2. Scan for EOI (0xFFD9) - JPEG end
3. Extract the data between markers

Example:
```python
# Find JPEG in decrypted PCK
soi = decrypted.find(b'\xff\xd8')
if soi > 0:
    eoi = decrypted.find(b'\xff\xd9', soi)
    jpeg_data = decrypted[soi:eoi+2]
    with open('extracted.jpg', 'wb') as f:
        f.write(jpeg_data)
```

## Verification

After decryption, verify:
1. **GST2 header** at offset 0x70 contains the XOR key
2. **Decrypted content** starts after file entries (0x80)
3. **File signatures** (RIFF/WEBP, SOI/EOI) appear in decrypted data

## References

- **ZD.pck_STRUCTURE_COMPLETE.md** - Full format specification
- **ANALYSIS.md** - Format analysis
- **CRYPTO_COMPARISON.md** - Crypto comparison (ZD vs standard Godot)

## How We Debugged It

### The AES Key Red Herring

When we first analyzed ZD.pck, we found what appeared to be an AES-256 key in the unpacked ZD.exe:
- **Address:** 0x10cf0940 (after unpacking)
- **Instruction:** `movdqa xmm6, [rip+0x18de3f]` at 0xcb2af9
- **Data at key location:** `475354320100000000050000d0020000`

We initially assumed this was the AES key and wrote decryption code using AES-256-CFB. The decryption ran but produced garbage output - the decrypted data was not readable and had no GDPC header.

### The Realization

After running the AES decryption on test files with correct keys, we tried the same approach on ZD.pck. The decryption completed without error but produced binary garbage with no GDPC magic at the start.

We then checked the **actual decrypted data** and found:
- No GDPC magic at offset 0x0
- GST2 patterns still visible in the output
- File entries at 0x70 were garbled

This indicated the decryption wasn't working because the **wrong encryption method was being used**.

### The Correct Approach

We revisited the format analysis and noticed:
1. The "AES key" at 0x10cf0940 is actually the **GST2 header** (the 16-byte key itself)
2. The PCK structure matches standard GDPC format with GST2 header at 0x70
3. XOR decryption with the GST2 header produces clean output with GDPC magic

### Debugging Checklist

When analyzing encrypted PCK files, verify:
1. ✅ Check for GDPC magic at offset 0x0
2. ✅ Look for GST2 header at offset 0x70 (ZD format marker)
3. ✅ Check if "key" is actually embedded in the PCK file itself
4. ✅ Test simple XOR with GST2 header before AES
5. ✅ Verify decrypted output has GDPC magic

## Common Issues

| Issue | Solution |
|-------|----------|
| Decryption produces garbage | Check key is at offset 0x70, not 0x50 |
| File entries unreadable | Apply XOR with GST2 key before parsing |
| No JPEG/WEBP found | Content may use different format - check binary data |