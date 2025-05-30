# Namecheap CLI

A comprehensive command-line interface for managing Namecheap domains and DNS records.

## Installation

```bash
pip install namecheap
```

Or install from source:

```bash
git clone https://github.com/adriangalilea/namecheap-python.git
cd namecheap-python
pip install -e .
```

## Quick Start

### 1. Initialize Configuration

```bash
nc config init
```

This will create `~/.namecheap/config.yaml` with your API credentials.

### 2. Basic Commands

```bash
# List all domains
nc domain list

# Check domain availability
nc domain check example.com --pricing

# List DNS records
nc dns list example.com

# Add DNS record
nc dns add example.com A www 192.0.2.1
```

## Command Structure

```
nc [global-options] <resource> <action> [options] [arguments]
```

### Resources

- `domain` - Domain management
- `dns` - DNS record management
- `account` - Account operations
- `config` - CLI configuration
- `completion` - Shell completion

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
nc domain list

# List domains expiring soon
nc domain list --expiring-in 60

# List only active domains
nc domain list --status active

# Output as JSON
nc domain list --output json
```

### Check Domain Availability

```bash
# Check single domain
nc domain check example.com

# Check multiple domains
nc domain check example.com coolstartup.io myproject.dev

# Include pricing information
nc domain check example.com --pricing

# Check from file
nc domain check --file domains.txt
```

### Domain Information

```bash
nc domain info example.com
```

## DNS Management

### List DNS Records

```bash
# List all records
nc dns list example.com

# Filter by type
nc dns list example.com --type A

# Filter by name
nc dns list example.com --name www

# Output as JSON
nc dns list example.com --output json
```

### Add DNS Records

```bash
# Add A record
nc dns add example.com A www 192.0.2.1

# Add AAAA record
nc dns add example.com AAAA www 2001:db8::1

# Add CNAME record
nc dns add example.com CNAME blog www.example.com

# Add MX record with priority
nc dns add example.com MX @ mail.example.com --priority 10

# Add TXT record
nc dns add example.com TXT @ "v=spf1 include:_spf.google.com ~all"

# Add URL redirect
nc dns add example.com URL301 www https://newsite.com

# Custom TTL
nc dns add example.com A www 192.0.2.1 --ttl 300
```

### Delete DNS Records

```bash
# Delete by type and name
nc dns delete example.com --type A --name www

# Delete by value
nc dns delete example.com --value "old-verification-string"

# Delete all records (with confirmation)
nc dns delete example.com --all

# Skip confirmation
nc dns delete example.com --type TXT --yes
```

### Export/Import DNS Records

```bash
# Export as YAML (default)
nc dns export example.com

# Export as BIND zone file
nc dns export example.com --format bind > example.com.zone

# Export as JSON
nc dns export example.com --format json > dns-records.json

# Import from file (not yet implemented)
nc dns import example.com --file dns-records.yaml
```

## Configuration

### Configuration File

Location: `~/.namecheap/config.yaml`

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

### Environment Variables

You can also use environment variables:

- `NAMECHEAP_API_KEY`
- `NAMECHEAP_USERNAME`
- `NAMECHEAP_API_USER`
- `NAMECHEAP_CLIENT_IP`
- `NAMECHEAP_SANDBOX`

### Using Profiles

```bash
# Use default profile
nc domain list

# Use specific profile
nc --profile business domain list
```

## Output Formats

### Table (Default)

```bash
nc domain list
```

```
Domains (3 total)
┏━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━┓
┃ Domain          ┃ Status ┃ Expires    ┃ Auto-Renew┃ Locked ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━┩
│ example.com     │ Active │ 2024-12-31 │ ✓         │ 🔒     │
│ coolstartup.io  │ Active │ 2025-06-15 │ ✓         │        │
│ myproject.dev   │ Active │ 2024-08-20 │ ✗         │ 🔒     │
└─────────────────┴────────┴────────────┴───────────┴────────┘
```

### JSON

```bash
nc domain list --output json
```

```json
[
  {
    "domain": "example.com",
    "status": "active",
    "expires": "2024-12-31T00:00:00",
    "auto_renew": true,
    "locked": true
  }
]
```

### CSV

```bash
nc domain list --output csv
```

```csv
domain,status,expires,auto_renew,locked
example.com,active,2024-12-31T00:00:00,true,true
```

### YAML

```bash
nc domain list --output yaml
```

```yaml
- domain: example.com
  status: active
  expires: '2024-12-31T00:00:00'
  auto_renew: true
  locked: true
```

## Shell Completion

### Install Completion

```bash
# Bash
nc completion bash >> ~/.bashrc

# Zsh
nc completion zsh >> ~/.zshrc

# Fish
nc completion fish > ~/.config/fish/completions/nc.fish
```

### Usage

```bash
nc domain <TAB>
check    info     list     lock     register renew    unlock

nc dns add example.com <TAB>
A        AAAA     CNAME    MX       NS       TXT      URL
```

## Advanced Usage

### Scripting

```bash
# Find domains expiring soon
nc domain list --expiring-in 30 --output json | \
  jq -r '.[] | .domain'

# Bulk check domains
for domain in site1.com site2.com site3.com; do
  nc dns add $domain A @ 192.0.2.1
done

# Export all DNS records
for domain in $(nc domain list --output json | jq -r '.[].domain'); do
  nc dns export $domain --format bind > zones/${domain}.zone
done
```

### Filtering with jq

```bash
# Get only A records
nc dns list example.com --output json | \
  jq '.[] | select(.type == "A")'

# Get domains without auto-renew
nc domain list --output json | \
  jq '.[] | select(.auto_renew == false) | .domain'
```

### Batch Operations

```bash
# Check domains from file
cat > domains.txt << EOF
coolname.com
awesomeproject.io
mycompany.dev
EOF

nc domain check --file domains.txt --pricing
```

## Error Handling

The CLI provides clear error messages:

```bash
$ nc domain register taken-domain.com
❌ Error: taken-domain.com is not available for registration

💡 Suggestions:
  • taken-domain.net is available for $12.98/year
  • taken-domain.io is available for $32.88/year
  • mytaken-domain.com is available for $12.98/year
```

## Exit Codes

- `0` - Success
- `1` - General error
- `130` - Interrupted (Ctrl+C)

## Tips

1. **Use aliases**: Add to your shell config:
   ```bash
   alias ncd='nc domain'
   alias ncdns='nc dns'
   ```

2. **Default output**: Set in config for your preference:
   ```yaml
   defaults:
     output: json  # Always output JSON
   ```

3. **Quick domain check**: 
   ```bash
   nc domain check example.com --pricing | grep "✅"
   ```

4. **Safe deletion**: Always use `--type` or `--name` to avoid accidents:
   ```bash
   nc dns delete example.com --type TXT --value "old-record"
   ```

5. **Dry run**: Use `--output json` to preview changes:
   ```bash
   nc dns list example.com --output json > before.json
   # Make changes
   nc dns list example.com --output json > after.json
   diff before.json after.json
   ```

## Troubleshooting

### API Key Issues

```bash
# Check if API key is set
echo $NAMECHEAP_API_KEY

# Test with sandbox
nc --sandbox domain list

# Use verbose mode
nc --verbose domain list
```

### Permission Denied

```bash
# Fix config file permissions
chmod 600 ~/.namecheap/config.yaml
```

### Debug Mode

```bash
# Show full traceback on errors
nc --debug domain list
```

## Contributing

See the main project README for contribution guidelines.

## License

MIT