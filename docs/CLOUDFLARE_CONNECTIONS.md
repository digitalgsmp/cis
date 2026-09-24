# Cloudflare Connections — CIS

Authoritative inventory of every Cloudflare connection CIS depends on: the
zone, the tunnels, every public hostname, what each one points at, and which
Access policy guards it.

Last verified **2026-09-24** against the live system (WB.1 stable-origin card).

**This file contains no credentials.** No API token, tunnel credential, origin
certificate, private key, service-token value or Access JWT appears here, and
none should ever be added. Credential *locations* are named; their contents are
not. When a value is genuinely needed, name the variable and keep the value in
`secrets.env` or the Cloudflare dashboard.

---

## 1. Zone

| Item | Value |
|---|---|
| Domain | `creative-intelligence-system.com` |
| Status | Active in the operator's Cloudflare account |
| Edge certificate | Cloudflare-served Let's Encrypt wildcard |
| Certificate SAN | `*.creative-intelligence-system.com`, `creative-intelligence-system.com` |
| Access team domain | `cis-live.cloudflareaccess.com` |

Because the wildcard covers every subdomain, a new hostname needs **no**
certificate work — only a DNS record and an ingress rule.

> **Not enabled: Always Use HTTPS.** Plain `http://` is served with a 200 and no
> redirect. Verified 2026-09-24. Turn on at SSL/TLS → Edge Certificates →
> Always Use HTTPS. Tracked as discovery 44 (CF-D2).

---

## 2. Tunnels

| Name | UUID | Created | State |
|---|---|---|---|
| `cis-creative-vm` | `2b2d168a-1180-43a4-9c3d-7533a076937b` | 2026-05-10 | **Active** — carries all traffic |
| `cis-live` | `943e623f-bcf2-45ee-b31f-aedf8703218c` | 2026-04-20 | Dormant — no connections, unused |

`cis-live` is a leftover. It is not running and nothing routes to it. Do not
delete it without checking the dashboard for DNS records still pointing at it.

### How `cis-creative-vm` runs

| Item | Value |
|---|---|
| Binary | `/usr/local/bin/cloudflared`, version 2026.3.0 |
| Managed by | **user** systemd — not system systemd |
| Unit | `~/.config/systemd/user/cloudflared.service` ("CIS Cloudflare Tunnel") |
| Command | `cloudflared tunnel run cis-creative-vm` |
| Config mode | **Locally-managed** — ingress lives in a local file, *not* the dashboard |
| Ingress file | `~/.cloudflared/config.yml` |
| Credentials | `~/.cloudflared/<uuid>.json` — never open or print |
| Origin cert | `~/.cloudflared/cert.pem` — never open or print |

Two consequences worth internalising:

1. **Ingress cannot be changed from the Cloudflare dashboard.** The dashboard
   does not hold this tunnel's routing. Edit `~/.cloudflared/config.yml`.
2. **Use `systemctl --user`, not `sudo systemctl`.** It is a user unit. It
   starts with the user session, not at boot before login.

---

## 3. Public hostnames

All three terminate at Cloudflare's edge and reach this machine only through
the tunnel. **No port is exposed to the Internet directly.**

| Hostname | → local service | What it is | Access policy |
|---|---|---|---|
| `mcp.creative-intelligence-system.com` | `localhost:8888` | `mcp-proxy` (pid 5359) | **Service token** — `GET /` returns 403 |
| `api.creative-intelligence-system.com` | `localhost:5000` | Production `cis-pipeline` container | **"Eric only" Allow** — `GET /` returns 302 to the Access login |
| `workbench.creative-intelligence-system.com` | `127.0.0.1:5055` | WB.1 OIDC preview app | **None, deliberately** — see §5 |

Ingress is first-match and ordered; the catch-all must stay last:

```yaml
ingress:
  - hostname: mcp.creative-intelligence-system.com
    service: http://localhost:8888
  - hostname: api.creative-intelligence-system.com
    service: http://localhost:5000
  - hostname: workbench.creative-intelligence-system.com
    service: http://127.0.0.1:5055
  - service: http_status:404
```

Verify any change before restarting:

```bash
cloudflared tunnel ingress validate
cloudflared tunnel ingress rule https://workbench.creative-intelligence-system.com/
```

---

## 4. Access policies

Reusable policies, from the dashboard (Access controls → Policies):

| Policy | Action | Applications using it |
|---|---|---|
| Eric only | Allow | 1 — `api.*` |
| API Service Token | Service Auth | 0 — currently inert |
| MCP Service Token | Service Auth | 1 — `mcp.*` |

Access is applied **per application**. There is no zone-wide or wildcard
application, proven by live probe: the `workbench.*` hostname returns CIS's own
responses with zero `cf-access-domain`, `cf-access-aud`, `CF_AppSession` or
`cloudflareaccess.com` redirects on any path.

---

## 5. Why the Workbench hostname has no Access policy

This is intentional, and reversing it would break the product.

The Workbench authenticates users through **Auth0/OIDC inside CIS**:

```
Browser → CIS → Auth0 → Google or email → CIS callback → Workbench session
```

Putting Cloudflare Access in front would insert a *second*, unrelated login and
intercept the Auth0 callback:

```
Cloudflare Access login → Workbench → Auth0 login     ← not what we want
```

Tunnel and Access are separate jobs. **The tunnel provides network ingress and
hides the origin. Auth0 + CIS provide the application login.**

What actually protects this hostname:

- the origin binds `127.0.0.1:5055` only — the tunnel is the sole external path;
- the preview app registers *only* the auth surface (see §6);
- once configured, CIS enforces OIDC signature/issuer/audience/nonce/PKCE plus a
  server-side email allowlist.

---

## 6. What the Workbench origin exposes

`tools/development/oidc_preview.py`, bound to loopback, registering eight routes
and nothing else:

```
/                                  /api/workbench/auth/login
/<path:asset>                      /api/workbench/auth/callback
/api/workbench/preview/status      /api/workbench/auth/session
/api/workbench/preview/whoami      /api/workbench/auth/logout
```

It does **not import** `workbench_app`, `card_factory_app`, `card_runner` or
`braingate_conversation` — so Card Factory, Card Runner, proposal
confirm/approve and dispatch have no route to reach and no database handle to
misuse. Asserted by `runtime/tests/test_oidc_preview_boundary.py`.

Note when probing: the SPA catch-all answers an unknown `GET` with `200
text/html` (`index.html`) and an unknown `POST` with `405`. Neither is an API.
Compare the body hash against `/` before reading a 200 as a live endpoint.

> The preview app is currently started by hand and **does not survive a reboot**.
> The hostname stays valid; the origin behind it would return 502 until it is
> restarted. Tracked as discovery 45 (CF-D3).

---

## 7. Operating notes

### Adding a hostname

```bash
# 1. edit ~/.cloudflared/config.yml — new rule BEFORE the catch-all
# 2. validate
cloudflared tunnel ingress validate
# 3. DNS (creates the CNAME to the tunnel)
cloudflared tunnel route dns cis-creative-vm <hostname>
# 4. apply — see the warning below
systemctl --user restart cloudflared
```

### ⚠ `SIGHUP` kills this cloudflared — it does not reload it

On 2026-09-24, `kill -HUP` on cloudflared 2026.3.0 terminated the process
(`code=killed, signal=HUP`). The user unit has **no `Restart=` policy**, so the
tunnel stayed down until restarted by hand — a 3m14s outage across *all*
hostnames.

- To apply an ingress change, use `systemctl --user restart cloudflared`.
- Expect a few seconds of downtime on every hostname; there is no zero-downtime
  reload for a locally-managed tunnel.
- **Any crash takes CIS off the Internet until a human notices.** Adding
  `Restart=always` and `RestartSec=5` to the unit is recommended — discovery 43 (CF-D1).

### Health checks

```bash
systemctl --user status cloudflared
cloudflared tunnel info cis-creative-vm      # expect 4 edge connections
journalctl --user -u cloudflared -n 50
```

A healthy tunnel registers ~4 connections across two Cloudflare colos
(observed: `ord08` ×2, `msp01` ×2).

### Version

2026.3.0 is installed; cloudflared reports 2026.9.1 available. Upgrading is an
unrelated change with its own outage risk — do it deliberately, not as a side
effect of another task.
