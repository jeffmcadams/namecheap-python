#!/usr/bin/env python3
"""
Simple script to test the Namecheap API connection.
"""

from namecheap.utils import test_api_connection

if __name__ == "__main__":
    # Will use environment variables for sandbox/production setting
    test_api_connection()
