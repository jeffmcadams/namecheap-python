# Namecheap Python SDK

A Python wrapper for the Namecheap API that allows developers to interact programmatically with Namecheap's domain registration and management services.

I needed an MCP, so I needed an API, I checked and the previous python API SDK for Namecheap was abandoned, so I went ahead and did this one.

## Project Focus

This SDK currently focuses on domain management functionality of the Namecheap API, including:
- Domain availability checking
- Domain registration and renewal
- DNS record management
- Domain contact information
- Domain information retrieval

Other Namecheap API features (like SSL certificates, email services, etc.) may be implemented in the future, but they are not currently a priority.

## Project Goals

- Provide a simple, intuitive Python interface to the Namecheap API
- Support domain management endpoints in the Namecheap API
- Handle authentication and request formatting automatically
- Return responses in Pythonic data structures (not raw XML)
- Comprehensive error handling with detailed error messages
- Well-documented with examples for common operations

## Requirements

- Python 3.7+
- A Namecheap account with API access enabled
- API key from your Namecheap account
- Whitelisted IP address(es) that will make API requests

## Installation

```bash
pip install namecheap-python
```

### For Developers

This project uses Poetry for dependency management and packaging:

```bash
# Install poetry
curl -sSL https://install.python-poetry.org | python3 -

# Setup development environment
poetry install

# Run tests
poetry run pytest

# Build package
poetry build

# Publish to PyPI
poetry publish
```

## Authentication

To use the Namecheap API, you need:

1. A Namecheap account
2. API access enabled on your account (do this at https://ap.www.namecheap.com/settings/tools/apiaccess/)
3. An API key generated from your Namecheap dashboard
4. Your client IP address(es) whitelisted

The Namecheap API uses the following authentication parameters:
- `ApiUser`: Your Namecheap username
- `ApiKey`: Your API key
- `UserName`: Your Namecheap username (typically the same as ApiUser)
- `ClientIp`: The whitelisted IP address making the request

## Usage

### Basic Setup

```python
from namecheap import NamecheapClient, NamecheapException

# Method 1: Initialize with explicit credentials
client = NamecheapClient(
    api_user="your_username",
    api_key="your_api_key",
    username="your_username",
    client_ip="your_whitelisted_ip",
    sandbox=True,  # Use False for production
    debug=False    # Set to True for debugging request and response details
)

# Method 2: Initialize using environment variables (recommended)
# Set these in your environment or .env file:
#   NAMECHEAP_API_USER=your_username
#   NAMECHEAP_API_KEY=your_api_key
#   NAMECHEAP_USERNAME=your_username
#   NAMECHEAP_CLIENT_IP=your_whitelisted_ip
#   NAMECHEAP_USE_SANDBOX=True

client = NamecheapClient()  # Automatically loads credentials from environment
```

### Check Domain Availability

```python
try:
    # Check multiple domains at once (up to 50)
    domains_to_check = ["example.com", "example.net", "example.org"]
    result = client.domains_check(domains_to_check)
    
    # Process results
    for domain in result.get("DomainCheckResult", []):
        print(f"{domain['Domain']}: {'Available' if domain['Available'] else 'Not available'}")
        if domain['IsPremiumName']:
            print(f"  Premium Domain - Price: {domain['PremiumRegistrationPrice']}")
except NamecheapException as e:
    print(f"API Error: {e}")
```

### Example Output

Running the check_domain.py example produces output like the following:

```
Checking availability for: example.com, something123unique.com

Results:
------------------------------------------------------------
Domain                         Available    Premium    Price
------------------------------------------------------------
example.com                    No           No         N/A
something123unique.com         Yes          No         N/A
```

### List Your Domains

```python
try:
    # Get list of domains in your account
    result = client.domains_get_list(
        page=1,
        page_size=20,
        sort_by="NAME",
        list_type="ALL"
    )
    
    # Process domain list
    domains = result.get("DomainGetListResult", {}).get("Domain", [])
    
    for domain in domains:
        print(f"Domain: {domain.get('Name')}")
        print(f"  Expires: {domain.get('Expires')}")
except NamecheapException as e:
    print(f"API Error: {e}")
```

### Register a Domain

```python
try:
    # Contact information required for domain registration
    registrant_info = {
        "FirstName": "John",
        "LastName": "Doe",
        "Address1": "123 Main St",
        "City": "Anytown",
        "StateProvince": "CA",
        "PostalCode": "12345",
        "Country": "US",
        "Phone": "+1.1234567890",
        "EmailAddress": "john@example.com"
    }
    
    # Register a new domain
    result = client.domains_create(
        domain_name="example.com",
        years=1,
        registrant_info=registrant_info,
        nameservers=["dns1.namecheaphosting.com", "dns2.namecheaphosting.com"],
        add_free_whois_guard=True,
        wg_enabled=True
    )
    
    # Process result
    domain_id = result.get("DomainCreateResult", {}).get("Domain", {}).get("ID")
    print(f"Domain registered with ID: {domain_id}")
except NamecheapException as e:
    print(f"API Error: {e}")
```

### Manage DNS Records

```python
try:
    # Get existing DNS records
    result = client.domains_dns_get_hosts("example.com")
    
    # The fields below use the more intuitive format, but the API will accept either format:
    # - Name/HostName (both work)
    # - Type/RecordType (both work)
    # - Value/Address (both work)
    # - Priority/MXPref (for MX records, both work)
    
    # Add new DNS records
    dns_records = [
        {
            "Name": "@",
            "Type": "A", 
            "Value": "192.0.2.1",
            "TTL": 1800  # Can be int or string
        },
        {
            "Name": "www",
            "Type": "CNAME",
            "Value": "@",
            "TTL": 1800
        },
        {
            "Name": "mail",
            "Type": "MX",
            "Value": "mail.example.com",
            "Priority": 10,  # MX priority
            "TTL": 1800
        }
    ]
    
    # Set the DNS records
    result = client.domains_dns_set_hosts(
        domain_name="example.com",
        hosts=dns_records
    )
    
    print("DNS records updated successfully")
except NamecheapException as e:
    print(f"API Error: {e}")
```

### Using the DNS Tool

The package includes a handy DNS management tool that you can use to manage your DNS records from the command line.

```bash
# List all DNS records for a domain
python examples/dns_tool.py list example.com

# Add a DNS record
python examples/dns_tool.py add example.com --name blog --type A --value 192.0.2.1 --ttl 1800

# Delete a DNS record
python examples/dns_tool.py delete example.com --name blog --type A

# Import DNS records from a JSON file
python examples/dns_tool.py import example.com dns_records.json

# Export DNS records to a JSON file
python examples/dns_tool.py export example.com dns_records.json
```

## Sandbox Environment

Namecheap provides a sandbox environment for testing. To use it, set `sandbox=True` when initializing the client.

## Rate Limits

Namecheap API has the following rate limits:
- 20 requests per minute
- 700 requests per hour
- 8000 requests per day

## Supported Endpoints

The SDK currently supports the following Namecheap API endpoints:

### Domains
- `domains_check` - Check domain availability
- `domains_get_list` - Get list of domains in your account
- `domains_get_contacts` - Get contact information for a domain
- `domains_create` - Register a new domain
- `domains_renew` - Renew a domain
- `domains_get_info` - Get detailed information about a domain
- `domains_get_tld_list` - Get list of available TLDs

### DNS
- `domains_dns_set_custom` - Set custom nameservers for a domain
- `domains_dns_set_default` - Set default nameservers for a domain
- `domains_dns_get_hosts` - Get DNS host records for a domain
- `domains_dns_set_hosts` - Set DNS host records for a domain

Additional endpoints from the Namecheap API may be added in future releases based on user needs and contributions.

## Error Handling

The SDK includes a `NamecheapException` class that provides detailed error information from the API:

```python
try:
    result = client.domains_check(["example.com"])
except NamecheapException as e:
    print(f"Error code: {e.code}")
    print(f"Error message: {e.message}")
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup

This project uses poetry for dependency management and packaging:

```bash
# Install poetry
curl -sSL https://install.python-poetry.org | python3 -

# Setup development environment
poetry install

# Install pre-commit hooks
pip install pre-commit
pre-commit install
```

### Code Quality Standards

This project follows these coding standards:

- **Formatting**: Black with 88 character line length
- **Import Sorting**: isort (configured to be compatible with Black)
- **Linting**: Ruff for fast and comprehensive linting
- **Type Checking**: mypy with strict type checking

All these checks are enforced in CI/CD pipelines and can be run locally:

```bash
# Format code
poetry run black .
poetry run isort .

# Lint code
poetry run ruff check .

# Type check
poetry run mypy namecheap

# Run tests
poetry run pytest
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

All this code was produced in a single sitting vibe coding with `claude code` for 2 hours and ~$25.

Excuse the occasional AI slop, if you spot it let me know.
