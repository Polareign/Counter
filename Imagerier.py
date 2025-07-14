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

def delete_history_entry(filename, timestamp):
    """Delete a specific entry from history."""
    try:
        history = get_history()
        # Find and remove the entry
        history = [entry for entry in history if not (entry.get("filename") == filename and entry.get("timestamp") == timestamp)]
        
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=2)
        print(f"[INFO] Deleted from history: {filename} - {timestamp}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to delete from history: {e}")
        return False

def clear_all_history():
    """Clear all history entries."""
    try:
        with open(HISTORY_FILE, "w") as f:
            json.dump([], f, indent=2)
        print("[INFO] All history cleared")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to clear history: {e}")
        return False

def get_processing_settings():
    """Get processing settings from config or return defaults."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
            return config.get("processing_settings", {
                "particle_size_min": 600,
                "particle_size_max": 5000,
                "circularity_min": 0.00,
                "circularity_max": 1.00,
                "median_radius": 3,
                "threshold_method": "Otsu"
            })
        except:
            pass
    
    # Return defaults
    return {
        "particle_size_min": 600,
        "particle_size_max": 5000,
        "circularity_min": 0.00,
        "circularity_max": 1.00,
        "median_radius": 3,
        "threshold_method": "Otsu"
    }

def save_processing_settings(settings):
    """Save processing settings to config."""
    try:
        config = {}
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    config = json.load(f)
            except:
                pass
        
        config["processing_settings"] = settings
        
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)
        print(f"[INFO] Processing settings saved: {settings}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to save processing settings: {e}")
        return False

def open_processing_settings():
    """Open processing settings dialog."""
    settings = get_processing_settings()
    
    # Create settings window
    settings_window = tk.Toplevel()
    settings_window.title("⚙️ Processing Settings")
    settings_window.geometry("500x600")
    settings_window.minsize(450, 550)
    settings_window.grab_set()  # Make modal
    
    # Center the window
    settings_window.transient()
    
    # Main frame
    main_frame = ttk.Frame(settings_window, padding="20")
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # Title
    title_label = ttk.Label(main_frame, text="⚙️ Processing Settings", font=("Arial", 14, "bold"))
    title_label.pack(pady=(0, 20))
    
    # Particle Size Settings
    size_frame = ttk.LabelFrame(main_frame, text="Particle Size (pixels)", padding="10")
    size_frame.pack(fill=tk.X, pady=(0, 15))
    
    ttk.Label(size_frame, text="Minimum Size:").grid(row=0, column=0, sticky=tk.W, pady=5)
    size_min_var = tk.IntVar(value=settings["particle_size_min"])
    size_min_spin = ttk.Spinbox(size_frame, from_=50, to=10000, textvariable=size_min_var, width=10)
    size_min_spin.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=5)
    
    ttk.Label(size_frame, text="Maximum Size:").grid(row=1, column=0, sticky=tk.W, pady=5)
    size_max_var = tk.IntVar(value=settings["particle_size_max"])
    size_max_spin = ttk.Spinbox(size_frame, from_=100, to=50000, textvariable=size_max_var, width=10)
    size_max_spin.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=5)
    
    # Circularity Settings
    circ_frame = ttk.LabelFrame(main_frame, text="Circularity (0.0 - 1.0)", padding="10")
    circ_frame.pack(fill=tk.X, pady=(0, 15))
    
    ttk.Label(circ_frame, text="Minimum Circularity:").grid(row=0, column=0, sticky=tk.W, pady=5)
    circ_min_var = tk.DoubleVar(value=settings["circularity_min"])
    circ_min_spin = ttk.Spinbox(circ_frame, from_=0.0, to=1.0, increment=0.01, textvariable=circ_min_var, width=10)
    circ_min_spin.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=5)
    
    ttk.Label(circ_frame, text="Maximum Circularity:").grid(row=1, column=0, sticky=tk.W, pady=5)
    circ_max_var = tk.DoubleVar(value=settings["circularity_max"])
    circ_max_spin = ttk.Spinbox(circ_frame, from_=0.0, to=1.0, increment=0.01, textvariable=circ_max_var, width=10)
    circ_max_spin.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=5)
    
    # Preprocessing Settings
    preproc_frame = ttk.LabelFrame(main_frame, text="Preprocessing", padding="10")
    preproc_frame.pack(fill=tk.X, pady=(0, 15))
    
    ttk.Label(preproc_frame, text="Median Filter Radius:").grid(row=0, column=0, sticky=tk.W, pady=5)
    median_var = tk.IntVar(value=settings["median_radius"])
    median_spin = ttk.Spinbox(preproc_frame, from_=1, to=10, textvariable=median_var, width=10)
    median_spin.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=5)
    
    ttk.Label(preproc_frame, text="Threshold Method:").grid(row=1, column=0, sticky=tk.W, pady=5)
    threshold_var = tk.StringVar(value=settings["threshold_method"])
    threshold_combo = ttk.Combobox(preproc_frame, textvariable=threshold_var, width=12,
                                   values=["Otsu", "Triangle", "Huang", "Li", "MaxEntropy", "Mean", "MinError"])
    threshold_combo.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=5)
    threshold_combo.state(['readonly'])
    
    # Current Settings Preview
    preview_frame = ttk.LabelFrame(main_frame, text="Current Settings Preview", padding="10")
    preview_frame.pack(fill=tk.X, pady=(0, 15))
    
    preview_text = tk.Text(preview_frame, height=6, width=50, wrap=tk.WORD)
    preview_text.pack(fill=tk.BOTH, expand=True)
    
    def update_preview():
        preview_text.delete(1.0, tk.END)
        preview_text.insert(tk.END, f"Particle Size: {size_min_var.get()} - {size_max_var.get()} pixels\n")
        preview_text.insert(tk.END, f"Circularity: {circ_min_var.get():.2f} - {circ_max_var.get():.2f}\n")
        preview_text.insert(tk.END, f"Median Filter: {median_var.get()} pixels\n")
        preview_text.insert(tk.END, f"Threshold: {threshold_var.get()}\n\n")
        preview_text.insert(tk.END, "These settings will be applied to the built-in macro processing.")
    
    # Update preview initially and bind to changes
    update_preview()
    for var in [size_min_var, size_max_var, circ_min_var, circ_max_var, median_var]:
        var.trace('w', lambda *args: update_preview())
    threshold_var.trace('w', lambda *args: update_preview())
    
    # Buttons
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(fill=tk.X, pady=(15, 0))
    
    def reset_defaults():
        """Reset all settings to defaults."""
        defaults = {
            "particle_size_min": 600,
            "particle_size_max": 5000,
            "circularity_min": 0.00,
            "circularity_max": 1.00,
            "median_radius": 3,
            "threshold_method": "Otsu"
        }
        size_min_var.set(defaults["particle_size_min"])
        size_max_var.set(defaults["particle_size_max"])
        circ_min_var.set(defaults["circularity_min"])
        circ_max_var.set(defaults["circularity_max"])
        median_var.set(defaults["median_radius"])
        threshold_var.set(defaults["threshold_method"])
        update_preview()
    
    def save_and_close():
        """Save settings and close window."""
        new_settings = {
            "particle_size_min": size_min_var.get(),
            "particle_size_max": size_max_var.get(),
            "circularity_min": circ_min_var.get(),
            "circularity_max": circ_max_var.get(),
            "median_radius": median_var.get(),
            "threshold_method": threshold_var.get()
        }
        
        if save_processing_settings(new_settings):
            messagebox.showinfo("Success", "Processing settings saved successfully!")
            settings_window.destroy()
        else:
            messagebox.showerror("Error", "Failed to save processing settings.")
    
    def cancel():
        """Close without saving."""
        settings_window.destroy()
    
    ttk.Button(button_frame, text="🔄 Reset to Defaults", command=reset_defaults).pack(side=tk.LEFT, padx=(0, 10))
    ttk.Button(button_frame, text="❌ Cancel", command=cancel).pack(side=tk.RIGHT, padx=(10, 0))
    ttk.Button(button_frame, text="✅ Save Settings", command=save_and_close).pack(side=tk.RIGHT)

def create_tooltip(widget, text):
    """Create a tooltip for a widget."""
    def show_tooltip(event):
        tooltip = tk.Toplevel()
        tooltip.wm_overrideredirect(True)
        tooltip.wm_geometry(f"+{event.x_root + 10}+{event.y_root + 10}")
        
        label = tk.Label(tooltip, text=text, background="lightyellow", 
                        relief="solid", borderwidth=1, font=("Arial", 9))
        label.pack()
        
        def hide_tooltip():
            tooltip.destroy()
        
        tooltip.after(3000, hide_tooltip)  # Hide after 3 seconds
        widget.tooltip = tooltip
    
    def hide_tooltip(event):
        if hasattr(widget, 'tooltip'):
            widget.tooltip.destroy()
    
    widget.bind('<Enter>', show_tooltip)
    widget.bind('<Leave>', hide_tooltip)

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

def count_multiple_nuclei_with_imagej(image_paths, macro_path, imagej_path, keep_images_open=False):
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
    
    # Get processing settings
    settings = get_processing_settings()
    
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
            print("[INFO] Using built-in processing steps with custom settings")
            processing_steps = f'''run("8-bit");
run("Median...", "radius={settings['median_radius']}");
setAutoThreshold("{settings['threshold_method']}");
run("Convert to Mask");
run("Invert");
run("Watershed");
run("Analyze Particles...", "size={settings['particle_size_min']}-{settings['particle_size_max']} circularity={settings['circularity_min']:.2f}-{settings['circularity_max']:.2f} show=Nothing clear");'''
    else:
        # Use built-in processing steps with custom settings
        print("[INFO] Using built-in processing steps with custom settings")
        processing_steps = f'''run("8-bit");
run("Median...", "radius={settings['median_radius']}");
setAutoThreshold("{settings['threshold_method']}");
run("Convert to Mask");
run("Invert");
run("Watershed");
run("Analyze Particles...", "size={settings['particle_size_min']}-{settings['particle_size_max']} circularity={settings['circularity_min']:.2f}-{settings['circularity_max']:.2f} show=Nothing clear");'''
    
    # Create batch macro that processes all images
    batch_mode = "true" if not keep_images_open else "false"
    close_images = "run(\"Close All\");" if not keep_images_open else "// Images kept open for inspection"
    quit_imagej = "run(\"Quit\");" if not keep_images_open else "// ImageJ kept open for inspection"
    
    batch_macro_content = f'''
// Batch macro to process multiple images in one session
setBatchMode({batch_mode});

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

{close_images}

'''
    
    # Add macro ending
    completion_message = "Images kept open for inspection!" if keep_images_open else "Processing complete!"
    batch_macro_content += f'''
setBatchMode(false);
print("Batch processing complete! {completion_message}");
{quit_imagej}
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
        print(f"[INFO] Keep images open: {keep_images_open}")
        print(f"[INFO] Processing settings: {settings}")
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
        if keep_images_open:
            print(f"[INFO] ImageJ remains open with processed images for inspection.")
        else:
            print(f"[INFO] ImageJ closed after processing.")
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

def select_and_count(keep_images_open=False):
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
        batch_results = count_multiple_nuclei_with_imagej(file_paths, config["macro_path"], config["imagej_path"], keep_images_open)
        
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

def create_gui():
    """Create the main GUI with history display, toggle, processing settings, and tooltips."""
    try:
        root = tk.Tk()
        root.title("Nuclei Counter v2.0")
        root.geometry("700x700")
        root.minsize(600, 600)
        
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Main frame
        main_frame = ttk.Frame(root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="🔬 Nuclei Counter", font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Toggle for keeping images open
        keep_images_var = tk.BooleanVar()
        keep_images_var.set(False)  # Default to closing images
        
        # Options frame
        options_frame = ttk.LabelFrame(main_frame, text="Processing Options", padding="10")
        options_frame.pack(fill=tk.X, pady=(0, 10))
        
        keep_images_check = ttk.Checkbutton(
            options_frame, 
            text="🖼️ Keep images open in ImageJ after processing", 
            variable=keep_images_var
        )
        keep_images_check.pack(anchor='w')
        create_tooltip(keep_images_check, "When enabled, ImageJ will remain open with all processed images for manual inspection and verification.")
        
        # Info label
        info_label = ttk.Label(
            options_frame, 
            text="When enabled, ImageJ will remain open with all processed images for inspection.",
            font=("Arial", 9),
            foreground="gray"
        )
        info_label.pack(anchor='w', pady=(5, 0))
        
        # Button frame
        button_frame = ttk.LabelFrame(main_frame, text="Actions", padding="10")
        button_frame.pack(fill=tk.X, pady=(0, 15))
        
        # History tree reference for refresh function
        history_tree = None
        status_label = None
        
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
                for i, entry in enumerate(reversed(history)):  # Show newest first
                    tag = 'evenrow' if i % 2 == 0 else 'oddrow'
                    history_tree.insert("", tk.END, values=(
                        entry.get("filename", "Unknown"), 
                        entry.get("count", "N/A"), 
                        entry.get("timestamp", "Unknown")
                    ), tags=(tag,))
                
                # Update status
                if status_label:
                    status_label.config(text=f"History: {len(history)} entries")
                
            except Exception as e:
                print(f"[ERROR] Error refreshing history: {e}")
        
        def delete_selected_entry():
            """Delete selected history entry."""
            if history_tree is None:
                return
                
            selection = history_tree.selection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select an entry to delete.")
                return
            
            item = selection[0]
            values = history_tree.item(item, 'values')
            filename = values[0]
            timestamp = values[2]
            
            # Confirm deletion
            if messagebox.askyesno("Confirm Delete", f"Delete entry for '{filename}' from {timestamp}?"):
                if delete_history_entry(filename, timestamp):
                    refresh_history()
                    messagebox.showinfo("Success", "Entry deleted successfully.")
                else:
                    messagebox.showerror("Error", "Failed to delete entry.")
        
        def clear_all_entries():
            """Clear all history entries."""
            if messagebox.askyesno("Confirm Clear All", "Are you sure you want to clear ALL history entries?\n\nThis cannot be undone."):
                if clear_all_history():
                    refresh_history()
                    messagebox.showinfo("Success", "All history cleared.")
                else:
                    messagebox.showerror("Error", "Failed to clear history.")
        
        # Main action buttons
        def count_and_refresh():
            try:
                keep_open = keep_images_var.get()
                select_and_count(keep_images_open=keep_open)
                refresh_history()
                
                # Update status based on toggle
                if keep_open:
                    status_label.config(text="Processing complete! ImageJ remains open with images.")
                else:
                    status_label.config(text="Processing complete! ImageJ closed after processing.")
                    
            except Exception as e:
                print(f"[ERROR] Error in count_and_refresh: {e}")
                messagebox.showerror("Error", f"Processing failed: {e}")
                if status_label:
                    status_label.config(text="Error during processing.")
        
        # Main processing button (larger and prominent)
        btn_count = ttk.Button(button_frame, text="📁 Select Images and Count Nuclei", 
                              command=count_and_refresh)
        btn_count.pack(fill=tk.X, pady=(0, 10))
        create_tooltip(btn_count, "Click to select one or more images and automatically count nuclei in each image using ImageJ.")
        
        # Settings buttons frame
        settings_frame = ttk.Frame(button_frame)
        settings_frame.pack(fill=tk.X, pady=(0, 5))
        
        btn_imagej = ttk.Button(settings_frame, text="⚙️ Change ImageJ Path", 
                               command=change_imagej_settings)
        btn_imagej.pack(side=tk.LEFT, padx=(0, 5))
        create_tooltip(btn_imagej, "Change the path to your ImageJ executable (ImageJ-win64.exe)")
        
        btn_macro = ttk.Button(settings_frame, text="🔧 Change Macro Settings", 
                              command=change_macro_settings)
        btn_macro.pack(side=tk.LEFT, padx=(0, 5))
        create_tooltip(btn_macro, "Select a custom ImageJ macro file or use the built-in processing")
        
        btn_processing = ttk.Button(settings_frame, text="🎛️ Processing Settings", 
                                   command=open_processing_settings)
        btn_processing.pack(side=tk.LEFT)
        create_tooltip(btn_processing, "Adjust particle size, circularity, and other processing parameters")
        
        # History section
        history_frame = ttk.LabelFrame(main_frame, text="Processing History", padding="10")
        history_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # History controls
        history_controls = ttk.Frame(history_frame)
        history_controls.pack(fill=tk.X, pady=(0, 10))
        
        btn_delete = ttk.Button(history_controls, text="🗑️ Delete Selected", 
                               command=delete_selected_entry)
        btn_delete.pack(side=tk.LEFT, padx=(0, 10))
        create_tooltip(btn_delete, "Delete the selected history entry permanently")
        
        btn_clear_all = ttk.Button(history_controls, text="🧹 Clear All History", 
                                  command=clear_all_entries)
        btn_clear_all.pack(side=tk.LEFT, padx=(0, 10))
        create_tooltip(btn_clear_all, "Clear all history entries (cannot be undone)")
        
        btn_refresh = ttk.Button(history_controls, text="🔄 Refresh", 
                                command=refresh_history)
        btn_refresh.pack(side=tk.LEFT)
        create_tooltip(btn_refresh, "Refresh the history display")
        
        # Treeview for history
        tree_frame = ttk.Frame(history_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("File", "Count", "Timestamp")
        history_tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
        
        # Configure columns
        history_tree.heading("File", text="📄 File Name")
        history_tree.heading("Count", text="🔢 Count")
        history_tree.heading("Timestamp", text="📅 Date/Time")
        
        history_tree.column("File", width=300)
        history_tree.column("Count", width=100)
        history_tree.column("Timestamp", width=200)
        
        # Add alternating row colors
        history_tree.tag_configure('oddrow', background='#f0f0f0')
        history_tree.tag_configure('evenrow', background='white')
        
        # Scrollbar for history
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=history_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        history_tree.configure(yscrollcommand=scrollbar.set)
        history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        create_tooltip(history_tree, "Double-click an entry to view details, or select and use buttons above to delete")
        
        # Status bar
        status_label = ttk.Label(main_frame, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        status_label.pack(fill=tk.X, pady=(10, 0))
        
        # Initial history load
        refresh_history()
        
        # Bind double-click to show details
        def on_double_click(event):
            selection = history_tree.selection()
            if selection:
                item = selection[0]
                values = history_tree.item(item, 'values')
                messagebox.showinfo("Entry Details", 
                                   f"File: {values[0]}\nCount: {values[1]}\nTimestamp: {values[2]}")
        
        history_tree.bind('<Double-1>', on_double_click)
        
        print("[INFO] Enhanced GUI with processing settings and tooltips loaded. Waiting for user action.")
        root.mainloop()
        
    except Exception as e:
        print(f"[ERROR] Error creating GUI: {e}")
        raise

if __name__ == "__main__":
    print("[INFO] Nuclei Counter v2.0 started.")
    
    if len(sys.argv) == 2:
        # Command-line mode - single image
        try:
            config = get_config()
            image_path = sys.argv[1]
            
            if not os.path.exists(image_path):
                print(f"[ERROR] Image file not found: {image_path}")
                sys.exit(1)
            
            print(f"[STEP] Running in command-line mode for image: {os.path.basename(image_path)}")
            
            # Use batch processing for single image (default: close images)
            batch_results = count_multiple_nuclei_with_imagej([image_path], config["macro_path"], config["imagej_path"], keep_images_open=False)
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