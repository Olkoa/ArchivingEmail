#!/usr/bin/env python
"""
Debug environment for the Okloa project.
"""

import os
import sys
import inspect
import importlib.util

def check_module(module_name, package=None):
    """Check if a module can be imported."""
    try:
        if package:
            module = __import__(module_name, fromlist=[package])
            print(f"✅ Successfully imported {module_name} from {package}")
        else:
            module = __import__(module_name)
            print(f"✅ Successfully imported {module_name}")
        return module
    except ImportError as e:
        print(f"❌ Failed to import {module_name}: {e}")
        return None

def check_directory(path):
    """Check if a directory exists and is accessible."""
    if os.path.exists(path):
        if os.path.isdir(path):
            print(f"✅ Directory exists: {path}")
            try:
                contents = os.listdir(path)
                print(f"   Contains {len(contents)} items")
            except PermissionError:
                print(f"❌ Cannot list contents of directory: {path}")
        else:
            print(f"❌ Path exists but is not a directory: {path}")
    else:
        print(f"❌ Directory doesn't exist: {path}")

def main():
    """Main function to debug the environment."""
    print("\n=== OKLOA ENVIRONMENT DEBUGGER ===\n")
    
    # Python Version
    print(f"Python version: {sys.version}")
    
    # Current Working Directory
    print(f"Current working directory: {os.getcwd()}")
    
    # Project Root
    project_root = os.path.dirname(os.path.abspath(__file__))
    print(f"Project root: {project_root}")
    
    # Check Data Directories
    data_dir = os.path.join(project_root, "data")
    raw_dir = os.path.join(data_dir, "raw")
    
    print("\n=== CHECKING DIRECTORIES ===\n")
    check_directory(data_dir)
    check_directory(raw_dir)
    
    # Try to import required modules
    print("\n=== CHECKING MODULES ===\n")
    check_module("mailbox")
    check_module("email")
    check_module("json")
    check_module("pandas")
    pytz = check_module("pytz")
    
    # Check if we can import our own modules
    print("\n=== CHECKING PROJECT MODULES ===\n")
    
    try:
        sys.path.append(project_root)
        from src.data import sample_generator
        print(f"✅ Successfully imported sample_generator from src.data")
        
        # Check if necessary functions exist
        functions = [
            "generate_email",
            "generate_mailbox",
            "save_as_mbox",
            "generate_test_mailboxes"
        ]
        
        for func_name in functions:
            if hasattr(sample_generator, func_name):
                func = getattr(sample_generator, func_name)
                argspec = inspect.getfullargspec(func)
                print(f"✅ Function '{func_name}' exists with arguments: {argspec.args}")
            else:
                print(f"❌ Function '{func_name}' not found in sample_generator")
    
    except ImportError as e:
        print(f"❌ Failed to import sample_generator: {e}")
    
    print("\nDebug complete!")

if __name__ == "__main__":
    main()