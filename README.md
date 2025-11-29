# VPN Config Scanner PRO

A powerful and user-friendly tool to scan, test, and manage VPN configurations (VMess, VLESS, Trojan, Shadowsocks) with a modern graphical interface.

## Features

- **Multi-source Configuration Loading**
  - Load from subscription URLs
  - Decode Base64-encoded configuration data
  - Import from local folder files (supports `sub*.txt` files)
  - Automatic deduplication of configurations

- **User-friendly Interface**
  - Dark mode design with customtkinter
  - Progress tracking with visual indicators
  - Real-time logging of operations
  - Easy-to-use controls and status updates

- **Configuration Testing**
  - Tests connection latency
  - Categorizes by protocol (VMess, VLESS, Trojan, Shadowsocks)
  - Filters valid configurations

## Installation

### Prerequisites
- Python 3.7 or higher

### Automatic Setup
The application will automatically install required dependencies on first run.

### Manual Installation
Install required packages using:
```bash
pip install -r requirements.txt
```

## Usage

1. **Load Configurations**
   - Enter a subscription URL or paste Base64-encoded data
   - Or select a local folder containing configuration files (`sub*.txt`)

2. **Start Scanning**
   - Click "START SCANNING" to begin testing configurations
   - Monitor progress through the progress bar and status updates
   - View results in the log window

## Supported Protocols
- VMess
- VLESS
- Trojan
- Shadowsocks (SS)

## File Structure
- `scanner.py`: Main application code with GUI and scanning logic
- `requirements.txt`: Required Python packages
- `.gitignore`: Git ignore file to exclude sensitive data and environment files

## Notes
- Never commit VPN configurations to version control (`.gitignore` is pre-configured to prevent this)
- The tool includes automatic error handling and dependency installation
- Connection latency is measured and filtered (≤800ms for valid configurations)

## License
[MIT](LICENSE) (Assumed, as no license file was provided)