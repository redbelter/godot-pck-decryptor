#!/usr/bin/env python3
"""
Extract all .ctex files from ZD.pck
Find files in the data section (after data_offset), extract GST2 headers and image data
"""

import struct
import os
from pathlib import Path


def extract_ctex_from_pck(pck_path: str, output_dir: str):
    """Extract all .ctex files from ZD.pck"""
    with open(pck_path, 'rb') as f:
        data = f.read()
    
    # Get GST2 info
    gst2_header = data[0x70:0x90]
    entry_count = struct.unpack('<I', gst2_header[8:12])[0]
    data_offset = struct.unpack('<I', gst2_header[12:16])[0]
    
    print(f"Entry count: {entry_count}")
    print(f"Data offset: {data_offset:#x}")
    
    file_data = data[data_offset:]
    
    # Find all .ctex files in data section
    ctex_files = []
    pos = 0
    while True:
        res_pos = file_data.find(b'res://', pos)
        if res_pos == -1:
            break
        
        ctex_pos = file_data.find(b'.ctex', res_pos)
        if ctex_pos == -1:
            break
        
        # Find start of path (should be right after res://)
        path_end = file_data.find(b'\"', ctex_pos + 5)
        if path_end == -1:
            path_end = ctex_pos + 100
        
        # Find end of metadata (look for null padding before GST2)
        path_str = file_data[res_pos:ctex_pos+5].decode('utf-8', errors='replace')
        
        # Find GST2 header after the path
        # Look for pattern: null padding + GST2 header
        search_start = ctex_pos + 5
        search_end = min(len(file_data), search_start + 1000)
        
        for check_offset in range(search_start, search_end - 32):
            if file_data[check_offset:check_offset+4] == b'GST2':
                gst2_pos = check_offset
                # Check if this is a valid GST2 header
                gst2_bytes = file_data[check_offset:check_offset+16]
                # GST2 magic: 47 53 54 32 (GST2 in ASCII)
                # Version: 01 00 00 00
                if gst2_bytes[0:4] == b'GST2' and gst2_bytes[4] == 1:
                    # Valid GST2 header
                    # Find start of this file (after previous res://)
                    if len(ctex_files) > 0:
                        prev_file_start = ctex_files[-1][1]
                        file_start = prev_file_start + 1  # Start from next byte
                    else:
                        file_start = res_pos
                    
                    # Calculate end of this file (start of next file or end of data)
                    if len(ctex_files) > 0:
                        next_start = len(file_data)  # Default to end
                    else:
                        next_start = len(file_data)
                    
                    # Find the GST2 header position relative to file_start
                    gst2_rel = gst2_pos - file_start
                    
                    ctex_files.append((path_str, file_start, next_start, res_pos, ctex_pos, gst2_rel))
                    break
        
        pos = ctex_pos + 10
    
    print(f"Found {len(ctex_files)} .ctex files")
    
    # Extract files
    os.makedirs(output_dir, exist_ok=True)
    
    extracted = 0
    for i, (path_str, file_start, file_end, res_pos, ctex_pos, gst2_rel) in enumerate(ctex_files):
        if i >= 100:  # Only extract first 100 for testing
            break
        
        filename = path_str.split('/')[-1]
        
        # Extract the GST2 header and image data
        gst2_pos = file_start + gst2_rel
        gst2_data = file_data[gst2_pos:gst2_pos+16]
        
        # Check if data after GST2 is image
        image_start = gst2_pos + 16
        image_end = file_end
        
        # Try to find actual end of image data
        # For WEBP, look for end of RIFF chunk
        # For JPEG, look for EOI marker
        
        # Check for RIFF/WEBP
        if image_start < len(file_data) and file_data[image_start:image_start+4] == b'RIFF':
            riff_size = struct.unpack('<I', file_data[image_start+4:image_start+8])[0]
            actual_end = image_start + 8 + riff_size
            if actual_end <= file_end:
                file_end = actual_end
        
        # Check for JPEG
        elif image_start < len(file_data) and file_data[image_start:image_start+2] == b'\\xff\\xd8':
            # Look for EOI marker
            for j in range(image_start, min(file_end, image_start + 100000)):
                if file_data[j:j+2] == b'\\xff\\xd9':
                    file_end = j + 2
                    break
        
        # Extract file data
        file_data_extract = file_data[file_start:file_end]
        
        output_path = os.path.join(output_dir, filename)
        
        with open(output_path, 'wb') as f:
            f.write(file_data_extract)
        
        extracted += 1
        if i % 10 == 0:
            print(f"Extracted: {extracted}")
    
    print(f"\\nExtracted: {extracted}")


def main():
    pck_path = r"C:\Users\red\Desktop\code\decode\ZD.pck"
    output_dir = r"C:\Users\red\Desktop\code\decode\extracted_from_pck"
    
    extract_ctex_from_pck(pck_path, output_dir)


if __name__ == "__main__":
    main()