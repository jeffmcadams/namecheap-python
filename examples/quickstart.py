#!/usr/bin/env python3
"""Quickstart example for Namecheap SDK."""

from namecheap import Namecheap, NamecheapError

# Initialize client (auto-loads from .env or environment variables)
nc = Namecheap()

# Example 1: Check domain availability
print("🔍 Checking domain availability...")
domains_to_check = ["example123456.com", "coolstartup.io", "myawesome.site"]

# Check with pricing
results = nc.domains.check(*domains_to_check, include_pricing=True)

for domain in results:
    if domain.available:
        if domain.price:
            price_info = f"${domain.price:.2f}"
            if domain.total_price and domain.total_price != domain.price:
                price_info += f" (${domain.total_price:.2f} with fees)"
        else:
            price_info = "price not available"
        print(f"✅ {domain.domain} is available for {price_info}")
    else:
        print(f"❌ {domain.domain} is taken")

print()

# Example 2: List your domains
print("📋 Your domains:")
my_domains = []
try:
    my_domains = nc.domains.list()
    if my_domains:
        for domain in my_domains:
            print(f"  • {domain.name} (expires: {domain.expires.strftime('%Y-%m-%d')})")
    else:
        print("  No domains found in your account")
except NamecheapError as e:
    print(f"  Error: {e}")

print()

# Example 3: DNS management with builder pattern
print("🌐 DNS Management example:")
try:
    # Get current DNS records for a domain
    # Use the first domain from your account, or specify one
    domain_name = my_domains[0].name if my_domains else "example.com"  # Replace with your domain
    print(f"Current DNS records for {domain_name}:")

    records = nc.dns.get(domain_name)
    for record in records:
        print(f"  {record.type:6} {record.name:20} -> {record.value}")

    # Example of setting new records using the builder
    print("\n  Example: To update DNS records, you would use:")
    print("  nc.dns.set(domain_name,")
    print("      nc.dns.builder()")
    print("      .a('@', '192.0.2.1')")
    print("      .a('www', '192.0.2.1')")
    print("      .mx('@', 'mail.example.com', priority=10)")
    print("      .txt('@', 'v=spf1 include:_spf.google.com ~all')")
    print("  )")

    # Uncomment to actually set records (DESTRUCTIVE - will replace ALL records!)
    # response = input("\n  ⚠️  Replace ALL DNS records? (yes/no): ")
    # if response.lower() == 'yes':
    #     nc.dns.set(domain_name, ...)
    #     print("  ✅ DNS records updated!")

except NamecheapError as e:
    print(f"  Note: {e.message}")

print()

# Example 4: Using context manager
print("🔒 Using context manager:")
with Namecheap() as nc:
    # The client will automatically close connections when done
    available = nc.domains.check("python-namecheap.com")
    print(f"  python-namecheap.com available: {available[0].available}")

print("\n✨ Done! Check out the examples folder for more advanced usage.")
