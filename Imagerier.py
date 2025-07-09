import subprocess
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import json
from datetime import datetime

CONFIG_FILE = os.path.expanduser("~/.nuclei_counter_config.json")
HISTORY_FILE = os.path.expanduser("~/.nuclei_counter_history.json")

def get_history():
    """Load counting history from file."""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                history = json.load(f)
            return history
        except:
            return []
    return []

def save_to_history(filename, count):
    """Save a count result to history."""
    history = get_history()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = {
        "filename": filename,
        "count": count,
        "timestamp": timestamp
    }
    history.append(entry)
    # Keep only last 100 entries
    if len(history) > 100:
        history = history[-100:]
    
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

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
        filename = os.path.basename(path)
        if count is not None:
            save_to_history(filename, count)
            results.append(f"{filename}: {count}")
        else:
            results.append(f"{filename}: Error")
    print("[INFO] All images processed. Showing results.")
    messagebox.showinfo("Nuclei Counts", "\n".join(results))

def change_fiji_settings():
    """Change only the Fiji executable setting."""
    config = get_config() if os.path.exists(CONFIG_FILE) else {}
    
    tk.Tk().withdraw()
    messagebox.showinfo("Change Fiji Setting", "Please select your Fiji executable (ImageJ-win64.exe)")
    print("[STEP] Waiting for user to select new Fiji executable...")
    fiji_path = filedialog.askopenfilename(
        title="Select Fiji executable",
        filetypes=[("All files", "*.*")]
    )
    if fiji_path:
        config["fiji_path"] = fiji_path
        print(f"[INFO] Fiji executable updated: {fiji_path}")
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f)
        messagebox.showinfo("Success", "Fiji executable updated successfully!")
    else:
        messagebox.showwarning("Cancelled", "Fiji executable was not changed.")

def change_macro_settings():
    """Change only the macro file setting."""
    config = get_config() if os.path.exists(CONFIG_FILE) else {}
    
    tk.Tk().withdraw()
    messagebox.showinfo("Change Macro Setting", "Please select your macro file (e.g., Macro.ijm)")
    print("[STEP] Waiting for user to select new macro file...")
    macro_path = filedialog.askopenfilename(
        title="Select Macro file",
        filetypes=[("ImageJ Macro", "*.ijm"), ("All files", "*.*")]
    )
    if macro_path:
        config["macro_path"] = macro_path
        print(f"[INFO] Macro file updated: {macro_path}")
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f)
        messagebox.showinfo("Success", "Macro file updated successfully!")
    else:
        messagebox.showwarning("Cancelled", "Macro file was not changed.")

def change_settings():
    """Legacy function - redirects to change all settings."""
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)
        print("[INFO] Config file deleted. User will be prompted to select Fiji and macro again.")
    messagebox.showinfo("Settings", "Please re-select your Fiji executable and macro file.")
    get_config()

def create_gui():
    """Create the main GUI with history display."""
    root = tk.Tk()
    root.title("Nuclei Counter")
    root.geometry("600x500")
    
    # Main frame
    main_frame = ttk.Frame(root, padding="10")
    main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    
    # Configure grid weights
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    main_frame.columnconfigure(1, weight=1)
    main_frame.rowconfigure(1, weight=1)
    
    # Button frame
    button_frame = ttk.Frame(main_frame)
    button_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
    
    # Main action button
    btn_count = ttk.Button(button_frame, text="Select Images and Count Nuclei", 
                          command=lambda: [select_and_count(), refresh_history()])
    btn_count.pack(fill=tk.X, pady=2)
    
    # Settings buttons
    settings_frame = ttk.Frame(button_frame)
    settings_frame.pack(fill=tk.X, pady=2)
    
    btn_fiji = ttk.Button(settings_frame, text="Change Fiji Settings", 
                         command=change_fiji_settings, width=25)
    btn_fiji.pack(side=tk.LEFT, padx=(0, 5))
    
    btn_macro = ttk.Button(settings_frame, text="Change Macro Settings", 
                          command=change_macro_settings, width=25)
    btn_macro.pack(side=tk.LEFT)
    
    # History section
    history_label = ttk.Label(main_frame, text="Previous Counts:", font=("Arial", 12, "bold"))
    history_label.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(10, 5))
    
    # Treeview for history
    columns = ("File", "Count", "Timestamp")
    history_tree = ttk.Treeview(main_frame, columns=columns, show="headings", height=15)
    
    # Configure columns
    history_tree.heading("File", text="File Name")
    history_tree.heading("Count", text="Count")
    history_tree.heading("Timestamp", text="Date/Time")
    
    history_tree.column("File", width=250)
    history_tree.column("Count", width=80)
    history_tree.column("Timestamp", width=150)
    
    history_tree.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
    
    # Scrollbar for history
    scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=history_tree.yview)
    scrollbar.grid(row=2, column=2, sticky=(tk.N, tk.S), pady=5)
    history_tree.configure(yscrollcommand=scrollbar.set)
    
    def refresh_history():
        """Refresh the history display."""
        # Clear existing items
        for item in history_tree.get_children():
            history_tree.delete(item)
        
        # Load and display history
        history = get_history()
        for entry in reversed(history):  # Show newest first
            history_tree.insert("", tk.END, values=(
                entry["filename"], 
                entry["count"], 
                entry["timestamp"]
            ))
    
    # Initial history load
    refresh_history()
    
    print("[INFO] GUI loaded. Waiting for user action.")
    root.mainloop()

if __name__ == "__main__":
    print("[INFO] Nuclei Counter started.")
    if len(sys.argv) == 2:
        try:
            config = get_config()
            image_path = sys.argv[1]
            print(f"[STEP] Running in command-line mode for image: {image_path}")
            count = count_nuclei_with_fiji(image_path, config["macro_path"], config["fiji_path"])
            if count is not None:
                # Save to history
                filename = os.path.basename(image_path)
                save_to_history(filename, count)
                print(f"Nuclei count: {count}")
            else:
                print("Failed to count nuclei.")
        except Exception as e:
            print(f"[ERROR] Command-line mode failed: {e}")
            sys.exit(1)
    else:
        try:
            create_gui()
        except Exception as e:
            print(f"[ERROR] GUI mode failed: {e}")
            print("[INFO] This might be due to no display available. Try running with an image path as argument for command-line mode.")
            sys.exit(1)