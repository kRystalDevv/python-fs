# python-fs

**python-fs** is a simple, easy-to-deploy file server requiring minimal configuration.

## Features

- Minimal setup
- Minimal dependencies
- Lightweight
- Serves files over HTTP

## Installing Dependencies

### Method 1 (Simple)

Run the `setup.bat` file to automatically Install `cloudflared` and  python dependencies.

### Method 2 (Manual)

```bash
pip install -r requirements.txt
```
Before running the server, ensure that cloudflared is installed and available in your system PATH.
[Install cloudflared](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install/)

## Usage

```bash
python python-fs.py
```
