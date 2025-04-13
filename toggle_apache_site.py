#!/usr/bin/env python3

import subprocess
from pathlib import Path
import inquirer

SITES_AVAILABLE = Path("/etc/apache2/sites-available")
SITES_ENABLED = Path("/etc/apache2/sites-enabled")

def get_sites():
    available = {f.name for f in SITES_AVAILABLE.glob("*.conf")}
    enabled = {f.name for f in SITES_ENABLED.glob("*.conf")}
    return sorted((site, site in enabled) for site in available)

def toggle_site(site, enabled):
    if enabled:
        print(f"🔻 Disabling {site}")
        subprocess.run(["sudo", "a2dissite", site], check=True)
    else:
        print(f"🔺 Enabling {site}")
        subprocess.run(["sudo", "a2ensite", site], check=True)

    print("🔄 Reloading Apache...")
    subprocess.run(["sudo", "systemctl", "reload", "apache2"])

def main():
    sites = get_sites()
    choices = [
        f"[{'✓' if enabled else ' '}] {site}" for site, enabled in sites
    ]

    if not choices:
        print("No available sites found.")
        return

    answer = inquirer.prompt([
        inquirer.List(
            "site",
            message="Select a site to toggle (enable/disable):",
            choices=choices
        )
    ])

    if not answer:
        print("No selection made.")
        return

    selected_line = answer["site"]
    selected_site = selected_line.split("]", 1)[1].strip()
    is_enabled = "[✓]" in selected_line

    toggle_site(selected_site, is_enabled)

if __name__ == "__main__":
    main()

