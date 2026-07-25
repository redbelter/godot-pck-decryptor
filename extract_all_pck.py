#!/usr/bin/env python3
"""
Extract all files from ZD.pck - full PCK unpacker
"""

import struct
import os
from pathlib import Path


def extract_all_from_pck(pck_path: str, output_dir: str):
    """Extract all files from ZD.pck"""
    with open(pck_path, 'rb') as f:
        data = f.read()
    
    if len(data) < 128:
        print("Error: File too small")
        return
    
    # Get GST2 header info
    gst2_header = data[0x70:0x90]
    gst2_key = gst2_header
    entry_count = struct.unpack('<I', gst2_header[8:12])[0]
    data_offset = struct.unpack('<I', gst2_header[12:16])[0]
    
    print(f"GST2 Key: {gst2_key.hex()}")
    print(f"Entry count: {entry_count}")
    print(f"Data offset: {data_offset:#x}")
    
    # Decrypt file entries at 0x80
    encrypted_start = 0x80
    encrypted_data = data[encrypted_start:]
    
    # Full decryption
    decrypted = bytearray(len(encrypted_data))
    for i in range(len(decrypted)):
        decrypted[i] = encrypted_data[i] ^ gst2_key[i % 16]
    
    # Parse entries
    # GST2 entry format: name_len(4) + name + 32_padding + offset(4) + size(4) + 20_padding
    # Total per entry: 60 + name_len bytes
    
    entries = []
    offset = 0
    entry_num = 0
    
    while offset + 4 < len(decrypted) and entry_num < entry_count:
        name_len = struct.unpack('<I', decrypted[offset:offset+4])[0]
        
        if name_len < 10 or name_len > 200:  # Invalid name length
            offset += 4
            continue
        
        # Valid entry
        name_start = offset + 4
        name = bytes(decrypted[name_start:name_start+name_len]).rstrip(b'\x00')
        
        if name.startswith(b'res://'):
            entry_end = name_start + name_len + 32 + 4 + 4 + 20
            file_offset = struct.unpack('<I', decrypted[name_start+name_len+32:offset+name_len+32+4])[0]
            file_size = struct.unpack('<I', decrypted[name_start+name_len+32+4:offset+name_len+32+8])[0]
            
            # Actual file position in PCK
            actual_offset = data_offset + file_offset
            
            entries.append({
                'path': name.decode('utf-8', errors='replace'),
                'offset': actual_offset,
                'size': file_size
            })
            
            offset = entry_end
            entry_num += 1
        else:
            offset += 4
    
    print(f"Found {len(entries)} valid entries")
    
    # Extract files
    os.makedirs(output_dir, exist_ok=True)
    
    extracted = 0
    failed = 0
    
    for entry in entries:
        try:
            with open(pck_path, 'rb') as f:
                f.seek(entry['offset'])
                file_data = f.read(entry['size'])
            
            # Determine file extension from path
            path_parts = entry['path'].split('/')
            filename = path_parts[-1]
            
            output_path = os.path.join(output_dir, filename)
            
            with open(output_path, 'wb') as f:
                f.write(file_data)
            
            extracted += 1
            
            if extracted % 100 == 0:
                print(f"Extracted: {extracted}/{len(entries)}")
                
        except Exception as e:
            print(f"  Failed: {entry['path']}: {e}")
            failed += 1
    
    print(f"\nExtracted: {extracted}/{len(entries)}")
    print(f"Failed: {failed}")


def main():
    pck_path = r"C:\Users\red\Desktop\code\decode\ZD.pck"
    output_dir = r"C:\Users\red\Desktop\code\decode\all_extracted"
    
    extract_all_from_pck(pck_path, output_dir)


if __name__ == "__main__":
    main()