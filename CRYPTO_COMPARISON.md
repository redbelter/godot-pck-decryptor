# Godot PCK vs Zombie Diary PCK Crypto Comparison

## Standard Godot PCK Encryption

### Method
- **Algorithm:** AES-256-CFB (Cipher Feedback mode)
- **Key:** 256-bit (32-byte) AES key
- **IV:** 128-bit (16-byte) Initialization Vector
- **Storage:** Key and IV are embedded in the game executable (export template)
- **Configuration:** Set at export time via `--encryption-key` flag

### Structure
```
Offset 0x0:   GDPC magic (0x47445043)
Offset 0x4:   Version (4 bytes)
Offset 0x8:   Flags/unknown (4 bytes)
Offset 0x10:  File count (4 bytes)
Offset 0x50:  File index entries begin (after 64-byte padding)
  - Each entry: name_len + name + padding + offset + size + padding
Offset XXX:   Encrypted file data
```

### Key Storage
- AES key stored in executable template at build time
- 64 hex characters (32 bytes) specified during export
- Key + IV used to encrypt entire PCK content

### Security Assessment
| Aspect | Assessment |
|--------|------------|
| **Attack Vectors** | - Key extraction from executable memory<br>- Memory dump during runtime<br>- Debugging (x64dbg, WinDbg) |
| **Crack Difficulty** | Medium - Requires extracting key from protected executable |
| **Key Length** | 256 bits (strong) |
| **Mode** | CFB - allows streaming decryption |
| **Defense** | Requires unpacking MPRESS/other packers first |

---

## Zombie Diary GST2 PCK Encryption

### Method
- **Algorithm:** XOR with repeating 16-byte key
- **Key:** 16 bytes from GST2 header at offset 0x70
- **IV:** None (XOR doesn't use IV)
- **Storage:** Key embedded in PCK file itself (GST2 header)
- **Configuration:** Auto-detected by GST2 header

### Structure
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
Offset 0x80:  File entries (encrypted)
Offset 0x2d0: Encrypted content
```

### Key Storage
- Key stored IN the PCK file itself at offset 0x70
- GST2 header contains: `GST2\x01\x00\x00\x00\x00\x05\x00\x00\xd0\x02\x00\x00`
- No external configuration needed

### Security Assessment
| Aspect | Assessment |
|--------|------------|
| **Attack Vectors** | - Direct XOR analysis<br>- Known plaintext attack<br>- Pattern recognition |
| **Crack Difficulty** | Low - Key is in the file itself |
| **Key Length** | 128 bits (16 bytes) - weaker than 256-bit |
| **Mode** | Simple repeating XOR - vulnerable to pattern analysis |
| **Defense** | None - key is obvious once format is known |

---

## Crypto Comparison Summary

| Feature | Standard Godot PCK | Zombie Diary PCK |
|---------|-------------------|------------------|
| **Algorithm** | AES-256-CFB | XOR (16-byte key) |
| **Key Length** | 256 bits | 128 bits |
| **Key Storage** | In executable (protected) | IN PCK file (exposed) |
| **IV** | 128 bits | N/A |
| **Difficulty to Crack** | Medium | Low |
| **Defensive Strength** | Strong | Very Weak |
| **Purpose** | Anti-tampering | Obfuscation |

---

## Why Zombie Diary's Approach is Weaker

1. **Key is in the file** - Anyone can read the key with a hex editor
2. **XOR is reversible** - Known plaintext reveals the key
3. **16-byte key** - Only 128 bits vs 256 bits AES
4. **No authentication** - No checksum/MAC to detect tampering

## Why Standard Godot PCK is Stronger

1. **AES-256** - Industry-standard, 256-bit security
2. **CFB mode** - Resistant to certain attacks
3. **Key in executable** - Requires unpacking to extract
4. **IV adds randomness** - Same plaintext produces different ciphertext

## Conclusion

**Standard Godot PCK encryption is significantly stronger** than Zombie Diary's GST2 XOR approach. The ZD format appears to be designed for:
- Obfuscation (hiding assets from casual viewers)
- Lightweight protection (fast decryption at runtime)
- Game engine compatibility (not security-focused)

The GST2 format sacrifices security for simplicity and speed, while standard Godot PCK uses proper encryption designed for anti-tampering protection.