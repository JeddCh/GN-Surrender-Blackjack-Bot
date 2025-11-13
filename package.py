import glob
import importlib.metadata
import os
import shutil
import subprocess
import sys

import paddlex


def build_exe():
    print("=" * 60)
    print("Smart BlackjackBot Build Script")
    print("=" * 60)

    # Clean old builds
    for folder in ["build", "dist"]:
        if os.path.exists(folder):
            shutil.rmtree(folder)
            print(f"Cleaned {folder}/ directory")

    # Main file to build
    main_file = "BlackjackGUI.py"

    # Get all installed packages
    user_deps = [dist.metadata["Name"] for dist in importlib.metadata.distributions()]

    # Get PaddleX required dependencies
    deps_all = list(paddlex.utils.deps.DEP_SPECS.keys())

    # Find which required deps are actually installed
    deps_need = [dep for dep in user_deps if dep in deps_all]

    print(f"\nFound {len(deps_need)} PaddleX dependencies to include:")
    for dep in deps_need:
        print(f"  - {dep}")

    # Build PyInstaller command
    cmd = [
        "pyinstaller",
        "--onedir",
        "--name=BlackjackBot",
        "--noconfirm",
        main_file,
        "--collect-data",
        "paddlex",
        "--collect-binaries",
        "paddle",
        "--collect-binaries",
        "nvidia",  # Include NVIDIA CUDA dependencies
    ]

    # Add metadata for all needed dependencies
    for dep in deps_need:
        cmd += ["--copy-metadata", dep]

    # Add your data files
    separator = ";" if sys.platform == "win32" else ":"

    data_files = []

    # Add Vars.txt
    if os.path.exists("Vars.txt"):
        data_files.append("Vars.txt")
        cmd += ["--add-data", f"Vars.txt{separator}."]
        print("✓ Adding Vars.txt")
    else:
        print("✗ WARNING: Vars.txt not found")

    # Add Strategy.xlsx
    if os.path.exists("Strategy.xlsx"):
        data_files.append("Strategy.xlsx")
        cmd += ["--add-data", f"Strategy.xlsx{separator}."]
        print("✓ Adding Strategy.xlsx")
    else:
        print("✗ WARNING: Strategy.xlsx not found")

    # Add BJ Buttons folder
    if os.path.exists("BJ Buttons"):
        cmd += ["--add-data", f"BJ Buttons{separator}BJ Buttons"]
        print("✓ Adding BJ Buttons folder")
    else:
        print("✗ WARNING: BJ Buttons folder not found")

    # Add Captured_Cards folder
    if os.path.exists("Captured_Cards"):
        cmd += ["--add-data", f"Captured_Cards{separator}Captured_Cards"]
        print("✓ Adding Captured_Cards folder")
    else:
        print("✗ WARNING: Captured_Cards folder not found")

    # Add PNG files
    png_files = glob.glob("*.PNG") + glob.glob("*.png")
    if png_files:
        print(f"✓ Found {len(png_files)} PNG files")
        for png in png_files:
            data_files.append(png)
            cmd += ["--add-data", f"{png}{separator}."]
    else:
        print("✗ WARNING: No PNG files found")

    print(f"\nTotal: {len(data_files)} files + folders to include")

    # Print command
    print("\n" + "=" * 60)
    print("PyInstaller command:")
    print(" ".join(cmd[:15]) + " ...")  # Truncated for readability
    print("=" * 60)

    # Run build
    try:
        print("\nBuilding (this may take several minutes)...")
        result = subprocess.run(cmd, check=True)

        print("\n" + "=" * 60)
        print("BUILD SUCCESSFUL!")
        print("=" * 60)

        # Verify and clean up
        dist_path = os.path.join("dist", "BlackjackBot")
        if os.path.exists(dist_path):
            print(f"\n✓ Application folder: {dist_path}")
            print(f"✓ Executable: {os.path.join(dist_path, 'BlackjackBot.exe')}")

            # Verify data files
            print("\nVerifying data files:")
            for f in data_files:
                dest = os.path.join(dist_path, os.path.basename(f))
                if os.path.exists(dest):
                    print(f"  ✓ {os.path.basename(f)}")
                else:
                    print(f"  ✗ {os.path.basename(f)} - MISSING, copying manually...")
                    try:
                        shutil.copy2(f, dest)
                        print(f"    ✓ Copied {os.path.basename(f)}")
                    except Exception as e:
                        print(f"    ✗ Failed to copy: {e}")

            # Verify folders
            print("\nVerifying folders:")
            for folder_name in ["BJ Buttons", "Captured_Cards"]:
                folder_path = os.path.join(dist_path, folder_name)
                if os.path.exists(folder_path):
                    file_count = len(
                        [
                            f
                            for f in os.listdir(folder_path)
                            if os.path.isfile(os.path.join(folder_path, f))
                        ]
                    )
                    print(f"  ✓ {folder_name}/ ({file_count} files)")
                else:
                    print(f"  ✗ {folder_name}/ - MISSING")
                    if os.path.exists(folder_name):
                        print(f"    Copying {folder_name} folder...")
                        try:
                            shutil.copytree(folder_name, folder_path)
                            print(f"    ✓ Copied {folder_name}/")
                        except Exception as e:
                            print(f"    ✗ Failed to copy: {e}")

            # Clean up build artifacts
            print("\nCleaning up temporary files...")
            if os.path.exists("build"):
                shutil.rmtree("build")
                print("  ✓ Deleted build/ folder")

            spec_file = "BlackjackBot.spec"
            if os.path.exists(spec_file):
                os.remove(spec_file)
                print("  ✓ Deleted .spec file")

            return True
        else:
            print(f"\n✗ ERROR: Distribution folder not found at {dist_path}")
            return False

    except subprocess.CalledProcessError as e:
        print(f"\n✗ Build failed with error: {e}")
        print("\n⚠ Keeping build/ folder for debugging")
        return False


if __name__ == "__main__":
    print(f"Python version: {sys.version}")
    print(f"Current directory: {os.getcwd()}")
    print()

    # Check PyInstaller
    if not shutil.which("pyinstaller"):
        print("PyInstaller not found! Installing...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "pyinstaller"], check=True
        )
        print("✓ PyInstaller installed\n")

    # Check main file exists
    if not os.path.exists("BlackjackGUI.py"):
        print("✗ ERROR: BlackjackGUI.py not found!")
        print("Make sure you're running this script from the project root directory.")
        sys.exit(1)

    # Pre-build checks
    print("Pre-build checks:")
    required_items = [
        "Vars.txt",
        "Strategy.xlsx",
        "BJ Buttons",
        "Captured_Cards",
        "BlackjackGUI.py",
    ]

    all_present = True
    for item in required_items:
        if os.path.exists(item):
            print(f"  ✓ {item}")
        else:
            print(f"  ✗ {item} - MISSING!")
            all_present = False

    if not all_present:
        print("\n⚠ WARNING: Some required files/folders are missing!")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != "y":
            print("Build cancelled.")
            sys.exit(1)

    print()
    success = build_exe()

    if success:
        print("\n" + "=" * 60)
        print("BUILD COMPLETE!")
        print("=" * 60)
        print("\nYour application is ready!")
        print("\nTo run:")
        print("  cd dist\\BlackjackBot")
        print("  BlackjackBot.exe")
        print("\nTo distribute:")
        print("  Zip the entire dist\\BlackjackBot\\ folder")
        print("  Users can extract and run BlackjackBot.exe")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("BUILD FAILED")
        print("=" * 60)
        print("\nCheck the errors above for details.")
        sys.exit(1)
