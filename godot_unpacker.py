#!/usr/bin/env python3
"""
Godot PCK Unpacker - Unified Tool

Supports:
- Standard Godot PCK (GDPC, AES-256-CFB)
- Zombie Diary GST2 XOR format
- Automatic format detection
- Full asset extraction and conversion
"""

import argparse
import hashlib
import os
import struct
import sys
from pathlib import Path

# Magic bytes
GDPC_MAGIC = b'GDPC'
GST2_MAGIC = b'GST2'
RIFF_MAGIC = b'RIFF'
WEBP_MAGIC = b'WEBP'
JPEG_SOI = b'\xff\xd8'
JPEG_EOI = b'\xff\xd9'
MP3_HEAD = b'\xff\xfa'  # MP3 frame sync


def parse_args():
    parser = argparse.ArgumentParser(
        description='Godot PCK Unpacker - Extract assets from PCK files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Extract all assets (auto-detects format)
  python godot_unpacker.py ZD.pck -o output/
  
  # Extract only images
  python godot_unpacker.py ZD.pck --images -o images/
  
  # Extract only audio
  python godot_unpacker.py game.pck --audio -o audio/
  
  # Show PCK info
  python godot_unpacker.py game.pck --info
        '''
    )
    
    parser.add_argument('input', help='Input PCK file or directory')
    parser.add_argument('-o', '--output', help='Output directory')
    parser.add_argument('--info', action='store_true', help='Show PCK info only')
    parser.add_argument('--images', action='store_true', help='Extract only images')
    parser.add_argument('--audio', action='store_true', help='Extract only audio')
    parser.add_argument('--raw', action='store_true', help='Extract without conversion')
    
    return parser.parse_args()


def detect_format(data):
    """Detect PCK format type"""
    if len(data) < 20:
        return None
    
    if data[:4] != GDPC_MAGIC:
        return None
    
    # Check for GST2 format (Zombie Diary style)
    if len(data) > 120:
        if data[12:16] == b'\x06\x00\x00\x00':  # ZD format marker
            return 'ZD_GST2'
    
    # Check if GST2 header exists at 0x70
    if len(data) > 120:
        gst2_data = data[112:128]
        if gst2_data[:4] == GST2_MAGIC:
            return 'ZD_GST2'
    
    # Default to standard Godot PCK
    return 'STANDARD'


def parse_zd_header(data):
    """Parse ZD GST2 format header"""
    if len(data) < 120:
        return None
    
    # Parse GDPC header
    gdpc_version = struct.unpack('<I', data[4:8])[0]
    file_count = struct.unpack('<I', data[16:20])[0]
    section_offset = struct.unpack('<I', data[24:28])[0]
    
    # Parse GST2 header at 0x70
    gst2_magic = data[112:116]
    gst2_version = struct.unpack('<I', data[116:120])[0]
    entry_count = struct.unpack('<I', data[120:124])[0]
    data_offset = struct.unpack('<I', data[124:128])[0]
    
    # Extract GST2 key (XOR key)
    gst2_key = data[112:128]
    
    return {
        'gdpc_version': gdpc_version,
        'file_count': file_count,
        'section_offset': section_offset,
        'gst2_version': gst2_version,
        'entry_count': entry_count,
        'data_offset': data_offset,
        'gst2_key': gst2_key
    }


def parse_standard_header(data):
    """Parse standard Godot PCK header"""
    if len(data) < 80:
        return None
    
    gdpc_version = struct.unpack('<I', data[4:8])[0]
    file_count = struct.unpack('<I', data[8:12])[0]
    
    # Skip to file entries (after 64-byte padding)
    file_entries_start = 80
    
    # Parse entries
    entries = []
    offset = file_entries_start
    
    for _ in range(file_count):
        if offset + 4 > len(data):
            break
        
        name_len = struct.unpack('<I', data[offset:offset+4])[0]
        offset += 4
        
        if offset + name_len > len(data):
            break
        
        path = data[offset:offset+name_len].rstrip(b'\x00').decode('utf-8', errors='replace')
        offset += name_len
        
        # Skip 32 bytes padding
        offset += 32
        
        if offset + 8 > len(data):
            break
        
        file_offset = struct.unpack('<I', data[offset:offset+4])[0]
        offset += 4
        file_size = struct.unpack('<I', data[offset:offset+4])[0]
        offset += 4 + 20  # Skip 4 + 20 padding
        
        entries.append({
            'path': path,
            'offset': file_offset,
            'size': file_size
        })
    
    return {
        'version': gdpc_version,
        'file_count': file_count,
        'entries': entries
    }


def decrypt_zd_xor(data, key):
    """XOR decrypt with GST2 key"""
    result = bytearray(len(data))
    key_len = len(key)
    
    for i in range(len(data)):
        result[i] = data[i] ^ key[i % key_len]
    
    return bytes(result)


def extract_entries_zd(data, header, output_dir):
    """Extract entries from ZD GST2 format"""
    output_path = Path(output_dir)
    success = 0
    
    # Decrypt the data starting after file entries (at 0x80)
    encrypted_start = 128  # 0x80
    encrypted_data = data[encrypted_start:]
    
    # Get GST2 key from header
    key = header['gst2_key']
    
    # Decrypt
    decrypted = decrypt_zd_xor(encrypted_data, key)
    
    # Parse decrypted file entries
    offset = 0
    entries = []
    
    for i in range(header['entry_count']):
        if offset + 4 > len(decrypted):
            break
        
        name_len = struct.unpack('<I', decrypted[offset:offset+4])[0]
        offset += 4
        
        if offset + name_len > len(decrypted):
            break
        
        path = decrypted[offset:offset+name_len].rstrip(b'\x00').decode('utf-8', errors='replace')
        offset += name_len
        
        # Skip 32 bytes padding (ZD uses 32 bytes)
        offset += 32
        
        if offset + 8 > len(decrypted):
            break
        
        file_offset = struct.unpack('<I', decrypted[offset:offset+4])[0]
        offset += 4
        file_size = struct.unpack('<I', decrypted[offset:offset+4])[0]
        offset += 4 + 20
        
        entries.append({
            'path': path,
            'offset': file_offset,
            'size': file_size
        })
    
    # Extract files
    for entry in entries:
        # Find actual data offset in decrypted content
        actual_offset = header['data_offset'] + entry['offset']
        actual_size = entry['size']
        
        if actual_offset + actual_size > len(decrypted):
            continue
        
        file_data = decrypted[actual_offset:actual_offset+actual_size]
        
        # Convert path and write
        rel_path = entry['path']
        if rel_path.startswith('res://'):
            rel_path = rel_path[6:]
        
        out_path = output_path / rel_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(file_data)
        
        success += 1
    
    return success, entries


def extract_standard_entries(data, header, output_dir):
    """Extract entries from standard Godot PCK"""
    output_path = Path(output_dir)
    success = 0
    
    with open(Path(output_dir).parent / '_raw.pck', 'rb') as f:
        for entry in header['entries']:
            f.seek(entry['offset'])
            file_data = f.read(entry['size'])
            
            rel_path = entry['path']
            if rel_path.startswith('res://'):
                rel_path = rel_path[6:]
            
            out_path = output_path / rel_path
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_bytes(file_data)
            
            success += 1
    
    return success


def extract_images_only(data, output_dir):
    """Extract all images from decrypted data"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    found = 0
    
    # Scan for RIFF/WEBP signatures
    offset = 0
    while offset < len(data) - 4:
        if data[offset:offset+4] == RIFF_MAGIC and data[offset+8:offset+12] == WEBP_MAGIC:
            # Found WEBP
            end_offset = offset + 8
            while end_offset < len(data) - 4:
                if data[end_offset:end_offset+4] == RIFF_MAGIC and end_offset > offset + 100:
                    break
                end_offset += 1
            
            if end_offset < len(data) - 4:
                webp_data = data[offset:end_offset]
                with open(output_path / f'image_{found:06d}.webp', 'wb') as f:
                    f.write(webp_data)
                found += 1
                offset = end_offset
            else:
                break
        else:
            offset += 1
    
    # Scan for JPEG signatures
    offset = 0
    while offset < len(data) - 4:
        if data[offset:offset+2] == JPEG_SOI:
            # Find EOI
            end_offset = offset + 2
            while end_offset < len(data) - 2:
                if data[end_offset:end_offset+2] == JPEG_EOI:
                    end_offset += 2
                    break
                end_offset += 1
            
            jpeg_data = data[offset:end_offset]
            with open(output_path / f'jpeg_{found:06d}.jpg', 'wb') as f:
                f.write(jpeg_data)
            found += 1
            offset = end_offset
        else:
            offset += 1
    
    return found


def extract_audio_only(data, output_dir):
    """Extract all audio from decrypted data"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    found = 0
    
    # Scan for MP3 frame sync
    offset = 0
    while offset < len(data) - 4:
        if data[offset] == 0xFF and (data[offset+1] & 0xF0) in [0xF0, 0xF2, 0xF3]:
            # Possible MP3 frame
            # Find next frame or EOF
            end_offset = offset + 4
            while end_offset < len(data) - 4:
                # Simple heuristic: look for next potential frame sync
                if data[end_offset] == 0xFF and (data[end_offset+1] & 0xF0) in [0xF0, 0xF2, 0xF3]:
                    # Found next frame
                    mp3_data = data[offset:end_offset]
                    with open(output_path / f'audio_{found:06d}.mp3', 'wb') as f:
                        f.write(mp3_data)
                    found += 1
                    offset = end_offset
                    break
                end_offset += 1
            else:
                # EOF reached
                mp3_data = data[offset:]
                with open(output_path / f'audio_{found:06d}.mp3', 'wb') as f:
                    f.write(mp3_data)
                found += 1
                break
        else:
            offset += 1
    
    return found


def unpack_pck(input_path, output_dir, images_only=False, audio_only=False):
    """Main unpacking function"""
    input_path = Path(input_path)
    
    if not input_path.exists():
        print(f"Error: File not found: {input_path}")
        return 1
    
    # Read file
    with open(input_path, 'rb') as f:
        data = f.read()
    
    print(f"File size: {len(data)} bytes")
    
    # Detect format
    format_type = detect_format(data)
    print(f"Detected format: {format_type}")
    
    if not format_type:
        print("Error: Not a valid PCK file")
        return 1
    
    # Parse header
    if format_type == 'ZD_GST2':
        header = parse_zd_header(data)
        print(f"  GST2 Version: {header['gst2_version']}")
        print(f"  Entry count: {header['entry_count']}")
        print(f"  Data offset: {header['data_offset']}")
        print(f"  GST2 key: {header['gst2_key'].hex()}")
    else:
        header = parse_standard_header(data)
        print(f"  PCK Version: {header['version']}")
        print(f"  File count: {header['file_count']}")
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Process based on format
    if format_type == 'ZD_GST2':
        # Decrypt ZD format
        key = header['gst2_key']
        encrypted_start = 128  # 0x80
        encrypted_data = data[encrypted_start:]
        
        decrypted = decrypt_zd_xor(encrypted_data, key)
        
        if images_only:
            found = extract_images_only(decrypted, str(output_path))
            print(f"Extracted {found} images")
            return 0
        
        if audio_only:
            found = extract_audio_only(decrypted, str(output_path))
            print(f"Extracted {found} audio files")
            return 0
        
        # Extract all files
        success, entries = extract_entries_zd(decrypted, header, str(output_path))
        print(f"Extracted {success}/{len(entries)} files")
        return 0
    
    else:
        # Standard format - extract directly
        success = extract_standard_entries(data, header, str(output_path))
        print(f"Extracted {success} files")
        return 0


def main():
    args = parse_args()
    
    input_path = Path(args.input)
    output_dir = args.output
    
    if not output_dir:
        output_dir = input_path.stem + '_unpacked'
    
    if input_path.is_dir():
        # Process all PCK files in directory
        pck_files = list(input_path.glob('*.pck')) + list(input_path.glob('*.exe'))
        
        if not pck_files:
            print(f"No PCK files found in {input_path}")
            return 1
        
        print(f"Found {len(pck_files)} PCK/EXE files\n")
        
        total_success = 0
        total_files = 0
        
        for pck_file in pck_files:
            print(f"Processing: {pck_file.name}")
            result = unpack_pck(str(pck_file), f"{output_dir}/{pck_file.stem}", 
                              args.images, args.audio)
            if result == 0:
                total_success += 1
            total_files += 1
            print()
        
        print(f"Completed: {total_success}/{total_files} files")
        return 0
    
    else:
        # Process single file
        if args.info:
            # Just show info
            with open(input_path, 'rb') as f:
                data = f.read()
            
            format_type = detect_format(data)
            print(f"File: {input_path.name}")
            print(f"Size: {len(data)} bytes")
            print(f"Format: {format_type}")
            
            if format_type == 'ZD_GST2':
                header = parse_zd_header(data)
                print(f"  GST2 Version: {header['gst2_version']}")
                print(f"  Entry count: {header['entry_count']}")
                print(f"  Data offset: {header['data_offset']}")
            else:
                header = parse_standard_header(data)
                print(f"  PCK Version: {header['version']}")
                print(f"  File count: {header['file_count']}")
            
            return 0
        
        return unpack_pck(str(input_path), output_dir, args.images, args.audio)


if __name__ == '__main__':
    sys.exit(main() or 0)