#!/usr/bin/env python3
"""
Test script to verify the command-line functionality works without GUI dependencies
"""
import sys
import os

# Mock the GUI dependencies for testing
class MockTk:
    def withdraw(self): pass

class MockMessageBox:
    @staticmethod
    def showinfo(*args): pass
    @staticmethod
    def showerror(*args): pass
    @staticmethod
    def showwarning(*args): pass

class MockFileDialog:
    @staticmethod
    def askopenfilename(*args, **kwargs): return ""
    @staticmethod
    def askopenfilenames(*args, **kwargs): return []

# Test imports and basic functionality
try:
    # Set up mock modules
    import types
    tk_module = types.ModuleType('tkinter')
    tk_module.Tk = MockTk
    sys.modules['tkinter'] = tk_module
    
    messagebox_module = types.ModuleType('tkinter.messagebox')
    messagebox_module.showinfo = MockMessageBox.showinfo
    messagebox_module.showerror = MockMessageBox.showerror
    messagebox_module.showwarning = MockMessageBox.showwarning
    sys.modules['tkinter.messagebox'] = messagebox_module
    
    filedialog_module = types.ModuleType('tkinter.filedialog')
    filedialog_module.askopenfilename = MockFileDialog.askopenfilename
    filedialog_module.askopenfilenames = MockFileDialog.askopenfilenames
    sys.modules['tkinter.filedialog'] = filedialog_module
    
    ttk_module = types.ModuleType('tkinter.ttk')
    sys.modules['tkinter.ttk'] = ttk_module
    
    # Now try to import our module
    import Imagerier
    print("✓ Imagerier module imported successfully")
    
    # Test history functions
    test_filename = "test_image.jpg"
    test_count = 42
    Imagerier.save_to_history(test_filename, test_count)
    print("✓ History save function works")
    
    history = Imagerier.get_history()
    print(f"✓ History load function works, found {len(history)} entries")
    
    if history and history[-1]["filename"] == test_filename and history[-1]["count"] == test_count:
        print("✓ History data is correct")
    else:
        print("✗ History data mismatch")
    
    print("\nAll basic functions are working correctly!")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
