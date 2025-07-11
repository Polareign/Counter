import subprocess
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import json
import glob
import csv
import tempfile
import time
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
        except Exception as e:
            print(f"[ERROR] Failed to load history: {e}")
            return []
    return []

def save_to_history(filename, count):
    """Save a count result to history."""
    try:
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
        print(f"[INFO] Saved to history: {filename} - {count}")
    except Exception as e:
        print(f"[ERROR] Failed to save to history: {e}")

def get_config():
    """Get or create configuration for ImageJ and macro paths."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
            print("[INFO] Loaded existing config file.")
            
            # Validate config has required keys (imagej_path is required, macro_path is optional)
            if "imagej_path" in config:
                return config
            else:
                print("[WARNING] Config file missing required keys. Recreating...")
                os.remove(CONFIG_FILE)
        except Exception as e:
            print(f"[ERROR] Failed to load config: {e}")
            if os.path.exists(CONFIG_FILE):
                os.remove(CONFIG_FILE)
    
    # Create new config
    config = {}
    try:
        root = tk.Tk()
        root.withdraw()
        
        # Get ImageJ executable - REQUIRED
        print("[STEP] Waiting for user to select ImageJ executable...")
        imagej_path = filedialog.askopenfilename(
            title="Select ImageJ executable (ImageJ-win64.exe)",
            filetypes=[("Executable files", "*.exe"), ("All files", "*.*")]
        )
        if imagej_path and os.path.exists(imagej_path):
            config["imagej_path"] = imagej_path
            print(f"[INFO] ImageJ executable selected: {imagej_path}")
        else:
            print("[ERROR] ImageJ executable not selected. Exiting.")
            sys.exit(1)
        
        # Get macro file - OPTIONAL
        print("[STEP] Waiting for user to select macro file (or Cancel to use built-in macro)...")
        macro_path = filedialog.askopenfilename(
            title="Select Macro file (e.g., Counter.ijm) - Cancel to use built-in macro",
            filetypes=[("ImageJ Macro", "*.ijm"), ("All files", "*.*")]
        )
        if macro_path and os.path.exists(macro_path):
            config["macro_path"] = macro_path
            print(f"[INFO] Custom macro file selected: {macro_path}")
        else:
            config["macro_path"] = None  # Use built-in macro
            print("[INFO] No macro file selected. Will use built-in macro.")
        
        # Save config
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)
        print("[INFO] Config file saved.")
        
        root.destroy()
        return config
        
    except Exception as e:
        print(f"[ERROR] Failed to get config: {e}")
        sys.exit(1)

def count_multiple_nuclei_with_imagej(image_paths, macro_path, imagej_path):
    """Count nuclei in multiple images using a single ImageJ session."""
    print(f"[STEP] Running ImageJ once for {len(image_paths)} images")
    
    # Validate inputs
    if not image_paths:
        print("[ERROR] No image paths provided")
        return {}
    
    if not os.path.exists(imagej_path):
        print(f"[ERROR] ImageJ executable not found: {imagej_path}")
        return {}
    
    # Create a temporary results file to capture all counts
    temp_results = tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.csv')
    temp_results_path = temp_results.name
    temp_results.close()
    
    # Determine processing steps to use
    if macro_path and os.path.exists(macro_path):
        # Use custom macro - extract processing steps
        try:
            with open(macro_path, 'r') as f:
                custom_macro = f.read()
            print(f"[INFO] Using custom macro processing from: {macro_path}")
            
            # Extract processing steps (remove open() and print() statements)
            processing_steps = custom_macro.replace('open(getArgument());', '')
            processing_steps = processing_steps.replace('print("Count: " + count);', '')
            processing_steps = processing_steps.strip()
            
        except Exception as e:
            print(f"[WARNING] Could not read custom macro: {e}")
            print("[INFO] Using built-in processing steps")
            processing_steps = '''run("8-bit");
run("Median...", "radius=3");
setAutoThreshold("Otsu");
run("Convert to Mask");
run("Invert");
run("Watershed");
run("Analyze Particles...", "size=600-5000 circularity=0.00-1.00 show=Nothing clear");'''
    else:
        # Use built-in processing steps - REVERTED TO ORIGINAL
        print("[INFO] Using built-in processing steps")
        processing_steps = '''run("8-bit");
run("Median...", "radius=3");
setAutoThreshold("Otsu");
run("Convert to Mask");
run("Invert");
run("Watershed");
run("Analyze Particles...", "size=600-5000 circularity=0.00-1.00 show=Nothing clear");'''
    
    # Create batch macro that processes all images
    batch_macro_content = f'''
// Batch macro to process multiple images in one session
setBatchMode(true);

// Results file path
results_path = "{temp_results_path.replace(chr(92), '/')}";

// Write CSV header
File.append("Filename,Count", results_path);

print("Starting batch processing of {len(image_paths)} images...");

'''
    
    # Add processing code for each image
    for i, image_path in enumerate(image_paths):
        safe_image_path = image_path.replace(chr(92), '/').replace('"', '\\"')
        filename = os.path.basename(image_path)
        
        batch_macro_content += f'''
// Process image {i+1}: {filename}
print("Processing {filename}...");
run("Clear Results");

// Enhanced image opening with error handling
if (File.exists("{safe_image_path}")) {{
    open("{safe_image_path}");
    
    if (nImages > 0) {{
        // Processing steps
        {processing_steps}
        
        count = nResults;
        print("Found " + count + " nuclei in {filename}");
        File.append("{filename}," + count, results_path);
        
    }} else {{
        print("ERROR: Could not open image: {filename}");
        File.append("{filename},ERROR", results_path);
    }}
}} else {{
    print("ERROR: File not found: {safe_image_path}");
    File.append("{filename},ERROR", results_path);
}}

run("Close All");

'''
    
    # Add macro ending
    batch_macro_content += '''
setBatchMode(false);
print("Batch processing complete!");
run("Quit");
'''
    
    # Write the batch macro to a temporary file
    temp_macro = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.ijm')
    temp_macro.write(batch_macro_content)
    temp_macro.close()
    temp_macro_path = temp_macro.name
    
    # Command to run ImageJ once with the batch macro
    cmd = [imagej_path, "-macro", temp_macro_path]
    
    try:
        print(f"[INFO] Starting ImageJ batch processing...")
        print(f"[INFO] Command: {' '.join(cmd)}")
        
        # Set environment variables
        env = os.environ.copy()
        env['JAVA_OPTS'] = '-Djava.awt.headless=false'
        
        # Start ImageJ process
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env
        )
        
        # Wait for ImageJ to process all images and close
        try:
            stdout, stderr = process.communicate(timeout=300)  # 5 minutes timeout
            return_code = process.returncode
        except subprocess.TimeoutExpired:
            print(f"[WARNING] ImageJ batch processing timed out after 5 minutes")
            process.kill()
            stdout, stderr = process.communicate()
            return_code = process.returncode
        
        print(f"[INFO] ImageJ batch processing completed. Return code: {return_code}")
        print(f"[DEBUG] ImageJ output: {repr(stdout + stderr)}")
        
        # Read the results file
        results = {}
        try:
            time.sleep(2)  # Give time for file to be written
            
            if os.path.exists(temp_results_path):
                with open(temp_results_path, 'r') as f:
                    lines = f.readlines()
                
                print(f"[DEBUG] Results file content: {lines}")
                
                # Parse CSV results (skip header)
                for line in lines[1:]:
                    if ',' in line:
                        filename, count_str = line.strip().split(',', 1)
                        if count_str == "ERROR":
                            results[filename] = None
                            print(f"[ERROR] Processing failed for: {filename}")
                        else:
                            try:
                                count = int(count_str)
                                results[filename] = count
                                print(f"[SUCCESS] {filename}: {count}")
                            except ValueError:
                                print(f"[WARNING] Could not parse count for {filename}: {count_str}")
                                results[filename] = None
            else:
                print(f"[WARNING] Results file not found: {temp_results_path}")
                
        except Exception as e:
            print(f"[ERROR] Error reading results file: {e}")
        
        return results
        
    finally:
        # Clean up temporary files
        try:
            if os.path.exists(temp_macro_path):
                os.unlink(temp_macro_path)
            if os.path.exists(temp_results_path):
                os.unlink(temp_results_path)
        except Exception as e:
            print(f"[DEBUG] Error cleaning up temp files: {e}")

def select_and_count():
    """Select images and count nuclei in each using batch processing."""
    try:
        config = get_config()
        
        # Create a temporary root for the file dialog
        temp_root = tk.Tk()
        temp_root.withdraw()
        
        print("[STEP] Waiting for user to select images...")
        
        file_paths = filedialog.askopenfilenames(
            title="Select images to count nuclei",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.tif *.tiff *.bmp"), ("All files", "*.*")]
        )
        
        temp_root.destroy()
        
        if not file_paths:
            print("[INFO] No images selected.")
            return
        
        print(f"[INFO] Processing {len(file_paths)} images in batch mode...")
        
        # Process all images in one ImageJ session
        batch_results = count_multiple_nuclei_with_imagej(file_paths, config["macro_path"], config["imagej_path"])
        
        # Format results and save to history
        results = []
        successful_counts = 0
        
        for path in file_paths:
            filename = os.path.basename(path)
            count = batch_results.get(filename)
            
            if count is not None:
                save_to_history(filename, count)
                results.append(f"{filename}: {count}")
                successful_counts += 1
            else:
                results.append(f"{filename}: Error")
        
        print(f"[INFO] Batch processing complete. {successful_counts}/{len(file_paths)} successful.")
        
        # Show results
        result_text = f"Results ({successful_counts}/{len(file_paths)} successful):\n\n" + "\n".join(results)
        print("[INFO] Results:")
        print(result_text)
        
        return results
        
    except Exception as e:
        print(f"[ERROR] Error in select_and_count: {e}")

def process_folder():
    """Process all images in a folder using batch processing."""
    try:
        config = get_config()
        
        # Create a temporary root for the folder dialog
        temp_root = tk.Tk()
        temp_root.withdraw()
        
        folder_path = filedialog.askdirectory(title="Select folder with images")
        temp_root.destroy()
        
        if not folder_path:
            print("[INFO] No folder selected.")
            return
        
        # Find all image files in the folder
        image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.tif', '*.tiff', '*.bmp']
        image_files = []
        for ext in image_extensions:
            image_files.extend(glob.glob(os.path.join(folder_path, ext)))
            image_files.extend(glob.glob(os.path.join(folder_path, ext.upper())))
        
        if not image_files:
            print("[WARNING] No image files found in selected folder.")
            return
        
        print(f"[INFO] Found {len(image_files)} images in folder: {folder_path}")
        print(f"[INFO] Processing all images in batch mode...")
        
        # Process all images in one ImageJ session
        batch_results = count_multiple_nuclei_with_imagej(image_files, config["macro_path"], config["imagej_path"])
        
        # Format results and save to history
        results = []
        successful_counts = 0
        
        for img_path in image_files:
            filename = os.path.basename(img_path)
            count = batch_results.get(filename)
            
            if count is not None:
                save_to_history(filename, count)
                results.append((filename, count))
                successful_counts += 1
            else:
                results.append((filename, "Error"))
        
        print(f"[INFO] Batch processing complete. {successful_counts}/{len(image_files)} successful.")
        
        # Save results to CSV
        try:
            csv_path = os.path.join(folder_path, "nuclei_counts.csv")
            with open(csv_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Filename', 'Count'])
                writer.writerows(results)
            
            result_text = f"Batch processing complete!\n\n{successful_counts}/{len(image_files)} images processed successfully.\n\nResults saved to:\n{csv_path}"
            print("[INFO] " + result_text)
        except Exception as e:
            print(f"[ERROR] Failed to save CSV: {e}")
        
        return results
        
    except Exception as e:
        print(f"[ERROR] Error in process_folder: {e}")

def change_imagej_settings():
    """Change only the ImageJ executable setting."""
    try:
        # Load existing config or create empty one
        config = {}
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    config = json.load(f)
            except:
                pass
        
        root = tk.Tk()
        root.withdraw()
        
        print("[STEP] Waiting for user to select new ImageJ executable...")
        
        imagej_path = filedialog.askopenfilename(
            title="Select ImageJ executable (ImageJ-win64.exe)",
            filetypes=[("Executable files", "*.exe"), ("All files", "*.*")]
        )
        
        if imagej_path and os.path.exists(imagej_path):
            config["imagej_path"] = imagej_path
            print(f"[INFO] ImageJ executable updated: {imagej_path}")
            
            with open(CONFIG_FILE, "w") as f:
                json.dump(config, f, indent=2)
                
            print("[INFO] ImageJ executable updated successfully!")
        else:
            print("[INFO] ImageJ executable was not changed.")
        
        root.destroy()
        
    except Exception as e:
        print(f"[ERROR] Error changing ImageJ settings: {e}")

def change_macro_settings():
    """Change only the macro file setting."""
    try:
        # Load existing config or create empty one
        config = {}
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    config = json.load(f)
            except:
                pass
        
        root = tk.Tk()
        root.withdraw()
        
        print("[STEP] Waiting for user to select new macro file (or Cancel to use built-in)...")
        
        macro_path = filedialog.askopenfilename(
            title="Select Macro file (e.g., Counter.ijm) - Cancel to use built-in macro",
            filetypes=[("ImageJ Macro", "*.ijm"), ("All files", "*.*")]
        )
        
        if macro_path and os.path.exists(macro_path):
            config["macro_path"] = macro_path
            print(f"[INFO] Macro file updated: {macro_path}")
        else:
            config["macro_path"] = None
            print("[INFO] Will use built-in macro.")
        
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)
            
        print("[INFO] Macro settings updated successfully!")
        
        root.destroy()
        
    except Exception as e:
        print(f"[ERROR] Error changing macro settings: {e}")

def change_settings():
    """Change all settings by deleting config file."""
    try:
        if os.path.exists(CONFIG_FILE):
            os.remove(CONFIG_FILE)
            print("[INFO] Config file deleted. User will be prompted to select ImageJ and macro again.")
        
        print("[INFO] Please re-select your ImageJ executable and macro file.")
        get_config()
        
    except Exception as e:
        print(f"[ERROR] Error changing settings: {e}")

def create_gui():
    """Create the main GUI with history display."""
    try:
        root = tk.Tk()
        root.title("Nuclei Counter")
        root.geometry("650x550")
        
        # Main frame
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # History tree reference for refresh function
        history_tree = None
        
        def refresh_history():
            """Refresh the history display."""
            if history_tree is None:
                return
            try:
                # Clear existing items
                for item in history_tree.get_children():
                    history_tree.delete(item)
                
                # Load and display history
                history = get_history()
                for entry in reversed(history):  # Show newest first
                    history_tree.insert("", tk.END, values=(
                        entry.get("filename", "Unknown"), 
                        entry.get("count", "N/A"), 
                        entry.get("timestamp", "Unknown")
                    ))
            except Exception as e:
                print(f"[ERROR] Error refreshing history: {e}")
        
        # Main action buttons
        def count_and_refresh():
            try:
                select_and_count()
                refresh_history()
            except Exception as e:
                print(f"[ERROR] Error in count_and_refresh: {e}")
        
        def folder_and_refresh():
            try:
                process_folder()
                refresh_history()
            except Exception as e:
                print(f"[ERROR] Error in folder_and_refresh: {e}")
        
        btn_count = ttk.Button(button_frame, text="Select Images and Count Nuclei", command=count_and_refresh)
        btn_count.pack(fill=tk.X, pady=2)
        
        btn_folder = ttk.Button(button_frame, text="Process Entire Folder", command=folder_and_refresh)
        btn_folder.pack(fill=tk.X, pady=2)
        
        # Settings buttons
        settings_frame = ttk.Frame(button_frame)
        settings_frame.pack(fill=tk.X, pady=2)
        
        btn_imagej = ttk.Button(settings_frame, text="Change ImageJ Settings", command=change_imagej_settings, width=25)
        btn_imagej.pack(side=tk.LEFT, padx=(0, 5))
        
        btn_macro = ttk.Button(settings_frame, text="Change Macro Settings", command=change_macro_settings, width=25)
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
        
        # Initial history load
        refresh_history()
        
        print("[INFO] GUI loaded. Waiting for user action.")
        root.mainloop()
        
    except Exception as e:
        print(f"[ERROR] Error creating GUI: {e}")
        raise

if __name__ == "__main__":
    print("[INFO] Nuclei Counter started.")
    
    if len(sys.argv) == 2:
        # Command-line mode - single image
        try:
            config = get_config()
            image_path = sys.argv[1]
            
            if not os.path.exists(image_path):
                print(f"[ERROR] Image file not found: {image_path}")
                sys.exit(1)
            
            print(f"[STEP] Running in command-line mode for image: {os.path.basename(image_path)}")
            
            # Use batch processing for single image
            batch_results = count_multiple_nuclei_with_imagej([image_path], config["macro_path"], config["imagej_path"])
            filename = os.path.basename(image_path)
            count = batch_results.get(filename)
            
            if count is not None:
                # Save to history
                save_to_history(filename, count)
                print(f"[SUCCESS] Nuclei count: {count}")
            else:
                print("[ERROR] Failed to count nuclei.")
                sys.exit(1)
                
        except Exception as e:
            print(f"[ERROR] Command-line mode failed: {e}")
            sys.exit(1)
    else:
        # GUI mode
        try:
            create_gui()
        except Exception as e:
            print(f"[ERROR] GUI mode failed: {e}")
            print("[INFO] This might be due to no display available. Try running with an image path as argument for command-line mode.")
            sys.exit(1)