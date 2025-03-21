#!/usr/bin/env python3
"""
A simple script to check if domains are available for registration using the Namecheap API.

Usage:
  python check_domain.py example.com domain2.com domain3.com
"""

import sys

from namecheap import NamecheapClient

from utils.print_table import print_table

# Check if the user provided any domains to check
if len(sys.argv) < 2:
    print("Please specify at least one domain to check.")
    print("Usage: python check_domain.py example.com domain2.com domain3.com")
    sys.exit(1)

# Create the Namecheap client and check domain availability
client = NamecheapClient()
result = client.domains_check(sys.argv[1:])

# Prepare table data
headers = ["Domain", "Available", "Premium", "Price"]
rows = []

for domain in result["DomainCheckResult"]:
    available = "Yes" if domain["Available"] else "No"
    premium = "Yes" if domain["IsPremiumName"] else "No"

    price = domain["PremiumRegistrationPrice"]
    price_display = "N/A" if price == 0 else f"${price:.2f}"

    rows.append([domain["Domain"], available, premium, price_display])

# Print the table
print("\nResults:")
print_table(headers, rows)
