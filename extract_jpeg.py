#!/usr/bin/env python3
"""
Extract JPEG data from .ctex files that have JPEG markers
"""

import os
import struct
from pathlib import Path

def extract_jpeg(filepath: str, output_dir: str):
    """Extract JPEG data from .ctex file"""
    try:
        with open(filepath, 'rb') as f:
            data = f.read()
        
        # Find GST2 header
        gst2_pos = None
        for offset in range(0x60, 0xA0):
            if data[offset:offset+4] == b'GST2':
                gst2_pos = offset
                break
        
        if gst2_pos is None:
            return None
        
        # Find JPEG SOI marker (0xFFD8)
        search_start = gst2_pos + 16
        jpeg_pos = data.find(b'\xFF\xD8', search_start)
        
        if jpeg_pos == -1:
            return None
        
        # Find JPEG EOI marker (0xFFD9) - look near the end
        search_end = len(data)
        for i in range(search_end - 100, search_end - 20, -1):
            if data[i:i+2] == b'\xFF\xD9':
                jpeg_end = i + 2
                break
        else:
            # Fall back to file end
            jpeg_end = len(data)
        
        # Extract JPEG data
        jpeg_data = data[jpeg_pos:jpeg_end]
        
        if len(jpeg_data) < 100:
            print(f"  JPEG data too small: {len(jpeg_data)} bytes")
            return None
        
        # Create output filename
        base_name = Path(filepath).stem.replace('.ctex', '')
        output_name = base_name + '.jpg'
        output_path = os.path.join(output_dir, output_name)
        
        with open(output_path, 'wb') as f:
            f.write(jpeg_data)
        
        print(f"  Extracted {len(jpeg_data)} bytes to {output_name}")
        return output_path
        
    except Exception as e:
        print(f"  Error: {e}")
        return None

def main():
    extracted_dir = r"<decode_directory>\extracted_files\.godot\imported"
    output_dir = r"<decode_directory>\extracted_assets\textures"
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Find all .ctex files that have GST2 but no RIFF
    ctex_files = list(Path(extracted_dir).glob("*.ctex"))
    
    # Filter for files with GST2 but without RIFF
    filtered_files = []
    for ctex_file in ctex_files:
        with open(ctex_file, 'rb') as f:
            data = f.read()
        gst2_pos = data.find(b'GST2')
        riff_pos = data.find(b'RIFF')
        if gst2_pos != -1 and riff_pos == -1:
            filtered_files.append(str(ctex_file))
    
    print(f"Found {len(filtered_files)} files with GST2 but no RIFF")
    
    # Process all of them
    success = 0
    fail = 0
    
    for fpath in filtered_files:
        result = extract_jpeg(fpath, output_dir)
        if result:
            success += 1
        else:
            fail += 1
    
    print(f"\nExtraction complete:")
    print(f"  Success: {success}")
    print(f"  Failed: {fail}")

if __name__ == "__main__":
    main()