# PCK Encryption Comparison

## Standard Godot PCK

| Feature | Value |
|---------|-------|
| Algorithm | AES-256-CFB |
| Key Length | 256 bits (32 bytes) |
| Key Storage | In executable template |
| IV | 128 bits |
| Difficulty | Medium (requires unpacking executable) |

## ZD GST2 PCK

| Feature | Value |
|---------|-------|
| Algorithm | XOR (16-byte repeating key) |
| Key Length | 128 bits (16 bytes) |
| Key Storage | Embedded in PCK file (GST2 header) |
| IV | N/A |
| Difficulty | Low (key in file, no unpacking needed) |

## Why GST2 is Different

ZD.pck uses GST2 format because:
- **Simplicity** - No need to embed key in executable
- **Speed** - XOR is faster than AES
- **Compatibility** - Works with modified Godot engine

However, GST2 is **less secure**:
- Key is exposed in the PCK file
- XOR can be broken with known plaintext
- No authentication to detect tampering

## Recommendation

Use standard Godot PCK with AES for production games.
GST2 format is suitable for rapid prototyping or internal tools.
