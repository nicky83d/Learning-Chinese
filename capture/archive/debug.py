#!/usr/bin/env python3
import sys
import os

print("Starting debug script...")
sys.stdout.flush()

try:
    print("Python version:", sys.version)
    sys.stdout.flush()
    
    print("Current directory:", os.getcwd())
    sys.stdout.flush()
    
    print("Importing Flask...")
    sys.stdout.flush()
    from flask import Flask
    print("Flask imported successfully")
    sys.stdout.flush()
    
    print("About to import app_fixed...")
    sys.stdout.flush()
    from app_fixed import app, db
    print("app_fixed imported successfully")
    sys.stdout.flush()
    
    print("Pushing app context...")
    sys.stdout.flush()
    with app.app_context():
        from models import Vocabulary
        print("Models imported")
        sys.stdout.flush()
        
        count = Vocabulary.query.count()
        print(f"Total vocabulary items: {count}")
        sys.stdout.flush()
        
        # Check how many need Japanese
        without_japanese = Vocabulary.query.filter(
            (Vocabulary.japanese == '') | (Vocabulary.japanese == None)
        ).count()
        print(f"Items without Japanese: {without_japanese}")
        sys.stdout.flush()
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.stdout.flush()

print("Debug script complete")
