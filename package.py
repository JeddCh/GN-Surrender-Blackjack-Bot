import glob
import importlib.metadata
import os
import shutil
import subprocess
import sys


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

    # Check for paddlex - it may not be installed
    try:
        import paddlex

        # Get all installed packages
        user_deps = [
            dist.metadata["Name"] for dist in importlib.metadata.distributions()
        ]
        # Get PaddleX required dependencies
        deps_all = list(paddlex.utils.deps.DEP_SPECS.keys())
        # Find which required deps are actually installed
        deps_need = [dep for dep in user_deps if dep in deps_all]
        print(f"\nFound {len(deps_need)} PaddleX dependencies to include:")
        for dep in deps_need:
            print(f"  - {dep}")
        has_paddlex = True
    except ImportError:
        print("\nPaddleX not found - skipping PaddleX-specific packaging")
        deps_need = []
        has_paddlex = False

    # Build PyInstaller command
    cmd = [
        "pyinstaller",
        "--onedir",
        "--name=BlackjackBot",
        "--noconfirm",
        "--console",  # Shows console window for debugging output
        main_file,
    ]

    # Add PaddleX/Paddle specific options only if installed
    if has_paddlex:
        cmd += [
            "--collect-data",
            "paddlex",
            "--collect-binaries",
            "paddle",
            "--collect-binaries",
            "nvidia",
        ]
        # Add metadata for all needed dependencies
        for dep in deps_need:
            cmd += ["--copy-metadata", dep]

    # Platform-specific path separator
    separator = ";" if sys.platform == "win32" else ":"

    # Track all data files/folders for verification
    data_files = []
    data_folders = []

    print("\n" + "-" * 40)
    print("Adding data files and folders:")
    print("-" * 40)

    # === Single Files ===
    single_files = [
        "Vars.txt",
        "Strategy.xlsx",
        "Game Location.PNG",
    ]

    for file in single_files:
        if os.path.exists(file):
            data_files.append(file)
            cmd += ["--add-data", f"{file}{separator}."]
            print(f"  ✓ {file}")
        else:
            print(f"  ✗ WARNING: {file} not found")

    # === PNG files in root ===
    png_files = glob.glob("*.PNG") + glob.glob("*.png")
    # Filter out already added files
    png_files = [f for f in png_files if f not in single_files]
    if png_files:
        print(f"  ✓ Found {len(png_files)} additional PNG files in root")
        for png in png_files:
            data_files.append(png)
            cmd += ["--add-data", f"{png}{separator}."]

    # === Folders with assets ===
    folders_to_add = [
        ("BJ Buttons", "BJ Buttons"),
        ("Captured_Cards", "Captured_Cards"),
        ("Example Bbox", "Example Bbox"),
    ]

    for folder_name, dest_name in folders_to_add:
        if os.path.exists(folder_name):
            data_folders.append(folder_name)
            cmd += ["--add-data", f"{folder_name}{separator}{dest_name}"]
            # Count files recursively
            file_count = sum(len(files) for _, _, files in os.walk(folder_name))
            print(f"  ✓ {folder_name}/ ({file_count} files)")
        else:
            print(f"  ✗ WARNING: {folder_name}/ folder not found")

    # === Hidden imports for local modules ===
    print("\n" + "-" * 40)
    print("Adding hidden imports:")
    print("-" * 40)

    # All Python files that might be imported
    hidden_imports = [
        # Root level modules
        "BlackjackMain",
        "boundingbox",
        "ButtonChecker",
        "find_player",
        "NumberGrabber",
        "OCR",
        "ReadVars",
        "resource_path",
        # blackjack_bot package
        "blackjack_bot",
        "blackjack_bot.bot",
        "blackjack_bot.enums",
        "blackjack_bot.main",
        "blackjack_bot.models",
        "blackjack_bot.game",
        "blackjack_bot.game.action_executor",
        "blackjack_bot.game.button_manager",
        "blackjack_bot.game.card_reader",
        "blackjack_bot.strategy",
        "blackjack_bot.strategy.decider",
        "blackjack_bot.strategy.tables",
        "blackjack_bot.utils",
        "blackjack_bot.utils.screenshot",
    ]

    for module in hidden_imports:
        cmd += ["--hidden-import", module]
        print(f"  ✓ {module}")

    # === Common dependencies that often need explicit inclusion ===
    common_hidden = [
        "PIL",
        "PIL._imagingtk",
        "PIL._tkinter_finder",
        "cv2",
        "numpy",
        "pandas",
        "openpyxl",
        "tkinter",
        "pyautogui",
        "pynput",
        "keyboard",
        "mss",
        "win32gui",
        "win32api",
        "win32con",
    ]

    print("\n  Common dependencies:")
    for module in common_hidden:
        cmd += ["--hidden-import", module]
        print(f"  ✓ {module}")

    # Summary
    print("\n" + "-" * 40)
    print(f"Total: {len(data_files)} files + {len(data_folders)} folders")
    print(f"Hidden imports: {len(hidden_imports) + len(common_hidden)}")
    print("-" * 40)

    # Print command (truncated)
    print("\n" + "=" * 60)
    print("PyInstaller command:")
    cmd_preview = " ".join(cmd[:10]) + f" ... ({len(cmd)} args total)"
    print(cmd_preview)
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

            # Verify and copy data files if missing
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

            # Verify and copy folders if missing
            print("\nVerifying folders:")
            for folder_name in data_folders:
                folder_path = os.path.join(dist_path, folder_name)
                if os.path.exists(folder_path):
                    file_count = sum(len(files) for _, _, files in os.walk(folder_path))
                    print(f"  ✓ {folder_name}/ ({file_count} files)")
                else:
                    print(f"  ✗ {folder_name}/ - MISSING, copying manually...")
                    if os.path.exists(folder_name):
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

            # Calculate final size
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(dist_path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    total_size += os.path.getsize(fp)
            size_mb = total_size / (1024 * 1024)
            print(f"\n  Total distribution size: {size_mb:.1f} MB")

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
        ("BlackjackGUI.py", "file"),
        ("Vars.txt", "file"),
        ("Strategy.xlsx", "file"),
        ("Game Location.PNG", "file"),
        ("BJ Buttons", "folder"),
        ("Captured_Cards", "folder"),
        ("blackjack_bot", "folder"),
    ]

    all_present = True
    for item, item_type in required_items:
        if os.path.exists(item):
            if item_type == "folder":
                file_count = sum(len(files) for _, _, files in os.walk(item))
                print(f"  ✓ {item}/ ({file_count} files)")
            else:
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
        print("  1. Zip the entire dist\\BlackjackBot\\ folder")
        print("  2. Send the zip to your friend")
        print("  3. They extract and run BlackjackBot.exe")
        print("\nNote: If the app needs a console for debugging, edit")
        print("      package.py and change --windowed to --console")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("BUILD FAILED")
        print("=" * 60)
        print("\nCheck the errors above for details.")
        print("\nCommon fixes:")
        print("  1. Make sure all dependencies are installed:")
        print("     pip install -r requirements.txt")
        print("  2. Try running with --console instead of --windowed")
        print("  3. Check for import errors in your Python files")
        sys.exit(1)
