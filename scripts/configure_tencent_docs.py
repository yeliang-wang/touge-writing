#!/usr/bin/env python3
"""Interactively add Tencent Docs to the host Codex configuration.

Run in a local terminal. Input is hidden and never stored in this repository.
Existing server definitions are not overwritten.
"""
import getpass
import json
import os
from pathlib import Path
from workspace_lib import atomic_text


def main():
    config = Path.home() / '.codex/config.toml'
    text = config.read_text() if config.exists() else ''
    if '[mcp_servers.tencent-docs' in text or '[mcp_servers."tencent-docs"' in text:
        raise SystemExit('tencent-docs already exists; review the existing host configuration.')
    print('Get your personal authorization value at https://docs.qq.com/open/auth/mcp.html')
    value = getpass.getpass('Tencent Docs Authorization value (hidden): ').strip()
    if not value or '\n' in value or '\r' in value:
        raise SystemExit('Empty or multiline value; configuration unchanged.')
    addition = '\n[mcp_servers.tencent-docs]\nurl = "https://docs.qq.com/openapi/mcp"\nstartup_timeout_sec = 30\ntool_timeout_sec = 60\nhttp_headers = { Authorization = ' + json.dumps(value) + ' }\n'
    # A configuration backup may itself contain credentials. Keep it in the host directory.
    backup = config.with_name('config.before-touge-tencent-docs.toml')
    if config.exists() and not backup.exists():
        atomic_text(backup, text)
        os.chmod(backup, 0o600)
    atomic_text(config, text + addition)
    os.chmod(config, 0o600)
    print('Saved in the host Codex configuration. Restart/reconnect MCP, then run real read/write checks. No token is printed.')


if __name__ == '__main__':
    main()
