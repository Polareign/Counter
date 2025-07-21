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
                "use_watershed": True,
                "disable_macro": False
            })
        except:
            pass
    
    # Return defaults
    return {
        "use_watershed": True,
        "disable_macro": False
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

def open_protocol_help():
    """Open protocol/help window with step-by-step instructions."""
    protocol_window = tk.Toplevel()
    protocol_window.title("📋 Nuclei Counter Protocol")
    protocol_window.geometry("800x700")
    protocol_window.minsize(700, 600)
    protocol_window.grab_set()  # Make modal
    
    # Center the window
    protocol_window.transient()
    
    # Main frame with scrollbar
    main_frame = ttk.Frame(protocol_window)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    
    # Canvas for scrolling
    canvas = tk.Canvas(main_frame, bg='white')
    scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)
    
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    # Title
    title_label = ttk.Label(scrollable_frame, text="📋 Nuclei Counter Protocol", font=("Arial", 16, "bold"))
    title_label.pack(pady=(0, 20))
    
    # Protocol content
    protocol_text = """
🔬 NUCLEI COUNTER - PROTOCOL

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. FIRST TIME SETUP
   • When you first run the program, it will ask you to select:
     - ImageJ executable (usually ImageJ-win64.exe)
     - Macro file (optional - Cancel to use built-in processing)
   • These settings are saved and can be changed later

2. PREPARE YOUR IMAGES
   • Supported formats: .jpg, .jpeg
   • Images should show nuclei clearly

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎛️ PROCESSING OPTIONS

KEEP IMAGES OPEN
   ✅ Checked: ImageJ stays open with processed images for inspection
   ❌ Unchecked: ImageJ closes automatically after processing (faster)

WATERSHED SEGMENTATION
   ✅ Enabled: Separates touching nuclei (recommended)
   ❌ Disabled: Used when nuclei are not bunched together

MACRO PROCESSING
   ✅ Enabled: Uses your custom macro file (if selected)
   ❌ Disabled: Forces built-in processing (overrides custom macro)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📁 PROCESSING WORKFLOW

1. CLICK "SELECT IMAGES AND COUNT NUCLEI"
   • File dialog opens - select one or more images
   • Ctrl+click to select multiple files
   • All selected images will be processed in one batch

2. AUTOMATIC PROCESSING
   • ImageJ opens and processes each image
   • Built-in processing steps:
     - Convert to 8-bit
     - Apply median filter (noise reduction)
     - Auto threshold (Otsu method)
     - Convert to binary mask
     - Invert colors
     - Watershed segmentation (if enabled)
     - Analyze particles (size: 450-25000 pixels)

3. RESULTS
   • Counts appear in the history table
   • Results are automatically saved
   • ImageJ may stay open for inspection (if option is checked)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔧 TROUBLESHOOTING

IMAGEJ NOT OPENING
   • Check that ImageJ path is correct
   • Make sure ImageJ is properly installed
   • Try running ImageJ manually first

LOW/HIGH COUNTS
   • Check image quality and contrast
   • Ensure nuclei are clearly visible
   • Consider adjusting image brightness/contrast before processing
   • Watershed may help separate touching nuclei

ERROR MESSAGES
   • Check console output for detailed error information
   • Ensure image files are not corrupted
   • Make sure ImageJ has sufficient memory for large images

CUSTOM MACRO ISSUES
   • Test your macro in ImageJ manually first
   • Ensure macro doesn't contain interactive dialogs
   • Remove any "open()" or "print()" statements

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Version: Nuclei Counter v3.11
Built-in processing: 8-bit → Median filter → Otsu threshold → Mask → Watershed → Particle analysis (450-25000 pixels)
"""

    # Create text widget with proper formatting
    text_widget = tk.Text(scrollable_frame, wrap=tk.WORD, font=("Consolas", 10), 
                         bg='white', fg='black', padx=20, pady=20)
    text_widget.insert(tk.END, protocol_text)
    text_widget.configure(state=tk.DISABLED)  # Make read-only
    text_widget.pack(fill=tk.BOTH, expand=True)
    
    # Pack canvas and scrollbar
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    # Close button
    close_frame = ttk.Frame(protocol_window)
    close_frame.pack(fill=tk.X, padx=20, pady=10)
    
    ttk.Button(close_frame, text="✅ Close Protocol", 
              command=protocol_window.destroy).pack(side=tk.RIGHT)
    
    # Bind mousewheel to canvas
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    canvas.bind("<MouseWheel>", _on_mousewheel)

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

def count_multiple_nuclei_with_imagej(image_paths, macro_path, imagej_path, keep_images_open=False, use_watershed=True, disable_macro=False):
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
    if macro_path and os.path.exists(macro_path) and not disable_macro:
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
            # Build watershed step
            watershed_step = 'run("Watershed");' if use_watershed else '// Watershed disabled'
            processing_steps = f'''run("8-bit");
run("Median...", "radius=3");
setAutoThreshold("Otsu");
run("Convert to Mask");
run("Invert");
{watershed_step}
run("Analyze Particles...", "size=450-25000 circularity=0.00-1.00 show=Nothing clear");'''
    else:
        # Use built-in processing steps with updated particle size range
        print("[INFO] Using built-in processing steps")
        if disable_macro:
            print("[INFO] Custom macro disabled by user setting")
        
        # Build watershed step
        watershed_step = 'run("Watershed");' if use_watershed else '// Watershed disabled'
        processing_steps = f'''run("8-bit");
run("Median...", "radius=3");
setAutoThreshold("Otsu");
run("Convert to Mask");
run("Invert");
{watershed_step}
run("Analyze Particles...", "size=450-25000 circularity=0.00-1.00 show=Nothing clear");'''
    
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
        print(f"[INFO] Use watershed: {use_watershed}")
        print(f"[INFO] Disable macro: {disable_macro}")
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

def select_and_count(keep_images_open=False, use_watershed=True, disable_macro=False):
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
        batch_results = count_multiple_nuclei_with_imagej(file_paths, config["macro_path"], config["imagej_path"], keep_images_open, use_watershed, disable_macro)
        
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
    """Create the main GUI with simplified controls and protocol help."""
    try:
        root = tk.Tk()
        root.title("Nuclei Counter v3.11")
        root.geometry("700x700")
        root.minsize(600, 600)
        
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Main frame
        main_frame = ttk.Frame(root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="🔬 Nuclei Counter v3.11", font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Processing options variables
        keep_images_var = tk.BooleanVar()
        keep_images_var.set(False)  # Default to closing images
        
        use_watershed_var = tk.BooleanVar()
        use_watershed_var.set(True)  # Default to using watershed
        
        disable_macro_var = tk.BooleanVar()
        disable_macro_var.set(False)  # Default to using macro if available
        
        # Options frame
        options_frame = ttk.LabelFrame(main_frame, text="Processing Options", padding="10")
        options_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Keep images open option
        keep_images_check = ttk.Checkbutton(
            options_frame, 
            text="🖼️ Keep images open in ImageJ after processing", 
            variable=keep_images_var
        )
        keep_images_check.pack(anchor='w', pady=2)
        create_tooltip(keep_images_check, "When enabled, ImageJ will remain open with all processed images for manual inspection and verification.")
        
        # Watershed option
        watershed_check = ttk.Checkbutton(
            options_frame, 
            text="🌊 Enable watershed segmentation (separates touching nuclei)", 
            variable=use_watershed_var
        )
        watershed_check.pack(anchor='w', pady=2)
        create_tooltip(watershed_check, "Watershed helps separate touching or overlapping nuclei. Disable for faster processing if nuclei are well-separated.")
        
        # Disable macro option
        disable_macro_check = ttk.Checkbutton(
            options_frame, 
            text="🚫 Disable custom macro (force built-in processing)", 
            variable=disable_macro_var
        )
        disable_macro_check.pack(anchor='w', pady=2)
        create_tooltip(disable_macro_check, "When enabled, always uses built-in processing even if a custom macro is selected.")
        
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
                use_watershed = use_watershed_var.get()
                disable_macro = disable_macro_var.get()
                
                # Save current settings
                settings = {
                    "use_watershed": use_watershed,
                    "disable_macro": disable_macro
                }
                save_processing_settings(settings)
                
                select_and_count(keep_images_open=keep_open, use_watershed=use_watershed, disable_macro=disable_macro)
                refresh_history()
                
                # Update status based on settings
                status_text = "Processing complete! "
                if keep_open:
                    status_text += "ImageJ remains open with images."
                else:
                    status_text += "ImageJ closed after processing."
                status_label.config(text=status_text)
                    
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
        
        btn_protocol = ttk.Button(settings_frame, text="📋 Protocol & Help", 
                                 command=open_protocol_help)
        btn_protocol.pack(side=tk.LEFT)
        create_tooltip(btn_protocol, "Open step-by-step protocol and troubleshooting guide")
        
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
        
        # Load saved settings
        settings = get_processing_settings()
        use_watershed_var.set(settings.get("use_watershed", True))
        disable_macro_var.set(settings.get("disable_macro", False))
        
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
        
        print("[INFO] Nuclei Counter v3.11 with updated protocol loaded. Waiting for user action.")
        root.mainloop()
        
    except Exception as e:
        print(f"[ERROR] Error creating GUI: {e}")
        raise

if __name__ == "__main__":
    print("[INFO] Nuclei Counter v3.11 started.")
    
    if len(sys.argv) == 2:
        # Command-line mode - single image
        try:
            config = get_config()
            image_path = sys.argv[1]
            
            if not os.path.exists(image_path):
                print(f"[ERROR] Image file not found: {image_path}")
                sys.exit(1)
            
            print(f"[STEP] Running in command-line mode for image: {os.path.basename(image_path)}")
            
            # Use batch processing for single image (default: close images, use watershed, don't disable macro)
            batch_results = count_multiple_nuclei_with_imagej([image_path], config["macro_path"], config["imagej_path"], keep_images_open=False, use_watershed=True, disable_macro=False)
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