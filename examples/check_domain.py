#!/usr/bin/env python3
"""
A simple script to check if domains are available for registration using the Namecheap API.

Usage:
  python check_domain.py example.com domain2.com domain3.com
  python check_domain.py --debug example.com domain2.com domain3.com
"""

import sys
import argparse

from namecheap import NamecheapClient

from utils.print_table import print_table

# Parse command line arguments
parser = argparse.ArgumentParser(
    description="Check domain availability with Namecheap API")
parser.add_argument('-d', '--debug', action='store_true',
                    help='Enable debug mode')
parser.add_argument('domains', nargs='+', help='Domains to check')

args = parser.parse_args()

# Create the Namecheap client and check domain availability
client = NamecheapClient(debug=args.debug)
result = client.enhanced.domains.check_with_pricing(args.domains)

# Prepare table data
headers = ["Domain", "Available", "Premium", "Price"]
rows = []

# The result now contains a DomainCheckResult key with a list of domain results
domains = result["DomainCheckResult"]

for domain in domains:
    available = "Yes" if domain.get("Available") else "No"
    premium = "Yes" if domain.get("IsPremiumName") else "No"

    price = domain.get("Price", 0)

    # If domain is not available, show N/A
    if domain.get("Available"):
        price_display = f"${price:.2f}"
    else:
        price_display = "N/A"

    rows.append([domain.get("Domain"), available, premium, price_display])

print("\nResults:")
print_table(headers, rows)
