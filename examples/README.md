# Namecheap Python SDK Examples

This directory contains examples demonstrating how to use the Namecheap Python SDK and its tools.

## 📚 Examples Overview

### 1. 🚀 Quickstart Example (`quickstart.py`)

A simple Python script showing basic SDK usage:

```python
from namecheap import Namecheap

# Initialize client
nc = Namecheap()

# Check domain availability
results = nc.domains.check("example.com", include_pricing=True)

# List your domains
domains = nc.domains.list()

# Manage DNS records
records = nc.dns.get("example.com")
```

**Run it:**
```bash
python examples/quickstart.py
```

### 2. 💻 Command-Line Interface (CLI)

A comprehensive CLI tool for managing domains and DNS records.

**Installation:**
```bash
pip install namecheap[cli]
```

**Example usage:**
```bash
# List all domains
uv run namecheap-cli domain list

# Check domain availability with pricing
uv run namecheap-cli domain check example.com coolstartup.io --pricing

# Add DNS record
uv run namecheap-cli dns add example.com A www 192.0.2.1

# Export DNS records
uv run namecheap-cli dns export example.com --format yaml
```

**Example output:**
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

**Output formats:** table (default), json, yaml, csv

[Full CLI documentation →](../src/namecheap_cli/README.md)

### 3. 🎨 DNS Manager TUI

An interactive Terminal User Interface for visual DNS management.

![DNS Manager TUI](../src/namecheap_dns_tui/assets/screenshot2.png)

**Installation:**
```bash
pip install namecheap[tui]
```

**Run it:**
```bash
uv run namecheap-dns-tui
```

**Features:**
- Visual DNS record management
- Add, edit, and delete records interactively
- Real-time validation
- Export/import configurations
- Keyboard shortcuts for efficiency

[Full TUI documentation →](../src/namecheap_dns_tui/README.md)

## 🔧 Setup

All examples require Namecheap API credentials. You can provide them via:

1. **Environment variables:**
   ```bash
   export NAMECHEAP_API_USER="your_username"
   export NAMECHEAP_API_KEY="your_api_key"
   export NAMECHEAP_USERNAME="your_username"
   ```

2. **`.env` file** (in project root):
   ```
   NAMECHEAP_API_USER=your_username
   NAMECHEAP_API_KEY=your_api_key
   NAMECHEAP_USERNAME=your_username
   ```

3. **CLI configuration** (for CLI tool only):
   ```bash
   uv run namecheap-cli config init
   ```

## 📦 Installation Options

```bash
# Core SDK only
pip install namecheap

# SDK + CLI tool
pip install namecheap[cli]

# SDK + TUI tool
pip install namecheap[tui]

# Everything
pip install namecheap[all]
```

## 🚦 Sandbox Mode

All tools support sandbox mode for testing:

```bash
# SDK
nc = Namecheap(sandbox=True)

# CLI
uv run namecheap-cli --sandbox domain list

# Environment variable
export NAMECHEAP_SANDBOX=true
```

## 📖 More Resources

- [SDK Documentation](../README.md)
- [API Reference](https://www.namecheap.com/support/api/methods/)
- [Getting API Access](https://www.namecheap.com/support/api/intro/)