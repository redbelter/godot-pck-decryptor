#!/usr/bin/env python3
"""
Extract textures from ZD.pck using GST2 decryption
"""

import struct
import os
import sys
from pathlib import Path


def extract_zd_pck(pck_path: str, output_dir: str):
    """Extract all assets from ZD.pck"""
    with open(pck_path, 'rb') as f:
        data = f.read()
    
    if len(data) < 128:
        print("Error: File too small")
        return
    
    # Get GST2 key from header at 0x70
    gst2_key = data[0x70:0x90]
    print(f"GST2 key: {gst2_key.hex()}")
    
    # File count from GDPC header at 0x10
    file_count = struct.unpack('<I', data[0x10:0x14])[0]
    print(f"File count: {file_count}")
    
    # Data offset from GST2 header at 0x7C
    data_offset = struct.unpack('<I', data[0x7C:0x80])[0]
    print(f"Data offset: {data_offset:#x}")
    
    # Parse file entries from 0x80
    # The entries at 0x80 are encrypted with GST2 key
    # When XORed with GST2 key, they reveal the actual entry data
    
    entry_start = 0x80
    
    # Decrypt the file entries section to find actual data offsets
    # Each entry should have: name_offset, name_len, data_offset, data_len
    # Let's find where 'res://' paths are after XOR decryption
    
    # Try decrypting and parsing
    decrypted_data = bytearray(len(data))
    for i in range(len(data)):
        decrypted_data[i] = data[i] ^ gst2_key[i % 16]
    
    # Find res:// paths in decrypted data (starting from data_offset)
    print(f"\nSearching for file data after data_offset...")
    
    # The data starts at data_offset (0x2d0)
    # But data_offset is relative to the start of the file
    # So actual data starts at: data_offset = 0x2d0
    
    file_data_start = data_offset
    file_data = decrypted_data[file_data_start:]
    
    # Search for 'res://' in decrypted file data
    res_pos = file_data.find(b'res://')
    if res_pos != -1:
        print(f"Found 'res://' at decrypted offset: 0x{res_pos:x}")
        # Find end of path (null byte or quote)
        end_pos = file_data.find(b'\"', res_pos)
        if end_pos != -1:
            path = file_data[res_pos:end_pos].decode('utf-8', errors='replace')
            print(f"Path: {path}")
    
    # Search for .ctex files
    ctex_pos = file_data.find(b'.ctex')
    if ctex_pos != -1:
        print(f"\nFound '.ctex' at decrypted offset: 0x{ctex_pos:x}")
        start = max(0, ctex_pos - 50)
        end = min(len(file_data), ctex_pos + 50)
        print(f"Context: {file_data[start:end].hex()}")
        print(f"Context ASCII: {file_data[start:end]}")
    
    # Look for GST2 patterns in decrypted data (self-referential)
    print(f"\nSearching for GST2 patterns in decrypted data...")
    gst2_pattern_count = 0
    for i in range(0, len(file_data) - 4, 16):
        if file_data[i:i+4] == b'GST2':
            gst2_pattern_count += 1
    
    print(f"Found {gst2_pattern_count} GST2 patterns in file data")


def main():
    pck_path = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\red\Desktop\code\decode\ZD.pck"
    output_dir = sys.argv[2] if len(sys.argv) > 2 else r"C:\Users\red\Desktop\code\decode\extracted"
    
    os.makedirs(output_dir, exist_ok=True)
    print(f"PCK file: {pck_path}")
    print(f"Output dir: {output_dir}")
    print()
    
    extract_zd_pck(pck_path, output_dir)


if __name__ == "__main__":
    main()