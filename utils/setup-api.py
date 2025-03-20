#!/usr/bin/env python3
"""
Interactive setup script for Namecheap API credentials.
"""

from namecheap.utils import setup_interactive

if __name__ == "__main__":
    print("Welcome to the Namecheap API Setup Wizard")
    print("========================================")
    print("This script will help you configure your Namecheap API credentials.")
    print("You will need:")
    print("1. Your Namecheap account username")
    print(
        "2. Your API key from Namecheap (https://ap.www.namecheap.com/settings/tools/apiaccess/)"
    )
    print("3. Your IP address that is whitelisted in Namecheap API settings")
    print("\nThis setup will create or update your .env file with these credentials.")
    print("\nPress Enter to continue...")
    input()

    setup_interactive()
