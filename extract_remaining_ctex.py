#!/usr/bin/env python3
"""
Extract remaining .ctex files from ZD.pck
Uses the known paths from extracted_files/.godot/imported/ to identify files to extract
"""

import struct
import os
from pathlib import Path


def extract_remaining_ctex(pck_path: str, known_dir: str, output_dir: str):
    """Extract .ctex files that are in PCK but not yet extracted"""
    
    # First, get the list of already extracted files
    extracted_dir = Path(known_dir)
    extracted_ctex = set(f.name for f in extracted_dir.glob('*.ctex'))
    print(f"Found {len(extracted_ctex)} already extracted .ctex files")
    
    # Get file count from PCK
    with open(pck_path, 'rb') as f:
        data = f.read()
    
    gst2_header = data[0x70:0x90]
    entry_count = struct.unpack('<I', gst2_header[8:12])[0]
    data_offset = struct.unpack('<I', gst2_header[12:16])[0]
    
    print(f"PCK entry count: {entry_count}")
    print(f"Data offset: {data_offset:#x}")
    
    # Decrypt file entries
    encrypted = data[0x80:0x80+100000]  # First 100KB of entries
    decrypted = bytearray(len(encrypted))
    gst2_key = gst2_header
    
    for i in range(len(decrypted)):
        decrypted[i] = encrypted[i] ^ gst2_key[i % 16]
    
    # Find entries with .ctex paths
    entries = []
    offset = 0
    entry_num = 0
    
    while offset + 4 < len(decrypted) and entry_num < entry_count:
        name_len = struct.unpack('<I', decrypted[offset:offset+4])[0]
        
        if name_len < 50 or name_len > 300:  # Reasonable path length
            offset += 4
            continue
        
        name_start = offset + 4
        name_end = name_start + name_len
        
        if name_end > len(decrypted):
            break
        
        name = bytes(decrypted[name_start:name_end]).rstrip(b'\x00')
        
        if b'.ctex' in name:
            # Entry ends at: name_start + name_len + 32 (padding) + 8 (offset + size)
            entry_end = name_end + 32 + 8
            
            file_offset = struct.unpack('<I', decrypted[name_end:name_end+4])[0]
            file_size = struct.unpack('<I', decrypted[name_end+4:name_end+8])[0]
            
            # Calculate actual file position in PCK
            actual_offset = data_offset + file_offset
            
            path_str = name.decode('utf-8', errors='replace')
            
            # Check if this file was already extracted
            filename = path_str.split('/')[-1]
            
            if filename not in extracted_ctex:
                entries.append({
                    'path': path_str,
                    'filename': filename,
                    'offset': actual_offset,
                    'size': file_size
                })
                
                if len(entries) >= 100:  # Limit for quick test
                    break
        
        offset = entry_end
        entry_num += 1
    
    print(f"Found {len(entries)} remaining .ctex files to extract")
    
    # Extract
    os.makedirs(output_dir, exist_ok=True)
    
    extracted = 0
    for entry in entries:
        try:
            with open(pck_path, 'rb') as f:
                f.seek(entry['offset'])
                file_data = f.read(entry['size'])
            
            output_path = os.path.join(output_dir, entry['filename'])
            
            with open(output_path, 'wb') as f:
                f.write(file_data)
            
            extracted += 1
            
            if extracted % 10 == 0:
                print(f"Extracted: {extracted}/{len(entries)}")
                
        except Exception as e:
            print(f"  Failed: {entry['filename']}: {e}")
    
    print(f"\nExtracted: {extracted}/{len(entries)}")


def main():
    pck_path = r"C:\Users\red\Desktop\code\decode\ZD.pck"
    known_dir = r"C:\Users\red\Desktop\code\decode\extracted_files\.godot\imported"
    output_dir = r"C:\Users\red\Desktop\code\decode\remaining_ctex"
    
    extract_remaining_ctex(pck_path, known_dir, output_dir)


if __name__ == "__main__":
    main()