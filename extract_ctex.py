#!/usr/bin/env python3
"""
Extract textures from Godot .ctex files (GST2 format)
Handles metadata .ctex files and texture .ctex files with embedded data
"""

import os
import struct
from pathlib import Path


def find_and_extract_texture(data: bytes, output_dir: str) -> tuple[str, int]:
    """
    Find and extract texture data from .ctex file
    Returns (output_path, extracted_size) or (None, 0) if not found
    """
    # Find GST2 header
    gst2_pos = data.find(b'GST2')
    if gst2_pos == -1:
        return None, 0
    
    # Parse GST2 header
    version = struct.unpack('<I', data[gst2_pos+4:gst2_pos+8])[0]
    width = struct.unpack('<I', data[gst2_pos+8:gst2_pos+12])[0]
    height = struct.unpack('<I', data[gst2_pos+12:gst2_pos+16])[0]
    
    print(f"  GST2: {width}x{height}, version {version}")
    
    # Data after GST2 header is the image data
    image_start = gst2_pos + 16
    
    # Try to find RIFF/WEBP signature after GST2
    riff_pos = data.find(b'RIFF', image_start)
    
    if riff_pos != -1:
        # WEBP format
        # Find the end of RIFF chunk
        if riff_pos + 8 < len(data):
            riff_size = struct.unpack('<I', data[riff_pos+4:riff_pos+8])[0]
            webp_end = riff_pos + 8 + riff_size
            webp_data = data[riff_pos:webp_end]
            
            output_name = f"texture_{width}x{height}_{riff_pos:08x}.webp"
            output_path = os.path.join(output_dir, output_name)
            
            with open(output_path, 'wb') as f:
                f.write(webp_data)
            
            return output_path, len(webp_data)
    
    # Check for JPEG
    jpeg_pos = data.find(b'\xff\xd8', image_start)
    if jpeg_pos != -1:
        # Find EOI
        eoi_pos = data.find(b'\xff\xd9', jpeg_pos)
        if eoi_pos != -1:
            eoi_pos += 2
            jpeg_data = data[jpeg_pos:eoi_pos]
            
            output_name = f"texture_{width}x{height}_{jpeg_pos:08x}.jpg"
            output_path = os.path.join(output_dir, output_name)
            
            with open(output_path, 'wb') as f:
                f.write(jpeg_data)
            
            return output_path, len(jpeg_data)
    
    # Try using the GST2 header itself as key for XOR decryption
    # and see if we get RIFF/WEBP
    gst2_key = data[gst2_pos:gst2_pos+16]
    
    # Decrypt the data after GST2 header
    decrypted = bytearray(len(data) - image_start)
    for i in range(len(decrypted)):
        decrypted[i] = data[image_start + i] ^ gst2_key[i % 16]
    
    # Check for RIFF in decrypted data
    if bytes(decrypted).startswith(b'RIFF') and b'WEBP' in bytes(decrypted)[:20]:
        output_name = f"texture_{width}x{height}_decrypted.webp"
        output_path = os.path.join(output_dir, output_name)
        
        with open(output_path, 'wb') as f:
            f.write(bytes(decrypted))
        
        return output_path, len(bytes(decrypted))
    
    # Check for PNG in decrypted data
    if bytes(decrypted).startswith(b'\x89PNG'):
        output_name = f"texture_{width}x{height}_decrypted.png"
        output_path = os.path.join(output_dir, output_name)
        
        with open(output_path, 'wb') as f:
            f.write(bytes(decrypted))
        
        return output_path, len(bytes(decrypted))
    
    # Check if decrypted data contains JPEG
    jpeg_start = bytes(decrypted).find(b'\xff\xd8')
    if jpeg_start != -1:
        eoi = bytes(decrypted).find(b'\xff\xd9', jpeg_start)
        if eoi != -1:
            eoi += 2
            jpeg_data = bytes(decrypted)[jpeg_start:eoi]
            
            output_name = f"texture_{width}x{height}_decrypted.jpg"
            output_path = os.path.join(output_dir, output_name)
            
            with open(output_path, 'wb') as f:
                f.write(jpeg_data)
            
            return output_path, len(jpeg_data)
    
    return None, 0


def extract_ctex(filepath: str, output_dir: str):
    """Extract .ctex file to WEBP/JPEG format"""
    try:
        with open(filepath, 'rb') as f:
            data = f.read()
        
        # Try to extract texture
        output_path, size = find_and_extract_texture(data, output_dir)
        
        if output_path:
            print(f"  -> Extracted texture: {output_path} ({size:,} bytes)")
            return output_path
        else:
            # Check if it's just a metadata file
            if b'res://' in data and b'metadata=' in data:
                print(f"  -> Metadata file only (no embedded texture data)")
                return None
            else:
                print(f"  -> No texture data found")
                print(f"     First 100 bytes: {data[:100].hex()}")
                return None
    
    except Exception as e:
        print(f"  Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    extracted_dir = r"<decode_directory>\extracted_files\.godot\imported"
    textures_dir = r"<decode_directory>\extracted_assets\textures"
    
    # Create output directory
    os.makedirs(textures_dir, exist_ok=True)
    
    # Find all .ctex files
    ctex_files = list(Path(extracted_dir).glob("**/*.ctex"))
    
    print(f"Found {len(ctex_files)} .ctex files")
    
    extracted_count = 0
    skipped_count = 0
    
    for ctex_file in ctex_files:
        print(f"\nProcessing: {ctex_file.name}")
        result = extract_ctex(str(ctex_file), textures_dir)
        
        if result:
            extracted_count += 1
        else:
            skipped_count += 1
    
    print(f"\n\nComplete:")
    print(f"  Extracted: {extracted_count}")
    print(f"  Skipped (metadata only): {skipped_count}")


if __name__ == "__main__":
    main()