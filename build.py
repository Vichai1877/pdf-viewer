#!/usr/bin/env python3
"""
Multi-Platform Build Script for PDF Coordinate Viewer
This script uses PyInstaller to bundle the application into platform-specific executables.

Supported Platforms:
- Windows (creates .exe)
- Linux (creates executable binary)
- macOS (creates executable binary, can create .app bundle)
"""

import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def get_platform_info():
    """Get detailed platform information."""
    system = platform.system().lower()
    machine = platform.machine().lower()

    platform_map = {"windows": "windows", "linux": "linux", "darwin": "macos"}

    # Determine architecture
    arch_map = {"x86_64": "x64", "amd64": "x64", "arm64": "arm64", "aarch64": "arm64", "i386": "x86", "i686": "x86"}

    platform_name = platform_map.get(system, system)
    arch = arch_map.get(machine, machine)

    return {
        "system": platform_name,
        "architecture": arch,
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "is_windows": system == "windows",
        "is_linux": system == "linux",
        "is_macos": system == "darwin",
        "executable_suffix": ".exe" if system == "windows" else "",
        "platform_tag": f"{platform_name}-{arch}",
    }


def clean_build_directories():
    """Clean up previous build artifacts."""
    dirs_to_clean = ["build", "dist", "__pycache__"]
    files_to_clean = ["*.spec"]

    print("🧹 Cleaning previous build artifacts...")

    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"   Removed {dir_name}/")

    # Remove .spec files
    for spec_file in Path(".").glob("*.spec"):
        spec_file.unlink()
        print(f"   Removed {spec_file}")


def get_platform_specific_args(platform_info):
    """Get platform-specific PyInstaller arguments."""
    base_args = [
        "pyinstaller",
        "--name",
        f"PDF-Coordinate-Viewer-{platform_info['platform_tag']}",
        "--onefile",  # Create single executable file
        "--windowed",  # Hide console window
        "--noconfirm",  # Overwrite output directory without confirmation
        "--clean",  # Clean PyInstaller cache and temp files
        "--collect-all",
        "tkinter",  # Collect all tkinter submodules
        "--add-data",
        "README.md:.",  # Include README in bundle
        # Essential hidden imports for cross-platform compatibility
        "--hidden-import",
        "PIL._tkinter_finder",
        "--hidden-import",
        "tkinter",
        "--hidden-import",
        "tkinter.ttk",
        "--hidden-import",
        "tkinter.filedialog",
        "--hidden-import",
        "tkinter.messagebox",
        "--hidden-import",
        "tkinter.scrolledtext",
        "--hidden-import",
        "tkinter.font",
        "--hidden-import",
        "_tkinter",
        "--hidden-import",
        "PIL.Image",
        "--hidden-import",
        "PIL.ImageTk",
        "--hidden-import",
        "fitz",
    ]

    # Platform-specific arguments
    if platform_info["is_windows"]:
        base_args.extend(
            [
                "--exclude-module",
                "readline",  # Not needed on Windows
                # Note: _tkinter is now included via hidden-import
            ]
        )

    elif platform_info["is_linux"]:
        base_args.extend(
            [
                "--exclude-module",
                "win32api",
                "--exclude-module",
                "win32con",
                "--exclude-module",
                "win32gui",
                "--exclude-module",
                "win32ui",
            ]
        )

    elif platform_info["is_macos"]:
        base_args.extend(
            [
                "--exclude-module",
                "win32api",
                "--exclude-module",
                "win32con",
                "--exclude-module",
                "win32gui",
                "--exclude-module",
                "win32ui",
                "--osx-bundle-identifier",
                "com.pdfviewer.coordinate-tracker",
            ]
        )

    # Add the main script
    base_args.append("main.py")

    return base_args


def create_executable(platform_info):
    """Create the executable using PyInstaller."""
    print(f"🔨 Building executable for {platform_info['system']} {platform_info['architecture']}...")
    print(f"   Python: {platform_info['python_version']}")

    # Get platform-specific arguments
    cmd = get_platform_specific_args(platform_info)

    try:
        # Show the command being run
        print(f"   Command: {' '.join(cmd[:5])} ... (truncated)")

        # Run PyInstaller
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Build completed successfully!")

        # Show any warnings
        if result.stderr:
            print("⚠️  Build warnings:")
            for line in result.stderr.split("\n"):
                if line.strip() and "WARNING" in line:
                    print(f"   {line}")

        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed with error code {e.returncode}")
        print(f"Error output: {e.stderr}")
        print(f"Standard output: {e.stdout}")
        return False
    except FileNotFoundError:
        print("❌ PyInstaller not found. Please install it first:")
        print("   uv sync --dev")
        return False


def create_portable_package(platform_info):
    """Create a portable package with the executable and documentation."""
    print("📦 Creating portable package...")

    # Create platform-specific package directory
    package_name = f"PDF-Coordinate-Viewer-{platform_info['platform_tag']}-Portable"
    package_dir = Path(package_name)

    if package_dir.exists():
        shutil.rmtree(package_dir)

    package_dir.mkdir()

    # Copy executable
    executable_name = f"PDF-Coordinate-Viewer-{platform_info['platform_tag']}{platform_info['executable_suffix']}"
    executable_path = Path("dist") / executable_name

    if executable_path.exists():
        target_name = f"PDF-Coordinate-Viewer{platform_info['executable_suffix']}"
        shutil.copy2(executable_path, package_dir / target_name)
        print(f"   ✅ Copied {executable_name} → {target_name}")
    else:
        print(f"   ❌ Executable not found: {executable_path}")
        return False, None

    # Copy documentation
    files_to_copy = ["README.md"]
    for file_name in files_to_copy:
        if Path(file_name).exists():
            shutil.copy2(file_name, package_dir / file_name)
            print(f"   ✅ Copied {file_name}")

    # Create platform-specific usage instructions
    usage_file = package_dir / "USAGE.txt"
    with open(usage_file, "w") as f:
        f.write(f"""PDF Coordinate Viewer - Portable Version
==========================================
Platform: {platform_info["system"].title()} {platform_info["architecture"].upper()}
Built with Python: {platform_info["python_version"]}

QUICK START:
""")

        if platform_info["is_windows"]:
            f.write("""1. Double-click PDF-Coordinate-Viewer.exe
2. If Windows Defender blocks it, click "More info" then "Run anyway"
""")
        else:
            f.write("""1. Open terminal in this folder
2. Run: ./PDF-Coordinate-Viewer
3. If permission denied, run: chmod +x PDF-Coordinate-Viewer
""")

        f.write("""
USAGE:
3. Click "Open PDF" to load a PDF file
4. Select coordinate origin from dropdown
5. Click anywhere on PDF to get coordinates
6. Use navigation buttons or arrow keys to change pages

FEATURES:
- Track X-Y coordinates with customizable origins
- Visual markers at click points  
- Click history with CSV export
- Zoom controls for precision
- Keyboard shortcuts

SYSTEM REQUIREMENTS:
""")

        if platform_info["is_windows"]:
            f.write("- Windows 7 or later\n- No additional software required\n")
        elif platform_info["is_linux"]:
            f.write("- Modern Linux distribution\n- X11 or Wayland display server\n- No additional software required\n")
        elif platform_info["is_macos"]:
            f.write("- macOS 10.13 or later\n- No additional software required\n")

        f.write("""
For detailed documentation, see README.md

This is a portable version - no installation required!
Just run the executable from any location.
""")

    print("   ✅ Created USAGE.txt")

    # Create build info file
    build_info = {
        "platform": platform_info["system"],
        "architecture": platform_info["architecture"],
        "python_version": platform_info["python_version"],
        "build_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "executable_name": f"PDF-Coordinate-Viewer{platform_info['executable_suffix']}",
        "package_name": package_name,
    }

    with open(package_dir / "build-info.json", "w") as f:
        json.dump(build_info, f, indent=2)
    print("   ✅ Created build-info.json")

    print(f"✅ Portable package created: {package_dir}/")
    return True, package_dir


def get_file_size(file_path):
    """Get human-readable file size."""
    if not os.path.exists(file_path):
        return "N/A"

    size = os.path.getsize(file_path)
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def create_release_info(platform_info, package_dir):
    """Create release information file."""
    print("📋 Creating release information...")

    executable_name = f"PDF-Coordinate-Viewer-{platform_info['platform_tag']}{platform_info['executable_suffix']}"
    executable_path = Path("dist") / executable_name

    release_info = {
        "version": "1.0.0",
        "platform": platform_info["platform_tag"],
        "build_date": datetime.now().strftime("%Y-%m-%d"),
        "executable_size": get_file_size(executable_path),
        "package_size": get_directory_size(package_dir) if package_dir else "N/A",
        "python_version": platform_info["python_version"],
        "files": {"executable": str(executable_path), "package": str(package_dir) if package_dir else None},
    }

    with open("release-info.json", "w") as f:
        json.dump(release_info, f, indent=2)

    print("   ✅ Created release-info.json")
    return release_info


def get_directory_size(directory):
    """Get human-readable directory size."""
    if not os.path.exists(directory):
        return "N/A"

    total_size = 0
    for dirpath, dirnames, filenames in os.walk(directory):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            total_size += os.path.getsize(filepath)

    for unit in ["B", "KB", "MB", "GB"]:
        if total_size < 1024:
            return f"{total_size:.1f} {unit}"
        total_size /= 1024
    return f"{total_size:.1f} TB"


def main():
    """Main build process."""
    print("🚀 PDF Coordinate Viewer - Multi-Platform Build Script")
    print("=" * 60)

    # Get platform information
    platform_info = get_platform_info()
    print("🖥️  Platform Detection:")
    print(f"   System: {platform_info['system'].title()}")
    print(f"   Architecture: {platform_info['architecture'].upper()}")
    print(f"   Python: {platform_info['python_version']}")
    print(f"   Tag: {platform_info['platform_tag']}")
    print()

    # Check if we're in the right directory
    if not Path("main.py").exists():
        print("❌ main.py not found. Run this script from the project root directory.")
        sys.exit(1)

    # Step 1: Clean previous builds
    clean_build_directories()
    print()

    # Step 2: Create executable
    if not create_executable(platform_info):
        sys.exit(1)
    print()

    # Step 3: Create portable package
    success, package_dir = create_portable_package(platform_info)
    if not success:
        sys.exit(1)
    print()

    # Step 4: Create release info
    release_info = create_release_info(platform_info, package_dir)
    print()

    # Show results
    print("🎉 Build Summary")
    print("-" * 40)

    # Find the executable
    executable_name = f"PDF-Coordinate-Viewer-{platform_info['platform_tag']}{platform_info['executable_suffix']}"
    executable_path = Path("dist") / executable_name

    if executable_path.exists():
        size = get_file_size(executable_path)
        print(f"📁 Executable: dist/{executable_name}")
        print(f"   Size: {size}")
        print(f"   Platform: {platform_info['platform_tag']}")

    if package_dir and package_dir.exists():
        package_size = get_directory_size(package_dir)
        print(f"📦 Portable Package: {package_dir}/")
        print(f"   Size: {package_size}")
        print("   Ready for distribution!")

    print()
    print("✅ Build completed successfully!")
    print("💡 Distribution options:")
    print(f"   • Share the {package_dir}/ folder for end users")
    print("   • Upload to releases for automated distribution")
    print("   • Build on other platforms for multi-platform support")

    # Platform-specific notes
    if platform_info["is_windows"]:
        print("\n🪟 Windows Notes:")
        print("   • Users may need to allow through Windows Defender")
        print("   • Consider code signing for production distribution")
    elif platform_info["is_linux"]:
        print("\n🐧 Linux Notes:")
        print("   • Users may need to set executable permissions")
        print("   • Requires X11 or Wayland display server")
    elif platform_info["is_macos"]:
        print("\n🍎 macOS Notes:")
        print("   • Users may need to right-click → 'Open' for unsigned apps")
        print("   • Consider app notarization for production distribution")


if __name__ == "__main__":
    main()
