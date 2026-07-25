#!/usr/bin/env python3
"""
Create final comprehensive report for Discord
"""

import os
import json
from pathlib import Path

def main():
    extracted_dir = r"C:\Users\red\Desktop\code\decode\extracted_files\.godot\imported"
    output_dir = r"C:\Users\red\Desktop\code\decode\extracted_assets"
    
    # Count assets
    ctex_count = len(list(Path(extracted_dir).glob("*.ctex")))
    
    # Count extracted textures
    textures_dir = os.path.join(output_dir, "textures")
    webp_count = len(list(Path(textures_dir).glob("*.webp")))
    jpg_count = len(list(Path(textures_dir).glob("*.jpg")))
    
    # Count extracted audio
    audio_dir = os.path.join(output_dir, "audio")
    mp3_count = len(list(Path(audio_dir).glob("*.mp3")))
    
    total_extracted = webp_count + jpg_count + mp3_count
    remaining_ctex = ctex_count - (webp_count + jpg_count)
    
    # Generate Discord report
    report = f"""
**ZOMBIE DIARY ASSET EXTRACTION REPORT**

**Summary:**
- Total assets found: **{ctex_count}** files
- Successfully extracted: **{total_extracted}** files
- Remaining: **{remaining_ctex}** files (may need additional analysis)

**Extracted Assets:**

**Textures:**
- .webp files: **{webp_count}**
- .jpg files: **{jpg_count}**
- Total: **{webp_count + jpg_count}**

**Audio:**
- .mp3 files: **{mp3_count}**
- Total: **{mp3_count}**

**Total: {total_extracted} assets successfully extracted to readable formats**

**Remaining Files:**
- {remaining_ctex} .ctex files (unextracted)
- These files may use a different compression format that requires additional analysis

**Extracted files saved to:**
`{output_dir}`

**Next Steps:**
- Further analysis of remaining 58 .ctex files may be needed
- Some files may use a different compression method (not standard WEBP or JPEG)

**Extracted files index saved to:**
`{os.path.join(output_dir, "extracted_assets_index.txt")}`
"""
    
    print(report)
    
    # Save full report to file
    report_path = os.path.join(output_dir, "DISCORD_REPORT.txt")
    with open(report_path, 'w') as f:
        f.write(report)
    
    print(f"\nFull report saved to: {report_path}")

if __name__ == "__main__":
    main()