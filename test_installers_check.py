import os

base_dir = os.path.dirname(__file__)

def check_file_contains(filepath, substring, label):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    assert substring in content, f"[{label}] Expected '{substring}' in {filepath}"

def run_test():
    # 1. Check requirements files
    for req_file in ["requirements.txt", "requirements_linux.txt", "requirements_windows.txt"]:
        path = os.path.join(base_dir, req_file)
        check_file_contains(path, "PyQt6", req_file)
        check_file_contains(path, "numpy", req_file)
        check_file_contains(path, "opencv-python", req_file)
        check_file_contains(path, "Pillow", req_file)
        check_file_contains(path, "requests", req_file)

    # 2. Check PaintNotNet.spec hiddenimports
    spec_path = os.path.join(base_dir, "PaintNotNet.spec")
    check_file_contains(spec_path, "'requests'", "PaintNotNet.spec")
    check_file_contains(spec_path, "'PIL'", "PaintNotNet.spec")
    check_file_contains(spec_path, "'Pillow'", "PaintNotNet.spec")

    # 3. Check install.bat
    bat_path = os.path.join(base_dir, "install.bat")
    check_file_contains(bat_path, "1.0.9", "install.bat")
    check_file_contains(bat_path, "requirements_windows.txt", "install.bat")

    # 4. Check install.sh
    sh_path = os.path.join(base_dir, "install.sh")
    check_file_contains(sh_path, "1.0.9dev", "install.sh")
    check_file_contains(sh_path, "requirements_linux.txt", "install.sh")

    print("All installer & dependency verification checks passed successfully!")

if __name__ == "__main__":
    run_test()
