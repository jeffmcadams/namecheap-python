# Namecheap Python SDK

A modern, friendly Python SDK for the Namecheap API with comprehensive CLI and TUI tools.

## 🚀 Features

- **Modern Python SDK** with full type hints and Pydantic models
- **CLI Tool** for managing domains and DNS from the terminal
- **TUI Application** for visual DNS record management
- **Smart DNS Builder** with fluent interface for record management
- **Auto-configuration** from environment variables
- **Helpful error messages** with troubleshooting guidance
- **Comprehensive logging** with beautiful colored output
- **Sandbox support** for safe testing

## 📦 Installation

```bash
# Core SDK only
pip install namecheap-python

# With CLI tool
pip install namecheap-python[cli]

# With TUI tool  
pip install namecheap-python[tui]

# Everything
pip install namecheap-python[all]
```

## 🎯 Quick Start

### SDK Usage

```python
from namecheap import Namecheap

# Initialize (auto-loads from environment)
nc = Namecheap()

# Check domain availability
domains = nc.domains.check("example.com", "coolstartup.io")
for domain in domains:
    if domain.available:
        print(f"✅ {domain.domain} is available!")

# List your domains
my_domains = nc.domains.list()
for domain in my_domains:
    print(f"{domain.name} expires on {domain.expires}")

# Manage DNS with the builder
nc.dns.set("example.com",
    nc.dns.builder()
    .a("@", "192.0.2.1")
    .a("www", "192.0.2.1")  
    .mx("@", "mail.example.com", priority=10)
    .txt("@", "v=spf1 include:_spf.google.com ~all")
)
```

### CLI Usage

```bash
# Configure CLI
uv run namecheap-cli config init

# List domains with beautiful table output
uv run namecheap-cli domain list
```

Output:
```
                    Domains (4 total)
┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━┓
┃ Domain            ┃ Status ┃ Expires    ┃ Auto-Renew ┃ Locked ┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━┩
│ example.com       │ Active │ 2025-10-21 │ ✓          │        │
│ coolsite.io       │ Active │ 2026-05-25 │ ✓          │        │
│ myproject.dev     │ Active │ 2026-05-30 │ ✓          │        │
│ awesome.site      │ Active │ 2026-03-20 │ ✓          │        │
└───────────────────┴────────┴────────────┴────────────┴────────┘
```

```bash
# Check domain availability
uv run namecheap-cli domain check myawesome.com coolstartup.io

# Manage DNS records
uv run namecheap-cli dns list example.com
uv run namecheap-cli dns add example.com A www 192.0.2.1
uv run namecheap-cli dns export example.com --format yaml

# Setup GitHub Pages (example: tdo.garden)
# First, check current DNS records (before setup)
uv run namecheap-cli dns list tdo.garden
```

Initial state (Namecheap default parking page):
```
                         DNS Records for tdo.garden (2 total)
┏━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━┓
┃ Type     ┃ Name                 ┃ Value                      ┃ TTL      ┃ Priority ┃
┡━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━┩
│ CNAME    │ www                  │ parkingpage.namecheap.com. │ 1800     │ 10       │
│ URL      │ @                    │ http://www.tdo.garden/     │ 1800     │ 10       │
└──────────┴──────────────────────┴────────────────────────────┴──────────┴──────────┘
```

```bash
# Add GitHub Pages A records for apex domain
❯ uv run namecheap-cli dns add tdo.garden A @ 185.199.108.153
      Built namecheap-python @ file:///Users/adrian/Developer/namecheap-python
Uninstalled 1 package in 0.77ms
Installed 1 package in 1ms
Adding A record to tdo.garden...
✅ Added A record successfully!

❯ uv run namecheap-cli dns add tdo.garden A @ 185.199.109.153
Adding A record to tdo.garden...
✅ Added A record successfully!

❯ uv run namecheap-cli dns add tdo.garden A @ 185.199.110.153
Adding A record to tdo.garden...
✅ Added A record successfully!

❯ uv run namecheap-cli dns add tdo.garden A @ 185.199.111.153
Adding A record to tdo.garden...
✅ Added A record successfully!

# Add CNAME for www subdomain
❯ uv run namecheap-cli dns add tdo.garden CNAME www adriangalilea.github.io
Adding CNAME record to tdo.garden...
✅ Added CNAME record successfully!

# Verify the setup
❯ uv run namecheap-cli dns list tdo.garden
```

Final state (with GitHub Pages + old records still present):
```
                         DNS Records for tdo.garden (7 total)
┏━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━┓
┃ Type     ┃ Name                 ┃ Value                      ┃ TTL      ┃ Priority ┃
┡━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━┩
│ A        │ @                    │ 185.199.108.153            │ 1800     │ 10       │
│ A        │ @                    │ 185.199.109.153            │ 1800     │ 10       │
│ A        │ @                    │ 185.199.110.153            │ 1800     │ 10       │
│ A        │ @                    │ 185.199.111.153            │ 1800     │ 10       │
│ CNAME    │ www                  │ parkingpage.namecheap.com. │ 1800     │ 10       │
│ CNAME    │ www                  │ adriangalilea.github.io.   │ 1800     │ 10       │
│ URL      │ @                    │ http://www.tdo.garden/     │ 1800     │ 10       │
└──────────┴──────────────────────┴────────────────────────────┴──────────┴──────────┘
```

Note: You may want to remove the old parking page records after confirming GitHub Pages works.
```

### TUI Usage

```bash
# Launch interactive DNS manager
uv run namecheap-dns-tui
```

![DNS Manager TUI](src/namecheap_dns_tui/assets/screenshot2.png)

## 📖 Documentation

- **[Examples Overview](examples/README.md)** - Quick examples for all tools
- **[CLI Documentation](src/namecheap_cli/README.md)** - Complete CLI reference
- **[TUI Documentation](src/namecheap_dns_tui/README.md)** - TUI features and usage
- **[SDK Quickstart](examples/quickstart.py)** - Python code examples

## ⚙️ Configuration

### Environment Variables

Create a `.env` file or set environment variables:

```bash
# Required
NAMECHEAP_API_KEY=your-api-key
NAMECHEAP_USERNAME=your-username

# Optional
NAMECHEAP_API_USER=api-username  # defaults to USERNAME
NAMECHEAP_CLIENT_IP=auto         # auto-detected if not set
NAMECHEAP_SANDBOX=false          # use production API
```

### Python Configuration

```python
from namecheap import Namecheap

nc = Namecheap(
    api_key="your-api-key",
    username="your-username", 
    api_user="api-username",    # Optional
    client_ip="1.2.3.4",       # Optional, auto-detected
    sandbox=False              # Production mode
)
```

### CLI Configuration

```bash
# Interactive setup
uv run namecheap-cli config init

# Creates ~/.namecheap/config.yaml with profiles
```

## 🔧 Advanced SDK Usage

### DNS Builder Pattern

The DNS builder provides a fluent interface for managing records:

```python
# Build complex DNS configurations
nc.dns.set("example.com",
    nc.dns.builder()
    # A records
    .a("@", "192.0.2.1")
    .a("www", "192.0.2.1")
    .a("blog", "192.0.2.2")
    
    # AAAA records  
    .aaaa("@", "2001:db8::1")
    .aaaa("www", "2001:db8::1")
    
    # MX records
    .mx("@", "mail.example.com", priority=10)
    .mx("@", "mail2.example.com", priority=20)
    
    # TXT records
    .txt("@", "v=spf1 include:_spf.google.com ~all")
    .txt("_dmarc", "v=DMARC1; p=none;")
    
    # CNAME records
    .cname("blog", "myblog.wordpress.com")
    .cname("shop", "myshop.shopify.com")
    
    # URL redirects
    .url("old", "https://new-site.com", redirect_type="301")
)
```

### Domain Management

```python
# Check multiple domains with pricing
results = nc.domains.check(
    "example.com", 
    "coolstartup.io",
    "myproject.dev",
    include_pricing=True
)

for domain in results:
    if domain.available:
        print(f"✅ {domain.domain} - ${domain.price}/year")
    else:
        print(f"❌ {domain.domain} is taken")

# List domains with filters
domains = nc.domains.list()
expiring_soon = [d for d in domains if (d.expires - datetime.now()).days < 30]

# Register a domain
from namecheap import Contact

contact = Contact(
    first_name="John",
    last_name="Doe", 
    address1="123 Main St",
    city="New York",
    state_province="NY",
    postal_code="10001", 
    country="US",
    phone="+1.2125551234",
    email="john@example.com"
)

result = nc.domains.register(
    "mynewdomain.com",
    years=2,
    contact=contact,
    whois_protection=True
)
```

### Error Handling

```python
from namecheap import NamecheapError

try:
    nc.domains.check("example.com")
except NamecheapError as e:
    print(f"Error: {e.message}")
    if e.help:
        print(f"💡 Tip: {e.help}")
```

## 🚧 Pending Features

The following Namecheap API features are planned for future releases:

- **SSL API** - Certificate management
- **Domain Transfer API** - Transfer domains between registrars  
- **Domain NS API** - Custom nameserver management
- **Users API** - Account management and balance checking
- **Whois API** - WHOIS information lookups
- **Email Forwarding** - Email forwarding configuration

See [pending.md](pending.md) for full details.

## 🛠️ Development

See [Development Guide](docs/dev/README.md) for detailed development instructions.

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. See the [Development Guide](docs/dev/README.md) for setup instructions and guidelines.