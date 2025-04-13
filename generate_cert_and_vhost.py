#!/usr/bin/env python3

import os
import subprocess
from pathlib import Path
import argparse
import stat
import sys
from datetime import datetime
from OpenSSL import crypto

CA_CERT = Path("/path/to/rootCA/rootCA.pem")
CA_KEY = Path("/path/to/rootCA/rootCA.key")
APACHE_SITES_AVAILABLE = Path("/etc/apache2/sites-available")
ETC_HOSTS = Path("/etc/hosts")

def is_cert_expiring(cert_path: Path, days: int = 30) -> bool:
    if not cert_path.exists():
        return True
    with open(cert_path, 'rb') as f:
        cert = crypto.load_certificate(crypto.FILETYPE_PEM, f.read())
    expiry = datetime.strptime(cert.get_notAfter().decode('ascii'), '%Y%m%d%H%M%SZ')
    remaining_days = (expiry - datetime.utcnow()).days
    return remaining_days < days

def create_ca_signed_cert(domain):
    cert_dir = Path.cwd() / domain
    cert_dir.mkdir(parents=True, exist_ok=True)

    key_file = cert_dir / f"{domain}.key"
    csr_file = cert_dir / f"{domain}.csr"
    crt_file = cert_dir / f"{domain}.crt"
    ext_file = cert_dir / f"{domain}_ext.cnf"

    if not is_cert_expiring(crt_file):
        print(f"✅ Certificate is still valid for more than 30 days: {crt_file}")
        return crt_file, key_file

    ext = f"""
subjectAltName = DNS:{domain}, DNS:localhost, IP:127.0.0.1
basicConstraints = CA:FALSE
keyUsage = critical, digitalSignature, keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
"""
    ext_file.write_text(ext)

    subprocess.run(["openssl", "genrsa", "-out", str(key_file), "2048"], check=True)
    subprocess.run([
        "openssl", "req", "-new", "-key", str(key_file),
        "-out", str(csr_file),
        "-subj", f"/CN={domain}"
    ], check=True)
    subprocess.run([
        "openssl", "x509", "-req", "-in", str(csr_file),
        "-CA", str(CA_CERT), "-CAkey", str(CA_KEY), "-CAcreateserial",
        "-out", str(crt_file), "-days", "825", "-sha256",
        "-extfile", str(ext_file)
    ], check=True)

    key_file.chmod(stat.S_IRUSR | stat.S_IWUSR)
    crt_file.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)

    print(f"✅ CA-signed certificate created: {crt_file}")
    return crt_file, key_file

def create_vhost_file(domain, document_root, cert_file, key_file):
    vhost_path = APACHE_SITES_AVAILABLE / f"{domain}.conf"

    vhost_content = f"""
<VirtualHost *:80>
    ServerName {domain}
    DocumentRoot {document_root}
    <Directory {document_root}/>
        Options Indexes FollowSymLinks
        AllowOverride All
        Require all granted
    </Directory>
    ErrorLog ${{APACHE_LOG_DIR}}/{domain}.error.log
    CustomLog ${{APACHE_LOG_DIR}}/{domain}.access.log combined
</VirtualHost>

<VirtualHost *:443>
    ServerName {domain}
    DocumentRoot {document_root}
    <Directory {document_root}/>
        Options Indexes FollowSymLinks
        AllowOverride All
        Require all granted
    </Directory>

    SSLEngine on
    SSLCertificateFile {cert_file}
    SSLCertificateKeyFile {key_file}

    ErrorLog ${{APACHE_LOG_DIR}}/{domain}.ssl.error.log
    CustomLog ${{APACHE_LOG_DIR}}/{domain}.ssl.access.log combined
</VirtualHost>
""".strip()

    with open(vhost_path, "w") as f:
        f.write(vhost_content)
    print(f"✅ VHost created (or overwritten): {vhost_path}")

    subprocess.run(["sudo", "a2ensite", f"{domain}.conf"], check=True)

def add_to_hosts(domain):
    with open(ETC_HOSTS, "r") as f:
        hosts = f.read()

    if domain not in hosts:
        entry = f"127.0.0.1 {domain}\n"
        with open(ETC_HOSTS, "a") as f:
            f.write(entry)
        print(f"✅ Added to /etc/hosts: {entry.strip()}")
    else:
        print(f"⚠️ Domain already exists in /etc/hosts: {domain}")

def check_apache_config():
    result = subprocess.run(["sudo", "apachectl", "configtest"], capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ Apache config is valid. Restarting Apache...")
        subprocess.run(["sudo", "systemctl", "restart", "apache2"])
    else:
        print("❌ Apache config error:")
        print(result.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description="Generate or renew CA-signed SSL cert, Apache vhost, and /etc/hosts entry",
        usage="sudo ./generate_cert_and_vhost.py <domain> <document_root>"
    )
    parser.add_argument("domain", help="Domain name (e.g., myapp.local)")
    parser.add_argument("document_root", help="Full path to DocumentRoot (e.g., /home/user/app/public)")
    args = parser.parse_args()

    if not args.domain or not args.document_root:
        parser.print_help()
        sys.exit(1)

    cert_file, key_file = create_ca_signed_cert(args.domain)
    create_vhost_file(args.domain, args.document_root, cert_file, key_file)
    add_to_hosts(args.domain)
    check_apache_config()

if __name__ == "__main__":
    main()
