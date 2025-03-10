#!/usr/bin/env python3
import sys
import os

# Print current directory and Python path
print(f"Current directory: {os.getcwd()}")
print(f"Python path: {sys.path}")

# Try importing the problematic module
try:
    import app
    print("Successfully imported app module")
    print(f"app module location: {app.__file__}")
    
    from app import config
    print("Successfully imported app.config module")
    print(f"config module location: {config.__file__}")
except ImportError as e:
    print(f"Import error: {e}")