#!/usr/bin/env python3
"""
Cleanroom - Combined Godot/ZD PCK Decrypter

A standalone tool to decrypt both standard Godot PCK files (AES-256-CFB)
and ZD-style PCK files (GST2 XOR encryption).

Usage:
    Standard Godot PCK with AES:
      python cleanroom.py --pck game.pck --key a1b2c3d4...
      python cleanroom.py --pck game.pck --key-file key.txt --output output.pck

    ZD files (auto-detected, no key needed):
      python cleanroom.py --pck ZD.pck
      python cleanroom.py --pck ZD.pck --output output.pck
"""

import argparse
import sys
import os
from pathlib import Path

try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend
except ImportError:
    print("Error: cryptography library not installed. Run: pip install cryptography")
    sys.exit(1)


def md5(data: bytes) -> bytes:
    """Compute MD5 hash of data"""
    import hashlib
    return hashlib.md5(data).digest()


def detect_zd_format(pck_path: str) -> bool:
    """Check if PCK uses ZD-style GST2 XOR encryption"""
    try:
        with open(pck_path, 'rb') as f:
            header = f.read(20)
        return (len(header) >= 20 and 
                header[:4] == b'GDPC' and 
                header[12:16] == b'\x06\x00\x00\x00')
    except:
        return False


def get_zd_key(pck_path: str) -> bytes:
    """Extract GST2 key from ZD PCK file"""
    with open(pck_path, 'rb') as f:
        f.seek(0x70)
        return f.read(16)


def decrypt_zd_pck(pck_path: str, output_path: str = None, 
                   chunk_size: int = 1024*1024) -> bool:
    """
    Decrypt ZD-style PCK files using GST2 XOR encryption.
    
    Efficiently streams the file to avoid loading entire 1GB+ files into memory.
    """
    print("[*] Detected ZD-style format (GST2 XOR encryption)")
    
    # Get GST2 key
    gst2_key = get_zd_key(pck_path)
    gst2_hex = gst2_key.hex()
    print(f"[*] GST2 key (hex): {gst2_hex}")
    
    # Parse ZD header
    with open(pck_path, 'rb') as f:
        header = f.read(0x80)
        
    if len(header) < 0x80:
        print(f"Error: File too small for ZD format")
        return False
    
    gdpc_magic = header[0x00:0x04]
    version = int.from_bytes(header[0x04:0x08], 'little')
    file_count = int.from_bytes(header[0x10:0x14], 'little')
    section_offset = int.from_bytes(header[0x14:0x18], 'little')
    
    print(f"[*] GDPC magic: {gdpc_magic}")
    print(f"[*] Version: {version}")
    print(f"[*] File count: {file_count}")
    print(f"[*] Section offset: 0x{section_offset:x}")
    
    # Read GST2 section to find actual data offset
    gst2_version = int.from_bytes(header[0x74:0x78], 'little')
    entry_count = int.from_bytes(header[0x78:0x7C], 'little')
    data_offset = int.from_bytes(header[0x7C:0x80], 'little')
    
    print(f"[*] GST2 version: {gst2_version}")
    print(f"[*] Entry count: {entry_count}")
    print(f"[*] Data offset: 0x{data_offset:x}")
    
    # Encrypted data starts after file entries (at 0x80)
    encrypted_start = 0x80
    
    # Get file size
    file_size = Path(pck_path).stat().st_size
    encrypted_size = file_size - encrypted_start
    
    print(f"[*] Encrypted data: {encrypted_size} bytes")
    
    # Write output
    if output_path is None:
        output_path = pck_path.replace('.pck', '_decrypted.pck')
    
    print(f"[*] Writing to: {output_path}")
    
    # Stream XOR decryption in chunks
    key_len = len(gst2_key)
    bytes_decrypted = 0
    
    with open(pck_path, 'rb') as fin:
        with open(output_path, 'wb') as fout:
            fin.seek(encrypted_start)
            
            while True:
                chunk = fin.read(chunk_size)
                if not chunk:
                    break
                
                # XOR decrypt chunk
                decrypted_chunk = bytearray(len(chunk))
                for i in range(len(chunk)):
                    decrypted_chunk[i] = chunk[i] ^ gst2_key[i % key_len]
                fout.write(decrypted_chunk)
                bytes_decrypted += len(chunk)
                
                if bytes_decrypted % (100*1024*1024) == 0:  # Print progress every 100MB
                    print(f"[*] Decrypted {bytes_decrypted / (1024*1024):.1f} MB...")
    
    print(f"[+] Decrypted {bytes_decrypted} bytes")
    print(f"[+] Written to {output_path}")
    return True


def decrypt_pck_aes(pck_path: str, key_hex: str, output_path: str = None) -> bool:
    """
    Decrypt standard Godot PCK files using AES-256-CFB mode.
    
    PCK Format:
        Offset 0:   GDPC magic (4 bytes)
        Offset 4:   MD5 hash (16 bytes) - verification hash
        Offset 20:  Data length (8 bytes, little-endian)
        Offset 28:  IV (16 bytes)
        Offset 44:  Encrypted data (variable, padded to 16-byte boundary)
    """
    key = bytes.fromhex(key_hex)
    
    if len(key) != 32:
        print(f"Error: Key must be 32 bytes (64 hex chars), got {len(key)} bytes")
        return False
    
    # Read encrypted PCK file
    with open(pck_path, 'rb') as f:
        data = f.read()
    
    print(f"[*] Read {len(data)} bytes from {pck_path}")
    
    # Detect file format (check for GDPC magic)
    if len(data) >= 4 and data[:4] == b'GDPC':
        print("[*] Detected GDPC magic header")
        data_offset = 4
    else:
        print("[*] No GDPC magic header found, assuming raw encrypted data")
        data_offset = 0
    
    if len(data) < data_offset + 44:
        print(f"Error: File too small ({len(data)} bytes), expected at least {data_offset + 44}")
        return False
    
    # Parse header
    md5_hash = data[data_offset + 0 : data_offset + 16]   # MD5 hash (16 bytes)
    data_length = int.from_bytes(data[data_offset + 16 : data_offset + 24], 'little')  # Length (8 bytes)
    iv = data[data_offset + 24 : data_offset + 40]       # IV (16 bytes)
    encrypted_data = data[data_offset + 40:]             # Encrypted data
    
    print(f"[*] Data length: {data_length} bytes")
    print(f"[*] IV: {iv.hex()}")
    print(f"[*] Encrypted data: {len(encrypted_data)} bytes")
    
    if len(encrypted_data) < 16:
        print("Error: Encrypted data too small")
        return False
    
    # Validate MD5
    expected_md5 = md5_hash
    print(f"[*] Stored MD5: {expected_md5.hex()}")
    
    # Decrypt using AES-256-CFB
    try:
        cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        decrypted_data = decryptor.update(encrypted_data) + decryptor.finalize()
        
        # Trim to actual data length
        decrypted_data = decrypted_data[:data_length]
        
        # Verify MD5
        actual_md5 = md5(decrypted_data)
        if actual_md5 != expected_md5:
            print(f"[!] MD5 mismatch (this is normal if key is wrong or data is corrupted)")
            print(f"    Expected: {expected_md5.hex()}")
            print(f"    Actual:   {actual_md5.hex()}")
            if output_path is None:
                # Still save the decrypted data even if MD5 fails
                output_path = pck_path.replace('.pck', '_decrypted.pck')
        else:
            print(f"[+] MD5 verified successfully")
        
    except Exception as e:
        print(f"Error during decryption: {e}")
        return False
    
    # Write output
    if output_path is None:
        output_path = pck_path.replace('.pck', '_decrypted.pck')
    
    with open(output_path, 'wb') as f:
        f.write(decrypted_data)
    
    print(f"[+] Written decrypted data to {output_path}")
    return True


def main():
    parser = argparse.ArgumentParser(
        description='Cleanroom - Decrypt Godot PCK files with AES-256-CFB or GST2 XOR',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  Standard Godot PCK with AES:
    python cleanroom.py --pck game.pck --key a1b2c3d4...
    python cleanroom.py --pck game.pck --key-file key.txt --output output.pck

  ZD files (auto-detected, no key needed):
    python cleanroom.py --pck ZD.pck
    python cleanroom.py --pck ZD.pck --output output.pck
    '''
    )
    
    parser.add_argument('--pck', '-p', required=True, 
                        help='Path to encrypted PCK file')
    parser.add_argument('--key', '-k', 
                        help='32-byte AES key in hex format (64 chars)')
    parser.add_argument('--key-file', '-f',
                        help='File containing the AES key (hex format)')
    parser.add_argument('--output', '-o',
                        help='Output file path (default: input_decrypted.pck)')
    
    args = parser.parse_args()
    
    # Get key
    key = None
    if args.key:
        key = args.key.strip()
    elif args.key_file:
        try:
            with open(args.key_file, 'r') as f:
                key = f.read().strip()
        except Exception as e:
            print(f"Error reading key file: {e}")
            sys.exit(1)
    
    # Validate key format if provided
    if key is not None:
        if not all(c in '0123456789abcdefABCDEF' for c in key):
            print("Error: Key must be hexadecimal")
            sys.exit(1)
        
        if len(key) != 64:
            print(f"Error: Key must be 64 hex characters (32 bytes), got {len(key)}")
            sys.exit(1)
    
    # Check input file
    pck_path = Path(args.pck)
    if not pck_path.exists():
        print(f"Error: PCK file not found: {args.pck}")
        sys.exit(1)
    
    # Check for ZD format before requiring key
    is_zd = detect_zd_format(args.pck)
    if is_zd:
        print("[*] Auto-detected ZD-style format")
    
    # Decrypt
    print("=" * 50)
    print("Cleanroom - Godot/ZD PCK Decrypter")
    print("=" * 50)
    print(f"[*] Input PCK: {args.pck}")
    if key:
        print(f"[*] Key: {key[:16]}...{key[-16:]}")
    elif not is_zd:
        print("[!] Warning: No key provided for standard PCK - AES decryption will fail")
    print()
    
    # Decide which decryption method to use
    if is_zd:
        success = decrypt_zd_pck(args.pck, args.output)
    elif key is not None:
        success = decrypt_pck_aes(args.pck, key, args.output)
    else:
        print("Error: Standard PCK requires a key. Use --key or --key-file.")
        sys.exit(1)
    
    if success:
        print()
        print("[SUCCESS] Decryption completed!")
        sys.exit(0)
    else:
        print()
        print("[FAILED] Decryption failed")
        sys.exit(1)


if __name__ == '__main__':
    main()