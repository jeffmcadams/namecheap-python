# DNS Manager TUI

A powerful Terminal User Interface (TUI) for managing DNS records using the Namecheap Python SDK and Textual framework.

## Features

- Interactive TUI for DNS record management
- Add, edit, and delete DNS records
- Real-time validation and error handling
- Support for multiple record types (A, AAAA, CNAME, MX, TXT, etc.)
- Batch operations support
- Export/Import DNS configurations

## Screenshots

![DNS Manager Main Screen - Landing View](assets/screenshot1.png)
![Domain Selected - tdo.garden](assets/screenshot2.png)
![Adding New DNS Record Modal](assets/screenshot3.png)
![Editing Existing DNS Record](assets/screenshot4.png)

## Installation

```bash
# Install with uv
uv pip install -e ".[tui]"

# Or with pip
pip install -e ".[tui]"
```

## Usage

Run the DNS manager:

```bash
namecheap-dns-tui
```

### Environment Variables

Make sure you have your Namecheap API credentials set:

```bash
export NAMECHEAP_API_USER="your_username"
export NAMECHEAP_API_KEY="your_api_key"
export NAMECHEAP_USERNAME="your_username"
```

Or create a `.env` file in the project root.

### Commands

- **↑/↓** - Navigate through records
- **Enter** - Edit selected record
- **n** - Add new record
- **d** - Delete selected record
- **r** - Refresh records
- **e** - Export configuration
- **i** - Import configuration
- **q** - Quit

## Architecture

This example demonstrates:
- Building complex TUIs with Textual
- Integrating with the Namecheap SDK
- Handling async operations in a TUI
- Form validation and error handling
- File I/O for configuration management

## Requirements

- Python 3.12+
- Namecheap API credentials
- Terminal with 256-color support (recommended)