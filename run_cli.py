#!/usr/bin/env python3
"""
Entry point for Dimpressionist CLI interface.
"""

import os

# Set HuggingFace cache to proper system location
os.environ.setdefault('HF_HOME', '/var/lib/huggingface')

from src.cli.main import main

if __name__ == "__main__":
    main()
