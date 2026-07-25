#!/usr/bin/env python3
"""
Create a comprehensive report of all extracted assets
"""

import os
from pathlib import Path
from collections import defaultdict

def count_files(directory, pattern="*"):
    """Count files in a directory"""
    path = Path(directory)
    if not path.exists():
        return 0
    return len(list(path.glob(pattern)))

def main():
    extracted_dir = r"C:\Users\red\Desktop\code\decode\extracted_files\.godot\imported"
    output_dir = r"C:\Users\red\Desktop\code\decode\extracted_assets"
    
    print("="*80)
    print("ZOMBIE DIARY ASSET EXTRACTION REPORT")
    print("="*80)
    
    # Count original files
    ctex_count = count_files(extracted_dir, "*.ctex")
    png_count = count_files(extracted_dir, "*.png")
    print(f"\nOriginal extracted files:")
    print(f"  .ctex files: {ctex_count}")
    print(f"  .png files: {png_count}")
    
    # Count extracted assets
    textures_dir = os.path.join(output_dir, "textures")
    
    if os.path.exists(textures_dir):
        webp_count = count_files(textures_dir, "*.webp")
        jpg_count = count_files(textures_dir, "*.jpg")
        
        print(f"\nExtracted assets (textures):")
        print(f"  .webp files: {webp_count}")
        print(f"  .jpg files: {jpg_count}")
        print(f"  Total: {webp_count + jpg_count}")
    else:
        webp_count = 0
        jpg_count = 0
    
    # Also check audio files
    audio_dir = os.path.join(output_dir, "audio")
    if os.path.exists(audio_dir):
        wav_count = count_files(audio_dir, "*.wav")
        mp3_count = count_files(audio_dir, "*.mp3")
        print(f"\nExtracted assets (audio):")
        print(f"  .wav files: {wav_count}")
        print(f"  .mp3 files: {mp3_count}")
        print(f"  Total: {wav_count + mp3_count}")
    else:
        wav_count = 0
        mp3_count = 0
    
    # Count remaining .ctex files
    remaining_ctex = ctex_count - webp_count - jpg_count
    print(f"\nRemaining .ctex files (unextracted):")
    print(f"  {remaining_ctex}")
    
    # Summary
    print(f"\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    total_extracted = webp_count + jpg_count + wav_count + mp3_count
    total_assets = ctex_count + png_count  # Original file count
    
    print(f"Total assets found: {total_assets}")
    print(f"Successfully extracted: {total_extracted}")
    print(f"Remaining (may need additional processing): {ctex_count + png_count - total_extracted}")
    
    # List of extracted files
    print(f"\nExtracted files saved to: {output_dir}")
    
    # Create a file listing
    if os.path.exists(output_dir):
        with open(os.path.join(output_dir, "extracted_assets_index.txt"), 'w') as f:
            f.write("ZOMBIE DIARY ASSET EXTRACTION INDEX\n")
            f.write("="*80 + "\n\n")
            
            f.write("Texture Files (.webp, .jpg):\n")
            if os.path.exists(textures_dir):
                for fpath in sorted(Path(textures_dir).glob("*")):
                    if fpath.is_file():
                        f.write(f"  {fpath.name}\n")
            
            f.write("\nAudio Files (.wav, .mp3):\n")
            if os.path.exists(audio_dir):
                for fpath in sorted(Path(audio_dir).glob("*")):
                    if fpath.is_file():
                        f.write(f"  {fpath.name}\n")
    
    print(f"\nIndex saved to: {os.path.join(output_dir, 'extracted_assets_index.txt')}")
    
    # Return values for Discord message
    return {
        "total_assets": total_assets,
        "extracted": total_extracted,
        "remaining": ctex_count + png_count - total_extracted,
        "webp_count": webp_count,
        "jpg_count": jpg_count,
        "wav_count": wav_count,
        "mp3_count": mp3_count,
    }

if __name__ == "__main__":
    result = main()
    print(f"\nResult dict: {result}")