# Namecheap Python SDK Examples

This directory contains example scripts demonstrating how to use the Namecheap Python SDK.

## Available Examples

- **check_domain.py**: A simple script to check domain availability
- **dns_tool.py**: A command-line tool for managing DNS records
- **utils/print_table.py**: A utility function for displaying tabular data

## Running the Examples

All example scripts use environment variables for authentication. You can set these in a `.env` file in the project root:

```
NAMECHEAP_API_USER=your_username
NAMECHEAP_API_KEY=your_api_key
NAMECHEAP_USERNAME=your_username
NAMECHEAP_CLIENT_IP=your_whitelisted_ip
NAMECHEAP_USE_SANDBOX=True  # Use False for production
```

### Check Domain Availability

This example checks if domains are available for registration:

```bash
python -m examples.check_domain example.com yourdomain.com
```

See `check_domain.py` for implementation details.

### DNS Management

This example provides a command-line interface for managing DNS records:

```bash
# List DNS records for a domain
python -m examples.dns_tool list yourdomain.com

# Add a DNS record
python -m examples.dns_tool add yourdomain.com --name www --type A --value 192.0.2.1

# Delete a DNS record
python -m examples.dns_tool delete yourdomain.com --name www --type A

# Export DNS records to JSON
python -m examples.dns_tool export yourdomain.com records.json

# Import DNS records from JSON
python -m examples.dns_tool import yourdomain.com records.json
```

See `dns_tool.py` for implementation details.

## Additional API Functions

The Namecheap Python SDK supports many other API operations that aren't covered by these examples, including:

- Listing domains in your account
- Retrieving domain information
- Registering new domains
- Renewing domains
- Setting custom nameservers

For more information on these operations, see the main README.md in the project root or the client.py file.