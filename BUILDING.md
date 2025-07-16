# Building PDF Coordinate Viewer

This guide provides comprehensive information about building the PDF Coordinate Viewer for multiple platforms.

## 🚀 Quick Start

### Local Building

**Easiest method:**
```bash
# Linux/macOS
./build.sh

# Windows
build.bat

# Manual/Advanced
uv run python build.py
```

**Test everything:**
```bash
uv run python build-all.py
```

### Automated CI/CD

- **Push to main/develop** → Development builds for all platforms
- **Create git tag** (e.g., `v1.0.0`) → Official releases
- **Pull request** → Validation builds

## 🏗️ Multi-Platform Architecture

### Supported Platforms

| Platform | Architecture | Python | Executable | Package |
|----------|-------------|---------|------------|---------|
| Windows  | x64         | 3.11    | `.exe`     | `.zip`  |
| Linux    | x64         | 3.11    | binary     | `.tar.gz` |
| macOS    | x64         | 3.11    | binary     | `.tar.gz` |

*Future: ARM64 support planned*

### Build Matrix

The GitHub Actions workflow builds on:
- **ubuntu-latest** (Linux x64)
- **windows-latest** (Windows x64)  
- **macos-latest** (macOS x64)

## 🔧 Build System Components

### Core Scripts

1. **`build.py`** - Advanced multi-platform build script
   - Platform detection and configuration
   - PyInstaller automation
   - Portable package creation
   - Build metadata generation

2. **`build.sh`** / **`build.bat`** - Simple wrapper scripts
   - Dependency installation
   - Single-command building
   - Error handling

3. **`build-all.py`** - Comprehensive testing
   - Full build system validation
   - Dependency verification
   - Output analysis

### CI/CD Pipeline

```yaml
# .github/workflows/build-multiplatform.yml
name: Build Multi-Platform Executables

on:
  push: [main, develop]
  tags: ['v*']
  pull_request: [main]
  workflow_dispatch:

jobs:
  build: # Parallel builds for all platforms
  create-release: # Automated releases for tags
  build-summary: # Detailed reports
```

## 🔬 Build Process Deep Dive

### 1. Platform Detection

```python
def get_platform_info():
    return {
        'system': 'windows|linux|macos',
        'architecture': 'x64|arm64|x86',
        'platform_tag': 'windows-x64',
        'executable_suffix': '.exe|""'
    }
```

### 2. PyInstaller Configuration

**Base arguments:**
```python
[
    "--onefile",              # Single executable
    "--windowed",             # GUI app (no console)
    "--noconfirm",            # Overwrite without prompt
    "--clean",                # Clean cache
]
```

**Platform-specific exclusions:**
- **Windows**: Exclude `readline`, Unix modules
- **Linux/macOS**: Exclude `win32*` modules
- **All**: Include essential hidden imports

### 3. Package Generation

Each build creates:
```
📁 dist/
  └── PDF-Coordinate-Viewer-{platform}-{arch}(.exe)

📦 PDF-Coordinate-Viewer-{platform}-{arch}-Portable/
  ├── PDF-Coordinate-Viewer(.exe)      # Clean executable name
  ├── README.md                        # Full documentation
  ├── USAGE.txt                        # Platform-specific guide
  └── build-info.json                  # Build metadata
```

### 4. Release Automation

For git tags (e.g., `v1.0.0`):
1. Parallel builds on all platforms
2. Create GitHub release
3. Upload platform-specific archives
4. Generate release notes

## 🛠️ Advanced Configuration

### Custom Build Options

Modify `build.py` for customization:

```python
def get_platform_specific_args(platform_info):
    base_args = [
        # Standard options
        "--onefile", "--windowed",
        
        # Custom additions
        "--icon", "assets/icon.ico",        # Custom icon
        "--add-data", "templates:templates", # Include data
        "--exclude-module", "unused_module", # Reduce size
        "--upx-dir", "/path/to/upx",        # Compression
    ]
```

### Build Variants

Create different build types:

```python
# Debug build
if debug_mode:
    base_args.extend([
        "--console",                    # Show console
        "--debug",                     # Debug mode
        "--log-level", "DEBUG"         # Verbose logging
    ])

# Optimized build  
if optimize:
    base_args.extend([
        "--strip",                     # Strip symbols
        "--upx-dir", upx_path,         # Compress
        "--exclude-module", "pdb"      # Remove debugger
    ])
```

### Environment Variables

Control builds via environment:

```bash
# Build options
export PYINSTALLER_COMPILE_BOOTLOADER=1  # Compile bootloader
export UPX_DIR=/usr/bin                   # UPX compressor path

# Debug options
export PYINSTALLER_DEBUG=1               # Debug PyInstaller
export PYTHONDEBUG=1                     # Python debug mode
```

## 🧪 Testing Strategy

### Local Testing

```bash
# 1. Test build system
uv run python build-all.py

# 2. Manual verification
ls -la dist/
file dist/PDF-Coordinate-Viewer-*

# 3. Basic executable test
./dist/PDF-Coordinate-Viewer-* --help || echo "GUI app"
```

### CI Testing

The GitHub Actions workflow includes:

1. **Dependency verification**: Import tests for all modules
2. **Build validation**: Successful PyInstaller execution  
3. **Artifact verification**: Executable creation and sizing
4. **Cross-platform**: All platforms build simultaneously

### Quality Gates

- ✅ All imports successful
- ✅ Executable created (~44MB)
- ✅ Portable package generated
- ✅ Platform-specific documentation
- ✅ Build metadata complete

## 🐛 Troubleshooting

### Common Build Issues

**"Module not found" errors:**
```bash
# Add to hidden imports in build.py
"--hidden-import", "missing_module"
```

**Large executable size:**
```bash
# Exclude unnecessary modules
"--exclude-module", "unused_module"

# Use directory instead of single file
"--onedir"  # instead of "--onefile"
```

**Platform-specific failures:**

**Linux:**
```bash
# Install system dependencies
sudo apt-get install python3-tk python3-dev
export DISPLAY=:99  # For headless builds
```

**Windows:**
```batch
# Antivirus exclusions
# Add build directory to Windows Defender exclusions
```

**macOS:**
```bash
# Handle unsigned executables
codesign --force --deep --sign - dist/PDF-Coordinate-Viewer
```

### Debugging Build Failures

**Enable verbose output:**
```python
# In build.py, add:
"--log-level", "DEBUG",
"--debug"
```

**Check PyInstaller logs:**
```bash
# Look in build/PDF-Coordinate-Viewer/
ls build/PDF-Coordinate-Viewer/
cat build/PDF-Coordinate-Viewer/warn-PDF-Coordinate-Viewer.txt
```

**Test imports manually:**
```bash
uv run python -c "import tkinter, fitz, PIL; print('All OK')"
```

## 📦 Distribution

### Release Process

1. **Tag creation:**
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

2. **Automated builds** trigger for all platforms

3. **GitHub Release** created with:
   - `PDF-Coordinate-Viewer-windows-x64.zip`
   - `PDF-Coordinate-Viewer-linux-x64.tar.gz`
   - `PDF-Coordinate-Viewer-macos-x64.tar.gz`

### Manual Distribution

```bash
# Create archives manually
tar -czf app-linux.tar.gz PDF-Coordinate-Viewer-linux-x64-Portable/
zip -r app-windows.zip PDF-Coordinate-Viewer-windows-x64-Portable/
```

### Security Considerations

**Code Signing (Production):**
- **Windows**: SignTool with certificate
- **macOS**: Apple Developer ID + notarization
- **Linux**: GPG signatures for packages

**Antivirus:** 
- PyInstaller executables may trigger false positives
- Submit to vendors for whitelisting
- Consider certificate signing

## 🔮 Future Enhancements

### Planned Features

1. **ARM64 Support:**
   - Apple Silicon (M1/M2) 
   - ARM64 Linux (Raspberry Pi)
   - ARM64 Windows

2. **Additional Platforms:**
   - FreeBSD
   - Solaris/Illumos

3. **Build Optimizations:**
   - UPX compression
   - Dead code elimination
   - Dependency analysis

4. **Distribution Improvements:**
   - App Store packaging
   - Linux packages (deb, rpm, AppImage)
   - Chocolatey/Homebrew packages

### Contributing Platforms

To add a new platform:

1. **Update platform detection** in `get_platform_info()`
2. **Add build configuration** in `get_platform_specific_args()`
3. **Update CI matrix** in GitHub Actions
4. **Test thoroughly** on target platform
5. **Document platform-specific requirements**

## 📊 Build Metrics

### Typical Performance

| Platform | Build Time | Executable Size | Dependencies |
|----------|------------|----------------|--------------|
| Linux    | 3-5 min    | 44.1 MB        | 15 packages  |
| Windows  | 4-6 min    | 44.8 MB        | 16 packages  |
| macOS    | 5-7 min    | 45.2 MB        | 15 packages  |

### Size Breakdown

- **Python Runtime**: ~20MB
- **PyMuPDF**: ~8MB  
- **Pillow**: ~6MB
- **Tkinter**: ~5MB
- **Application Code**: ~1MB
- **Other Dependencies**: ~4MB

## 🔗 Resources

### Documentation
- [PyInstaller Manual](https://pyinstaller.readthedocs.io/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [uv Package Manager](https://docs.astral.sh/uv/)

### Tools
- [PyInstaller](https://www.pyinstaller.org/) - Python packaging
- [UPX](https://upx.github.io/) - Executable compression  
- [GitHub Actions](https://github.com/features/actions) - CI/CD
- [uv](https://github.com/astral-sh/uv) - Python package management

### Community
- [PyInstaller GitHub Issues](https://github.com/pyinstaller/pyinstaller/issues)
- [Python Packaging Guide](https://packaging.python.org/)
- [Cross-Platform Development](https://docs.python.org/3/library/platform.html)

---

**Need Help?** Check the [main README](README.md) or create an issue with your platform details and error messages. 