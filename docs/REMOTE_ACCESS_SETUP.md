# Remote Access Setup Guide

## Option 1: Tailscale (Recommended — Simplest)

### Install Tailscale on the host (creative-vm)
```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```

### Expose the control plane
```bash
# Expose port 5000 via Tailscale Serve
tailscale serve --bg 5000
```

This gives you a `https://creative-vm.tailnet-xxx.ts.net` URL accessible from any device on your tailnet.

### Access from phone
1. Install Tailscale app on your phone
2. Connect to the same tailnet
3. Navigate to the Tailscale URL in your browser

## Option 2: Nginx Reverse Proxy + Let's Encrypt

### Install nginx
```bash
sudo apt install nginx certbot python3-certbot-nginx
```

### Configure reverse proxy
Create `/etc/nginx/sites-available/cis`:
```nginx
server {
    server_name cis.yourdomain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Enable and get TLS certificate
```bash
sudo ln -s /etc/nginx/sites-available/cis /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d cis.yourdomain.com
```

## Option 3: SSH Tunnel (Quick, no setup)

From remote machine:
```bash
ssh -L 5000:127.0.0.1:5000 eric@192.168.1.15
```

Then access `http://localhost:5000` locally.

## Authentication

The relay API supports Bearer token auth via `CIS_PIPELINE_API_KEY` environment variable.

To enable:
1. Set `CIS_PIPELINE_API_KEY=your-secret-key` in the container environment
2. All relay endpoints require `Authorization: Bearer your-secret-key` header

The existing UI auth system (`/api/app/auth/login` and `/api/app/auth/register`) can be extended to provide session-based auth for the control plane UI.
