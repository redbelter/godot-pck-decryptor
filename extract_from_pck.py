#!/usr/bin/env python3
"""
Extract textures from ZD.pck using file entry offsets
Decodes GST2 format texture data
"""

import struct
import os
import sys
from pathlib import Path


def get_zd_pck_info(pck_path: str):
    """Parse ZD.pck and return entries with file data offsets"""
    with open(pck_path, 'rb') as f:
        data = f.read()
    
    # GST2 header at 0x70
    gst2_key = data[0x70:0x90]
    entry_count = struct.unpack('<I', data[0x78:0x7C])[0]
    data_offset = struct.unpack('<I', data[0x7C:0x80])[0]
    
    print(f"GST2 key: {gst2_key.hex()}")
    print(f"Entry count: {entry_count}")
    print(f"Data offset: {data_offset:#x}")
    
    # Decrypt file entries section
    encrypted_start = 0x80
    decrypted = bytearray(len(data) - encrypted_start)
    
    for i in range(len(decrypted)):
        decrypted[i] = data[encrypted_start + i] ^ gst2_key[i % 16]
    
    # Parse entries
    offset = 0
    entries = []
    for i in range(entry_count):
        name_len = struct.unpack('<I', decrypted[offset:offset+4])[0]
        offset += 4
        path = decrypted[offset:offset+name_len].rstrip(b'\x00').decode('utf-8', errors='replace')
        offset += name_len
        offset += 32  # padding
        file_offset = struct.unpack('<I', decrypted[offset:offset+4])[0]
        offset += 4
        file_size = struct.unpack('<I', decrypted[offset:offset+4])[0]
        offset += 4 + 20  # padding
        
        # Add 0x2d0 (data_offset) to get actual file offset in PCK
        actual_offset = data_offset + file_offset
        
        entries.append({
            'path': path,
            'offset': actual_offset,
            'size': file_size
        })
    
    return entries, data_offset, gst2_key


def extract_texture_from_pck(pck_path: str, entry: dict, output_dir: str):
    """Extract texture from PCK file at entry offset"""
    try:
        with open(pck_path, 'rb') as f:
            f.seek(entry['offset'])
            data = f.read(entry['size'])
        
        # Check if data contains GST2 header
        gst2_pos = data.find(b'GST2')
        if gst2_pos == -1:
            print(f"  No GST2 header in entry, skipping")
            return None
        
        # Parse GST2 header
        width = struct.unpack('<I', data[gst2_pos+8:gst2_pos+12])[0]
        height = struct.unpack('<I', data[gst2_pos+12:gst2_pos+16])[0]
        print(f"  GST2: {width}x{height}")
        
        # Check for RIFF/WEBP after GST2
        riff_pos = data.find(b'RIFF', gst2_pos + 16)
        if riff_pos != -1 and riff_pos > gst2_pos + 16:
            riff_size = struct.unpack('<I', data[riff_pos+4:riff_pos+8])[0]
            webp_data = data[riff_pos:riff_pos+8+riff_size]
            
            output_name = f"texture_{width}x{height}_{entry['path'].split('/')[-1].replace('.ctex', '.webp')}"
            output_path = os.path.join(output_dir, output_name)
            
            with open(output_path, 'wb') as f:
                f.write(webp_data)
            
            return output_path
        
        # Try decrypted data
        gst2_key = data[gst2_pos:gst2_pos+16]
        image_start = gst2_pos + 16
        decrypted = bytearray(len(data) - image_start)
        
        for i in range(len(decrypted)):
            decrypted[i] = data[image_start + i] ^ gst2_key[i % 16]
        
        # Check for RIFF in decrypted
        decrypted_bytes = bytes(decrypted)
        if decrypted_bytes.startswith(b'RIFF') and b'WEBP' in decrypted_bytes[:20]:
            output_name = f"texture_{width}x{height}_decrypted.webp"
            output_path = os.path.join(output_dir, output_name)
            
            with open(output_path, 'wb') as f:
                f.write(decrypted_bytes)
            
            return output_path
        
        return None
        
    except Exception as e:
        print(f"  Error: {e}")
        return None


def main():
    # Get ZD.pck from args or default
    pck_path = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\red\Desktop\code\decode\ZD.pck"
    
    # Parse PCK
    entries, data_offset, gst2_key = get_zd_pck_info(pck_path)
    print(f"Found {len(entries)} entries in PCK\n")
    
    # Output directory
    output_dir = r"C:\Users\red\Desktop\code\decode\extracted_from_pck"
    os.makedirs(output_dir, exist_ok=True)
    
    # Extract .ctex files
    extracted = 0
    for entry in entries:
        if entry['path'].endswith('.ctex'):
            print(f"Processing: {entry['path']}")
            result = extract_texture_from_pck(pck_path, entry, output_dir)
            if result:
                print(f"  -> Extracted: {result}")
                extracted += 1
    
    print(f"\nExtracted {extracted} textures from PCK")


if __name__ == "__main__":
    main()