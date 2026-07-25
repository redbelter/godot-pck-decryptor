#!/usr/bin/env python3
"""
Extract textures from Godot .ctex files (encrypted with GST2 XOR key)
Convert them to standard WEBP/PNG formats
"""

import os
import hashlib
from pathlib import Path

def get_xor_key(gst2_header: bytes) -> bytes:
    """Generate XOR key from GST2 header"""
    # Use SHA256 of the GST2 data to create a consistent key
    return hashlib.sha256(gst2_header).digest()[:16]

def decrypt_data(data: bytes, key: bytes) -> bytes:
    """XOR decrypt data with repeating key"""
    result = bytearray(len(data))
    key_len = len(key)
    for i, b in enumerate(data):
        result[i] = b ^ key[i % key_len]
    return bytes(result)

def extract_ctex(filepath: str, output_dir: str):
    """Extract .ctex file to WEBP format"""
    try:
        with open(filepath, 'rb') as f:
            data = f.read()
        
        # Find GST2 header (usually around offset 0x70)
        gst2_pos = data.find(b'GST2')
        if gst2_pos == -1:
            print(f"  No GST2 header found in {os.path.basename(filepath)}")
            return None
        
        # Read GST2 header bytes (around 16 bytes)
        gst2_header = data[gst2_pos:gst2_pos+16]
        
        # The data after GST2 header should be encrypted
        encrypted_data = data[gst2_pos+16:]
        
        # Try XOR decryption with GST2 as key
        xor_key = hashlib.sha256(gst2_header).digest()[:16]
        decrypted = decrypt_data(encrypted_data, xor_key)
        
        # Check if decrypted data starts with WEBP RIFF header
        if decrypted.startswith(b'RIFF') and b'WEBP' in decrypted[:20]:
            # This is WEBP format, save it
            output_name = Path(filepath).stem.replace('.ctex', '.webp')
            output_path = os.path.join(output_dir, output_name)
            
            with open(output_path, 'wb') as f:
                f.write(decrypted)
            
            return output_path
        else:
            # Try other decryption approaches
            # Check for PNG signature
            if decrypted.startswith(b'\x89PNG'):
                output_name = Path(filepath).stem.replace('.ctex', '.png')
                output_path = os.path.join(output_dir, output_name)
                with open(output_path, 'wb') as f:
                    f.write(decrypted)
                return output_path
            
            # Check if it's already PNG data (some files might not be encrypted)
            if data.startswith(b'\x89PNG'):
                output_name = Path(filepath).stem.replace('.ctex', '.png')
                output_path = os.path.join(output_dir, output_name)
                with open(output_path, 'wb') as f:
                    f.write(data)
                return output_path
            
            print(f"  Unknown format - could not extract {os.path.basename(filepath)}")
            print(f"    First 20 bytes: {data[:20]}")
            return None
    
    except Exception as e:
        print(f"  Error processing {filepath}: {e}")
        return None

def extract_audio_sample(filepath: str, output_dir: str):
    """Extract .sample files (audio) to WAV format"""
    try:
        with open(filepath, 'rb') as f:
            data = f.read()
        
        # Sample files have metadata header followed by WAV data
        # Find WAV header
        wav_pos = data.find(b'RIFF')
        if wav_pos != -1:
            # Extract WAV data
            wav_data = data[wav_pos:]
            output_name = Path(filepath).stem.replace('.sample', '.wav')
            output_path = os.path.join(output_dir, output_name)
            
            with open(output_path, 'wb') as f:
                f.write(wav_data)
            return output_path
        else:
            print(f"  No WAV data found in {os.path.basename(filepath)}")
            return None
    except Exception as e:
        print(f"  Error processing {filepath}: {e}")
        return None

def main():
    extracted_dir = r"<decode_directory>\extracted_files\.godot\imported"
    textures_dir = r"<decode_directory>\extracted_assets\textures"
    audio_dir = r"<decode_directory>\extracted_assets\audio"
    
    # Create output directories
    os.makedirs(textures_dir, exist_ok=True)
    os.makedirs(audio_dir, exist_ok=True)
    
    # Find all .ctex files
    ctex_files = list(Path(extracted_dir).glob("*.ctex"))
    
    print(f"Found {len(ctex_files)} .ctex files to extract")
    
    extracted_count = 0
    failed_count = 0
    
    for ctex_file in ctex_files:
        print(f"\nProcessing: {ctex_file.name}")
        result = extract_ctex(str(ctex_file), textures_dir)
        if result:
            print(f"  -> Extracted to: {result}")
            extracted_count += 1
        else:
            failed_count += 1
    
    print(f"\n\nTexture Extraction complete:")
    print(f"  Successfully extracted: {extracted_count}")
    print(f"  Failed: {failed_count}")
    
    # Also check for video/audio files
    print("\n\nChecking for audio files...")
    
    # Check .sample files (audio)
    sample_files = list(Path(extracted_dir).glob("*.sample"))
    print(f"  Found {len(sample_files)} .sample (audio) files")
    
    sample_extracted = 0
    sample_failed = 0
    for sample_file in sample_files:
        print(f"\nProcessing: {sample_file.name}")
        result = extract_audio_sample(str(sample_file), audio_dir)
        if result:
            print(f"  -> Extracted to: {result}")
            sample_extracted += 1
        else:
            sample_failed += 1
    
    print(f"\n\nAudio Extraction complete:")
    print(f"  Successfully extracted: {sample_extracted}")
    print(f"  Failed: {sample_failed}")
    
    # Check .mp3str files (streaming audio)
    mp3str_files = list(Path(extracted_dir).glob("*.mp3str"))
    print(f"\n\nFound {len(mp3str_files)} .mp3str files")
    
    # Check .webm files
    webm_files = list(Path(r"<decode_directory>\extracted_files").glob("**/*.webm"))
    print(f"Found {len(webm_files)} .webm files")
    
    # Check for .scn files (scene files)
    scn_files = list(Path(r"<decode_directory>\extracted_files\.godot\exported").glob("**/*.scn"))
    print(f"Found {len(scn_files)} .scn (scene) files")
    
    # Check for .res files (resource files)
    res_files = list(Path(r"<decode_directory>\extracted_files\.godot\exported").glob("**/*.res"))
    print(f"Found {len(res_files)} .res (resource) files")

if __name__ == "__main__":
    main()