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
result = client.enhanced.domains.check_with_pricing(sys.argv[1:])

# Prepare table data
headers = ["Domain", "Available", "Premium", "Price"]
rows = []

# Handle the standard API response format
if isinstance(result, dict) and "DomainCheckResult" in result:
    domains = result["DomainCheckResult"]
    if not isinstance(domains, list):
        domains = [domains]  # Handle single domain case

    for domain in domains:
        available = "Yes" if domain.get("Available") else "No"
        premium = "Yes" if domain.get("IsPremiumName") else "No"

        price = domain.get("Price", 0)
        price_display = "N/A" if price == 0 else f"${price:.2f}"

        rows.append([domain.get("Domain"), available, premium, price_display])

# Print the table
print("\nResults:")
print_table(headers, rows)
