# ZD.pck Extraction Analysis

## Summary
The `ZD.pck` file uses **GDPC format** (Godot PCK with swapped header: GDPC instead of GDCP) and contains **encrypted content**.

## Evidence

### 1. File Header Analysis
- Magic bytes: `47 44 50 43` = "GDPC" 
- Standard Godot uses: `47 44 43 50` = "GDCP"
- The C/P swap indicates a custom/modified format

### 2. Content Structure
- First readable string (`res://`) found at offset **3,686,551** (after ~3.7MB)
- Gap between header and first file path contains non-null bytes → ENCRYPTED DATA
- No embedded ZIP signatures found

### 3. GDPC Validation Code
- ZD.exe contains `memcmp` with "GDPC" string at offset `0x29b130e`
- The code validates the PCK header before processing
- Godot's built-in loader handles GDPC format natively

### 4. PE Section Analysis
- No embedded .pck resource section in ZD.exe
- All sections are standard code/data sections
- No encryption keys found in static analysis

## Extraction Requirements
To extract encrypted PCK content, you need:

1. **Export Preset File** (`export_presets.cfg`) - Contains the encryption key
2. OR **Reverse-engineer the decryption algorithm** from ZD.exe (complex)

## Next Steps

### Option A: Find export_presets.cfg
Look for these files in the original game folder:
- `export_presets.cfg` (Godot project settings)
- `project.godot` (project configuration)

These might be embedded in a backup, installer, or development folder.

### Option B: Use Godot CLI to extract
If you can install Godot engine:
```bash
godot --check-only path/to/ZD.pck
```

Godot 4.x has built-in PCK handling that may work with GDPC format.

## Current Status
**PCK IS ENCRYPTED - Cannot extract without encryption key.**

The game loads the file because ZD.exe contains Godot's engine which knows how to decrypt it using the build-time configuration.
