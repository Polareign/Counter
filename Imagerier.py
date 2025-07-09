import subprocess
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import json

CONFIG_FILE = os.path.expanduser("~/.nuclei_counter_config.json")

def get_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
        print("[INFO] Loaded config file.")
        return config
    else:
        config = {}
        tk.Tk().withdraw()
        # Require Fiji executable
        while True:
            messagebox.showinfo("Step 1", "Please select your Fiji executable (ImageJ-win64.exe)")
            print("[STEP] Waiting for user to select Fiji executable...")
            fiji_path = filedialog.askopenfilename(
                title="Select Fiji executable",
                filetypes=[("All files", "*.*")]
            )
            if fiji_path:
                config["fiji_path"] = fiji_path
                print(f"[INFO] Fiji executable selected: {fiji_path}")
                break
            else:
                messagebox.showerror("Error", "You must select a Fiji executable to continue.")
                print("[ERROR] Fiji executable not selected.")
        # Require macro file
        while True:
            messagebox.showinfo("Step 2", "Please select your macro file (e.g., Macro.ijm)")
            print("[STEP] Waiting for user to select macro file...")
            macro_path = filedialog.askopenfilename(
                title="Select Macro file",
                filetypes=[("ImageJ Macro", "*.ijm"), ("All files", "*.*")]
            )
            if macro_path:
                config["macro_path"] = macro_path
                print(f"[INFO] Macro file selected: {macro_path}")
                break
            else:
                messagebox.showerror("Error", "You must select a macro file to continue.")
                print("[ERROR] Macro file not selected.")
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f)
        print("[INFO] Config file saved.")
        return config

def count_nuclei_with_fiji(image_path, macro_path, fiji_path):
    print(f"[STEP] Running Fiji on image: {image_path}")
    cmd = [
        fiji_path,
        "--headless",
        "-macro", macro_path, image_path
    ]
    print("[INFO] Running command:", " ".join(cmd))
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        output = result.stdout + result.stderr
        print("[INFO] Fiji output received.")
        print(output)
        for line in output.splitlines():
            if "Count:" in line:
                count = int(line.split("Count:")[1].strip())
                print(f"[INFO] Nuclei count for {os.path.basename(image_path)}: {count}")
                return count
        print("[ERROR] Nuclei count not found in Fiji output.")
        messagebox.showerror("Error", f"Nuclei count not found in Fiji output for {os.path.basename(image_path)}.\n\nOutput:\n{output}")
        return None
    except Exception as e:
        print(f"[ERROR] Error running Fiji: {e}")
        messagebox.showerror("Error", f"Error running Fiji: {e}")
        return None

def select_and_count():
    config = get_config()
    messagebox.showinfo("Step 3", "Select one or more images to count nuclei.")
    print("[STEP] Waiting for user to select images...")
    file_paths = filedialog.askopenfilenames(
        title="Select images",
        filetypes=[("Image files", "*.jpg *.png *.tif *.tiff *.bmp"), ("All files", "*.*")]
    )
    if not file_paths:
        print("[INFO] No images selected.")
        return
    results = []
    for path in file_paths:
        count = count_nuclei_with_fiji(path, config["macro_path"], config["fiji_path"])
        results.append(f"{os.path.basename(path)}: {count if count is not None else 'Error'}")
    print("[INFO] All images processed. Showing results.")
    messagebox.showinfo("Nuclei Counts", "\n".join(results))

def change_settings():
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)
        print("[INFO] Config file deleted. User will be prompted to select Fiji and macro again.")
    messagebox.showinfo("Settings", "Please re-select your Fiji executable and macro file.")
    get_config()

if __name__ == "__main__":
    print("[INFO] Nuclei Counter started.")
    if len(sys.argv) == 2:
        config = get_config()
        image_path = sys.argv[1]
        print(f"[STEP] Running in command-line mode for image: {image_path}")
        count = count_nuclei_with_fiji(image_path, config["macro_path"], config["fiji_path"])
        if count is not None:
            print(f"Nuclei count: {count}")
        else:
            print("Failed to count nuclei.")
    else:
        root = tk.Tk()
        root.title("Nuclei Counter")
        root.geometry("350x140")
        btn = tk.Button(root, text="Select Images and Count Nuclei", command=select_and_count)
        btn.pack(expand=True, fill=tk.BOTH, padx=20, pady=10)
        btn_settings = tk.Button(root, text="Change Fiji/Macro Settings", command=change_settings)
        btn_settings.pack(expand=True, fill=tk.BOTH, padx=20, pady=10)
        print("[INFO] GUI loaded. Waiting for user action.")
        root.mainloop()