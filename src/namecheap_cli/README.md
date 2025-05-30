# Namecheap CLI

A comprehensive command-line interface for managing Namecheap domains and DNS records.

## Features

- 🌐 Domain management (list, check availability, get info)
- 📝 DNS record management (list, add, delete, export)
- 🎨 Multiple output formats (table, json, yaml, csv)
- ⚙️ Configuration profiles support
- 🔄 Shell completion for bash, zsh, and fish
- 🎯 Intuitive command structure
- 🔒 Sandbox mode for testing

## Installation

```bash
# Install with CLI dependencies
pip install namecheap[cli]

# Or with uv
uv pip install "namecheap[cli]"
```

## Quick Start

### 1. Initialize Configuration

```bash
namecheap-cli config init
```

This creates `~/.namecheap/config.yaml` with your API credentials.

### 2. Basic Commands

```bash
# List all domains
namecheap-cli domain list

# Check domain availability
namecheap-cli domain check example.com

# List DNS records
namecheap-cli dns list example.com

# Add DNS record
namecheap-cli dns add example.com A www 192.0.2.1
```

## Command Structure

```
namecheap-cli [global-options] <resource> <action> [options] [arguments]
```

### Global Options

- `--config PATH` - Use alternate config file
- `--profile NAME` - Use specific profile
- `--sandbox` - Use sandbox API
- `--output FORMAT` - Output format (table, json, yaml, csv)
- `--quiet` - Minimal output
- `--verbose` - Verbose output

## Domain Management

### List Domains

```bash
# List all domains
namecheap-cli domain list

# List domains expiring soon
namecheap-cli domain list --expiring-in 60

# Output as JSON
namecheap-cli domain list --output json
```

### Check Domain Availability

```bash
# Check single domain
namecheap-cli domain check example.com

# Check multiple domains
namecheap-cli domain check example.com coolstartup.io myproject.dev

# Include pricing information
namecheap-cli domain check example.com --pricing

# Check from file
namecheap-cli domain check --file domains.txt
```

### Domain Information

```bash
namecheap-cli domain info example.com
```

## DNS Management

### List DNS Records

```bash
# List all records
namecheap-cli dns list example.com

# Filter by type
namecheap-cli dns list example.com --type A

# Output as JSON
namecheap-cli dns list example.com --output json
```

### Add DNS Records

```bash
# Add A record
namecheap-cli dns add example.com A www 192.0.2.1

# Add MX record with priority
namecheap-cli dns add example.com MX @ mail.example.com --priority 10

# Add TXT record
namecheap-cli dns add example.com TXT @ "v=spf1 include:_spf.google.com ~all"

# Add URL redirect
namecheap-cli dns add example.com URL301 www https://newsite.com

# Custom TTL
namecheap-cli dns add example.com A www 192.0.2.1 --ttl 300
```

### Delete DNS Records

```bash
# Delete by type and name
namecheap-cli dns delete example.com --type A --name www

# Delete by value
namecheap-cli dns delete example.com --value "old-verification-string"

# Skip confirmation
namecheap-cli dns delete example.com --type TXT --yes
```

### Export DNS Records

```bash
# Export as YAML (default)
namecheap-cli dns export example.com

# Export as BIND zone file
namecheap-cli dns export example.com --format bind > example.com.zone

# Export as JSON
namecheap-cli dns export example.com --format json > dns-records.json
```

## Configuration

### Config File Location

`~/.namecheap/config.yaml`

### Example Configuration

```yaml
default_profile: personal

profiles:
  personal:
    api_key: your-api-key
    username: your-username
    api_user: your-username
    sandbox: false
    
  business:
    api_key: business-api-key
    username: business-username
    api_user: business-username
    sandbox: false

defaults:
  output: table
  color: true
  auto_renew: true
  whois_privacy: true
  dns_ttl: 1800
```

### Using Profiles

```bash
# Use default profile
namecheap-cli domain list

# Use specific profile
namecheap-cli --profile business domain list
```

### Environment Variables

You can also use environment variables:
- `NAMECHEAP_API_KEY`
- `NAMECHEAP_USERNAME`
- `NAMECHEAP_API_USER`
- `NAMECHEAP_CLIENT_IP`
- `NAMECHEAP_SANDBOX`

## Output Formats

### Table (Default)

```bash
namecheap-cli domain list
```

```
                    Domains (4 total)
┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━┓
┃ Domain            ┃ Status ┃ Expires    ┃ Auto-Renew ┃ Locked ┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━┩
│ adriangalilea.com │ Active │ 2025-10-21 │ ✓          │        │
│ e-id.to           │ Active │ 2026-05-25 │ ✓          │        │
│ tdo.garden        │ Active │ 2026-05-30 │ ✓          │        │
│ untitled.garden   │ Active │ 2026-03-20 │ ✓          │        │
└───────────────────┴────────┴────────────┴────────────┴────────┘
```

### JSON

```bash
namecheap-cli domain list --output json | jq '.[] | select(.auto_renew == false)'
```

### CSV

```bash
namecheap-cli domain list --output csv > domains.csv
```

### YAML

```bash
namecheap-cli domain list --output yaml
```

## Shell Completion

### Install Completion

```bash
# Bash
namecheap-cli completion bash >> ~/.bashrc

# Zsh
namecheap-cli completion zsh >> ~/.zshrc

# Fish
namecheap-cli completion fish > ~/.config/fish/completions/namecheap-cli.fish
```

## Advanced Usage

### Batch Operations

```bash
# Check domains from file
cat > domains.txt << EOF
coolname.com
awesomeproject.io
mycompany.dev
EOF

namecheap-cli domain check --file domains.txt --pricing
```

### Scripting

```bash
# Find domains expiring soon
namecheap-cli domain list --expiring-in 30 --output json | \
  jq -r '.[] | .domain'

# Export all DNS records
for domain in $(namecheap-cli domain list --output json | jq -r '.[].domain'); do
  namecheap-cli dns export $domain --format bind > zones/${domain}.zone
done
```

### Filtering with jq

```bash
# Get only A records
namecheap-cli dns list example.com --output json | \
  jq '.[] | select(.type == "A")'

# Get domains without auto-renew
namecheap-cli domain list --output json | \
  jq '.[] | select(.auto_renew == false) | .domain'
```

## Tips

1. **Use aliases**: Add to your shell config:
   ```bash
   alias ncd='namecheap-cli domain'
   alias ncdns='namecheap-cli dns'
   ```

2. **Quick domain check**: 
   ```bash
   namecheap-cli domain check example.com --pricing | grep "✅"
   ```

3. **Safe deletion**: Always use `--type` or `--name` to avoid accidents:
   ```bash
   namecheap-cli dns delete example.com --type TXT --value "old-record"
   ```

## Troubleshooting

### API Key Issues

```bash
# Check if API key is set
echo $NAMECHEAP_API_KEY

# Test with sandbox
namecheap-cli --sandbox domain list

# Use verbose mode
namecheap-cli --verbose domain list
```

### Debug Mode

```bash
# Show full traceback on errors
namecheap-cli --debug domain list
```

## Exit Codes

- `0` - Success
- `1` - General error
- `130` - Interrupted (Ctrl+C)