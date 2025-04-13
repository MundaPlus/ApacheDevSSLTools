# Apache Dev SSL Tools

A pair of Python utilities to streamline local development with Apache:

1. **`generate_cert_and_vhost.py`**  
   🔐 Generates a **CA-signed SSL certificate**, creates or updates an Apache virtual host, adds the domain to `/etc/hosts`, and reloads Apache. Supports auto-renewal of certificates.

2. **`toggle_apache_site.py`**  
   🔁 Interactive tool to enable/disable Apache sites from a list of available configs.

---

## 📦 Requirements

Install dependencies:

```bash
pip install pyOpenSSL inquirer
```

System packages:

```bash
sudo apt install openssl apache2
```

---

## 🧰 Usage

### 1. Generate or Renew SSL Cert + VHost

```bash
sudo ./generate_cert_and_vhost.py mysite.local /path/to/project/public
```

This will:
- Generate a new certificate signed by your local root CA (`rootCA.pem` and `rootCA.key`)
- Create/update Apache vhost config
- Add the domain to `/etc/hosts`
- Reload Apache if config is valid
- Skip renewal if cert is still valid (less than 30 days remaining)

> Root CA must be created separately and trusted by your system/browser. See below.

---

### 2. Toggle Apache Site (Enable/Disable)

```bash
sudo ./toggle_apache_site.py
```

- Lists all available site configs in `/etc/apache2/sites-available/`
- Marks enabled sites with ✓
- Lets you select one to enable or disable
- Automatically reloads Apache after change

---

## 🔐 Creating Your Local Root CA (One-time)

```bash
mkdir -p ~/Programs/certs/rootCA
cd ~/Programs/certs/rootCA

openssl genrsa -out rootCA.key 4096
openssl req -x509 -new -nodes -key rootCA.key -sha256 -days 3650 -out rootCA.pem \
    -subj "/C=XX/ST=Dev/L=Local/O=DevRootCA/OU=LocalDev/CN=LocalDev Root CA"

sudo cp rootCA.pem /usr/local/share/ca-certificates/rootCA.crt
sudo update-ca-certificates
```

> 💡 You must also **import `rootCA.pem` into your browser trust store** (Chrome/Edge/Firefox) for HTTPS to be fully trusted.

---

## 🕒 Optional: Set Up Auto-Renew

Run every 15 days via cron:

```bash
sudo crontab -e
```

```cron
0 2 */15 * * /usr/bin/python3 /path/to/generate_cert_and_vhost.py mysite.local /path/to/project/public
```

---

## 📂 Project Structure

```
.
├── generate_cert_and_vhost.py
├── toggle_apache_site.py
└── README.md
```

---

## 💬 License

MIT License – use freely and customize for your dev needs.


