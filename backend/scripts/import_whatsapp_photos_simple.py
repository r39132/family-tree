#!/usr/bin/env python3
"""Simple WhatsApp photo importer - uses existing bulk upload endpoint."""

import os
import sys

# Add parent to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

print("WhatsApp import script placeholder")
print("This script will be implemented to import WhatsApp photos")
print(f"Export folder: {sys.argv[2] if len(sys.argv) > 2 else 'N/A'}")
