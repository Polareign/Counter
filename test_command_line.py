import subprocess
import sys
import os

def test_fiji_headless():
    """Test Fiji headless execution with minimal macro."""
    
    # Hardcode your paths for testing
    fiji_path = r"C:\Users\Griffin Taylor\Downloads\Fiji.app\ImageJ-win64.exe"
    macro_path = r"C:\Users\Griffin Taylor\Downloads\test_macro.ijm"
    image_path = r"C:\Users\Griffin Taylor\Downloads\LCR10-Chip6-Location1BottomEndoRED.JPG"
    
    # Check if files exist
    print(f"[TEST] Checking files...")
    print(f"[TEST] Fiji exists: {os.path.exists(fiji_path)}")
    print(f"[TEST] Macro exists: {os.path.exists(macro_path)}")
    print(f"[TEST] Image exists: {os.path.exists(image_path)}")
    
    if not all([os.path.exists(fiji_path), os.path.exists(macro_path), os.path.exists(image_path)]):
        print("[ERROR] Some files don't exist!")
        return
    
    # Try the simplest command
    cmd = [fiji_path, "--headless", "-macro", macro_path, image_path]
    print(f"[TEST] Running command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print(f"[TEST] Return code: {result.returncode}")
        print(f"[TEST] STDOUT:")
        print(result.stdout)
        print(f"[TEST] STDERR:")
        print(result.stderr)
        
        # Look for count
        all_output = result.stdout + result.stderr
        for line in all_output.splitlines():
            if "Count:" in line:
                print(f"[SUCCESS] Found count line: {line}")
                return
        
        print("[WARNING] No count found in output")
        
    except subprocess.TimeoutExpired:
        print("[ERROR] Command timed out after 30 seconds")
    except Exception as e:
        print(f"[ERROR] Command failed: {e}")

if __name__ == "__main__":
    test_fiji_headless()