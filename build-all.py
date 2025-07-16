#!/usr/bin/env python3
"""
Local Multi-Platform Build Test Script
This script helps test the build system locally and can simulate builds for different platforms.
"""

import json
import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a command and show the result."""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print("   ✅ Success")
        if result.stdout:
            print(f"   Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Failed: {e}")
        if e.stdout:
            print(f"   Output: {e.stdout}")
        if e.stderr:
            print(f"   Error: {e.stderr}")
        return False


def check_requirements():
    """Check if all build requirements are available."""
    print("🔍 Checking build requirements...")

    requirements = [
        ("uv --version", "uv package manager"),
        ("python --version", "Python interpreter"),
    ]

    all_good = True
    for cmd, name in requirements:
        if not run_command(cmd, f"Checking {name}"):
            all_good = False

    return all_good


def test_dependencies():
    """Test that all Python dependencies can be imported."""
    print("🧪 Testing Python dependencies...")

    test_imports = [
        "import tkinter; print(f'Tkinter: {tkinter.TkVersion}')",
        "import fitz; print(f'PyMuPDF: {fitz.VersionBind}')",
        "import PIL; print(f'Pillow: {PIL.__version__}')",
        "import platform; print(f'Platform: {platform.system()} {platform.machine()}')",
    ]

    for test_import in test_imports:
        cmd = f'uv run python -c "{test_import}"'
        if not run_command(cmd, f"Testing import: {test_import.split(';')[0]}"):
            return False

    return True


def build_current_platform():
    """Build for the current platform."""
    print("🚀 Building for current platform...")
    return run_command("uv run python build.py", "Building executable")


def analyze_build_output():
    """Analyze the build output and show summary."""
    print("📊 Analyzing build output...")

    # Check for dist directory
    dist_dir = Path("dist")
    if not dist_dir.exists():
        print("   ❌ No dist/ directory found")
        return False

    # Find executables
    executables = list(dist_dir.glob("PDF-Coordinate-Viewer-*"))
    if not executables:
        print("   ❌ No executables found in dist/")
        return False

    print(f"   ✅ Found {len(executables)} executable(s):")
    for exe in executables:
        size_mb = exe.stat().st_size / (1024 * 1024)
        print(f"      • {exe.name} ({size_mb:.1f} MB)")

    # Check for portable packages
    portable_dirs = list(Path(".").glob("PDF-Coordinate-Viewer-*-Portable"))
    if portable_dirs:
        print(f"   ✅ Found {len(portable_dirs)} portable package(s):")
        for pkg in portable_dirs:
            print(f"      • {pkg.name}/")
    else:
        print("   ⚠️  No portable packages found")

    # Check for release info
    release_info_file = Path("release-info.json")
    if release_info_file.exists():
        try:
            with open(release_info_file) as f:
                release_info = json.load(f)
            print("   ✅ Release info generated:")
            print(f"      • Platform: {release_info.get('platform', 'unknown')}")
            print(f"      • Build Date: {release_info.get('build_date', 'unknown')}")
            print(f"      • Executable Size: {release_info.get('executable_size', 'unknown')}")
        except Exception as e:
            print(f"   ⚠️  Could not read release info: {e}")

    return True


def clean_build_artifacts():
    """Clean up build artifacts."""
    print("🧹 Cleaning build artifacts...")

    import os
    import shutil

    # Directories to remove
    dirs_to_clean = ["build", "dist"]
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"   Removed {dir_name}/")

    # Files to remove
    files_to_clean = ["*.spec", "release-info.json", "PDF-Coordinate-Viewer-*-Portable"]
    for pattern in files_to_clean:
        for file_path in Path(".").glob(pattern):
            if file_path.is_file():
                file_path.unlink()
                print(f"   Removed {file_path}")
            elif file_path.is_dir():
                shutil.rmtree(file_path)
                print(f"   Removed {file_path}/")

    return True


def main():
    """Main test process."""
    print("🧪 PDF Coordinate Viewer - Build System Test")
    print("=" * 50)

    # Step 1: Check requirements
    if not check_requirements():
        print("\n❌ Build requirements not met. Please install missing tools.")
        sys.exit(1)

    print()

    # Step 2: Install dependencies
    if not run_command("uv sync --dev", "Installing dependencies"):
        print("\n❌ Failed to install dependencies.")
        sys.exit(1)

    print()

    # Step 3: Test dependencies
    if not test_dependencies():
        print("\n❌ Dependency test failed.")
        sys.exit(1)

    print()

    # Step 4: Clean previous builds
    clean_build_artifacts()

    print()

    # Step 5: Build current platform
    if not build_current_platform():
        print("\n❌ Build failed.")
        sys.exit(1)

    print()

    # Step 6: Analyze build output
    if not analyze_build_output():
        print("\n❌ Build analysis failed.")
        sys.exit(1)

    print()
    print("✅ Build system test completed successfully!")
    print("💡 Next steps:")
    print("   • Test the executable manually")
    print("   • Push to GitHub to trigger multi-platform builds")
    print("   • Create a git tag (e.g., v1.0.0) to trigger releases")


if __name__ == "__main__":
    main()
