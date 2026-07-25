#!/usr/bin/env python3
"""
Extract audio from .mp3str files
"""

import os
from pathlib import Path

def extract_mp3str(filepath: str, output_dir: str):
    """Extract MP3 data from .mp3str file"""
    try:
        with open(filepath, 'rb') as f:
            data = f.read()
        
        print(f"File: {os.path.basename(filepath)}")
        print(f"  Size: {len(data)} bytes")
        
        # .mp3str files might already contain MP3 data or have a header
        # Check for MP3 signature
        if data[:2] == b'\xFF\xF3' or data[:2] == b'\xFF\xF2' or data[:2] == b'\xFF\xF1' or data[:2] == b'\xFF\xFA':
            print(f"  Found MP3 signature at start")
            # Save as MP3
            base_name = Path(filepath).stem.replace('.mp3str', '')
            output_name = base_name + '.mp3'
            output_path = os.path.join(output_dir, output_name)
            
            with open(output_path, 'wb') as f:
                f.write(data)
            
            print(f"  Extracted {len(data)} bytes to {output_name}")
            return output_path
        else:
            # Look for MP3 signature in the file
            for i in range(len(data) - 2):
                if data[i:i+1] == b'\xFF' and (data[i+1] & 0xE0) == 0xE0:
                    print(f"  Found MP3 signature at offset 0x{i:04x}")
                    mp3_data = data[i:]
                    base_name = Path(filepath).stem.replace('.mp3str', '')
                    output_name = base_name + '.mp3'
                    output_path = os.path.join(output_dir, output_name)
                    
                    with open(output_path, 'wb') as f:
                        f.write(mp3_data)
                    
                    print(f"  Extracted {len(mp3_data)} bytes to {output_name}")
                    return output_path
        
        print(f"  No MP3 data found")
        return None
        
    except Exception as e:
        print(f"  Error: {e}")
        return None

def main():
    extracted_dir = r"<decode_directory>\extracted_files\.godot\imported"
    output_dir = r"<decode_directory>\extracted_assets\audio"
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Find all .mp3str files
    mp3str_files = list(Path(extracted_dir).glob("*.mp3str"))
    
    print(f"Found {len(mp3str_files)} .mp3str files")
    
    # Process all of them
    success = 0
    fail = 0
    
    for mp3str_file in mp3str_files:
        result = extract_mp3str(str(mp3str_file), output_dir)
        if result:
            success += 1
        else:
            fail += 1
    
    print(f"\nExtraction complete:")
    print(f"  Success: {success}")
    print(f"  Failed: {fail}")

if __name__ == "__main__":
    main()