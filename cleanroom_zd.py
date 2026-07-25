#!/usr/bin/env python3
"""
Cleanroom PCK Decrypter - Fast XOR version

A standalone tool to decrypt ZD PCK files (GST2 XOR encryption) efficiently.
"""

import argparse
import sys
from pathlib import Path

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


def decrypt_zd_pck(pck_path: str, output_path: str = None, chunk_size: int = 1024*1024) -> bool:
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


def main():
    parser = argparse.ArgumentParser(
        description='Cleanroom - Decrypt ZD PCK files with GST2 XOR',
        epilog='''
Examples:
  python cleanroom.py --pck ZD.pck
  python cleanroom.py --pck ZD.pck --output output.pck
        '''
    )
    
    parser.add_argument('--pck', '-p', required=True, 
                        help='Path to ZD PCK file')
    parser.add_argument('--output', '-o',
                        help='Output file path (default: input_decrypted.pck)')
    
    args = parser.parse_args()
    
    # Check input file
    pck_path = Path(args.pck)
    if not pck_path.exists():
        print(f"Error: PCK file not found: {args.pck}")
        sys.exit(1)
    
    # Check for ZD format
    if not detect_zd_format(args.pck):
        print("Error: Not a ZD-style PCK file")
        print("This tool only handles ZD files with GST2 XOR encryption.")
        sys.exit(1)
    
    # Decrypt
    print("=" * 50)
    print("Cleanroom - ZD PCK Decrypter")
    print("=" * 50)
    print(f"[*] Input PCK: {args.pck}")
    print()
    
    success = decrypt_zd_pck(args.pck, args.output)
    
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