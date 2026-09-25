# Cloudflare Connections — CIS

Authoritative inventory of every Cloudflare connection CIS depends on: the
zone, the tunnels, every public hostname, what each one points at, and which
Access policy guards it.

Last verified **2026-09-25** against the live system (WB.1 tunnel-durability
card; supersedes the stable-origin card of 2026-09-24).

Discovery status as of this revision:

| Discovery | State |
|---|---|
| 43 (CF-D1) — tunnel crash durability | **RESOLVED** — `Restart=always`/`RestartSec=5`, proven by a controlled `SIGKILL` recovery test (§7) |
| 44 (CF-D2) — no HTTP→HTTPS redirect on Workbench | **RESOLVED** — hostname-scoped `308` Redirect Rule; zone-wide `Always Use HTTPS` still OFF (§8) |
| 45 (CF-D3) — preview origin does not survive reboot | **EXPLICITLY DEFERRED** — temporary dev listener by design (§6) |

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

> **Still not enabled: Always Use HTTPS.** The zone-wide toggle remains OFF, and
> deliberately so — turning it on would also change `api.*` and `mcp.*` for
> existing machine clients. HTTPS on the Workbench hostname is instead enforced
> by a *hostname-scoped* `308` Redirect Rule. Verified 2026-09-25; discovery 44
> (CF-D2) resolved. See §8, including how the toggle's state is established
> behaviourally rather than assumed.

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
| Drop-in | `~/.config/systemd/user/cloudflared.service.d/10-restart.conf` |
| Tracked source for the drop-in | `runtime/config/systemd/cloudflared.service.d/10-restart.conf` |
| Command | `cloudflared tunnel run cis-creative-vm` |
| Restart policy | `Restart=always`, `RestartSec=5` (from the drop-in) |
| Enabled | `enabled`, `WantedBy=default.target` |
| User linger | `yes` for uid 1000 (`/var/lib/systemd/linger/eric`) |
| Config mode | **Locally-managed** — ingress lives in a local file, *not* the dashboard |
| Ingress file | `~/.cloudflared/config.yml` |
| Credentials | `~/.cloudflared/<uuid>.json` — never open or print |
| Origin cert | `~/.cloudflared/cert.pem` — never open or print |

Three consequences worth internalising:

1. **Ingress cannot be changed from the Cloudflare dashboard.** The dashboard
   does not hold this tunnel's routing. Edit `~/.cloudflared/config.yml`.
2. **Use `systemctl --user`, not `sudo systemctl`.** It is a user unit.
3. **It does start at boot without anyone logging in.** Linger is enabled for
   uid 1000, so `user@1000.service` — and with it `default.target` and this
   unit — comes up at boot. An interactive or graphical login is not required.

### Restart policy — the tracked drop-in

The desired policy is **not** stored only under `$HOME`. The tracked source of
truth is:

```
runtime/config/systemd/cloudflared.service.d/10-restart.conf
```

```ini
[Service]
Restart=always
RestartSec=5
```

Install or re-install it on the live host with:

```bash
install -D -m 0644 \
  /mnt/projects/cis/runtime/config/systemd/cloudflared.service.d/10-restart.conf \
  ~/.config/systemd/user/cloudflared.service.d/10-restart.conf
systemctl --user daemon-reload
systemctl --user show cloudflared.service -p Restart -p RestartUSec -p DropInPaths
```

`daemon-reload` is enough — the new policy applies to the already-running unit.
No restart, and therefore no outage, is needed to install it.

#### Why `Restart=always` and not `Restart=on-failure`

The base unit has carried `Restart=on-failure` since 2026-05-09, and the tunnel
*still* stayed down for 3m14s after the SIGHUP incident. That is not a bug — it
is documented systemd behaviour. Under `Restart=on-failure`, systemd treats
termination by **SIGHUP, SIGINT, SIGTERM or SIGPIPE** as a *clean* exit and
does not restart (`man systemd.service`, `Restart=`; confirmed on systemd 255).
SIGHUP is precisely how this cloudflared build dies.

`Restart=always` is the only setting that covers a clean-looking termination as
well as a crash. Do not "simplify" it back to `on-failure`.

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
> restarted. Tracked as discovery 45 (CF-D3), which remains **explicitly
> deferred**: this is a temporary OIDC development listener, and production
> Workbench activation will run under the production runtime path rather than
> promoting the preview into a daemon. Do not add a systemd unit for it.

### Running the preview origin (manual, by design)

```bash
# start (verified 2026-09-24; foreground, loopback-only)
cd /mnt/projects/cis
python3 -m tools.development.oidc_preview serve --port 5055

# confirm it is running
ss -ltnp | grep 5055            # expect 127.0.0.1:5055, python3
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:5055/   # expect 200

# stop
# Ctrl-C in its terminal, or:
pkill -f 'tools.development.oidc_preview serve'
```

If it is down, `workbench.creative-intelligence-system.com` returns 502 from
Cloudflare while the tunnel itself stays healthy. That is a preview-origin
outage, not a tunnel outage — check `ss -ltnp | grep 5055` before touching
`cloudflared`.

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
(`code=killed, signal=HUP`). Because `Restart=on-failure` classifies SIGHUP as
a clean exit, systemd did **not** bring it back: a 3m14s outage across *all*
hostnames until someone restarted it by hand.

**Never send `SIGHUP` to this installation.** There is no reload path. The
correct change procedure is:

```bash
# 1. edit ~/.cloudflared/config.yml
# 2. validate BEFORE touching the running process
cloudflared tunnel ingress validate
cloudflared tunnel ingress rule https://<hostname>/     # confirm the match
# 3. controlled restart
systemctl --user restart cloudflared.service
# 4. confirm
systemctl --user show cloudflared.service -p MainPID -p ActiveState -p SubState
cloudflared tunnel info cis-creative-vm                 # expect 4 connections
```

Expect a few seconds of downtime on every hostname; there is no zero-downtime
reload for a locally-managed tunnel.

### Unexpected process death now self-heals (discovery 43, resolved)

With `Restart=always` / `RestartSec=5` in place, an unexpected death no longer
takes CIS off the Internet until a human notices. Verified 2026-09-24 by
`SIGKILL`ing the supervised MainPID — not `systemctl stop`, which is an
administrative stop and would not exercise the restart path:

| Measurement | Value |
|---|---|
| Old MainPID | 1347107 |
| Termination | `SIGKILL` at 14:45:18.768Z → `code=killed, status=9/KILL` |
| systemd action | `Scheduled restart job, restart counter is at 1` at 14:45:23 |
| New MainPID | 1603879, live at t+5.44s |
| `NRestarts` | 0 → 1 |
| Tunnel reconnect | 4 edge connections re-registered by t+7.5s (ord07, ord11, msp01 ×2) |
| Workbench first good response | t+6.09s |
| Manual `systemctl start` | **none — recovery was fully automatic** |

`mcp.*` (403) and `api.*` (302 → Access) answered from Cloudflare's edge
throughout and never returned an origin error, so `workbench.*` is the only
externally observable origin-liveness signal of the three. All three ride the
same tunnel process, so its reconnection covers all three.

### Health checks

```bash
systemctl --user status cloudflared
systemctl --user show cloudflared.service -p Restart -p RestartUSec -p NRestarts
loginctl show-user "$USER" | grep Linger      # expect Linger=yes
cloudflared tunnel info cis-creative-vm       # expect 4 edge connections
journalctl --user -u cloudflared -n 50
```

A healthy tunnel registers ~4 connections across two Cloudflare colos
(observed: `ord08` ×2, `msp01` ×2 before the restart; `ord07`, `ord11`,
`msp01` ×2 after — the colo mix varies and is not a fault signal).

### Version

2026.3.0 is installed; cloudflared reports 2026.9.1 available. Upgrading is an
unrelated change with its own outage risk — do it deliberately, not as a side
effect of another task.

---

## 8. HTTP → HTTPS on the Workbench hostname (discovery 44, RESOLVED)

**Resolved 2026-09-25.** Plain HTTP to the Workbench hostname now redirects to
HTTPS. Previously it was *served* — `200 text/html` at `/`, no `Location`
header — which is what discovery 44 recorded.

### The rule

A **hostname-scoped wildcard Single Redirect**, created in the Cloudflare
dashboard (Rules → Redirect Rules), named `workbench-https-only`:

| Field | Value |
|---|---|
| Match | `http://workbench.creative-intelligence-system.com/*` |
| Target | `https://workbench.creative-intelligence-system.com/${1}` |
| Status | `308` Permanent Redirect |
| Preserve query string | ON |

`308` rather than `301` is the better choice here: it preserves the request
method and body, so a `POST` to an OIDC endpoint over HTTP is replayed as a
`POST` over HTTPS rather than being silently downgraded to a `GET`.

### Verified behaviour

Every case below returns `308` with the scheme swapped and everything else
intact:

| Request path | `Location` |
|---|---|
| `/` | `https://workbench.…/` |
| `/api/workbench/auth/session` | `https://workbench.…/api/workbench/auth/session` |
| `/login?next=%2Fcards` | `https://workbench.…/login?next=%2Fcards` |
| `/a/b/c/deep/path` | preserved |
| `/x?a=1&b=2&c=hello%20world` | preserved, multi-param |
| `/p%C3%A4th/%C3%BCnicode` | preserved, percent-encoding intact |
| `/trailing/` | trailing slash intact |
| `/?onlyquery=1` | query-only intact |

`HEAD` and `POST` both redirect and keep their method. Following the redirect
lands on the right place with valid TLS — `num_redirects=1`, `http_version=2`,
`ssl_verify_result=0`, no `curl -k` anywhere:

```
http://workbench.…/                          -> 200  https://workbench.…/
http://workbench.…/login?next=%2Fcards       -> 200  https://workbench.…/login?next=%2Fcards
http://workbench.…/api/workbench/auth/session-> 503  https://workbench.…/api/workbench/auth/session
```

(The `503` is the preview reporting OIDC unconfigured — discovery 39 — not a
redirect fault.) No redirect leaves the domain, and none lands on Cloudflare
Access.

### Scope: the zone-wide toggle is still OFF

**`Always Use HTTPS` was not enabled, and this work never enabled it.** That is
not an assumption — the zone settings API is denied to the only credential on
this host, so it is established behaviourally:

All four hostnames in the zone are proxied (from the DNS API, which the token
*can* read: apex, `api.*`, `mcp.*`, `workbench.*`, all `proxied=True`).
`Always Use HTTPS` is a zone-wide edge redirect applied to every proxied
hostname before origin resolution, so if it were on, the apex would `301`
instead of reaching an origin error. It does not:

```
http://creative-intelligence-system.com/   ->  530  (origin error 1016), no Location
```

A proxied hostname that reaches an origin error over plain HTTP proves the
zone-wide redirect is not running. The toggle is off.

### `api.*` and `mcp.*` — what is and is not known

Both now answer plain HTTP with `301` to their **own** HTTPS host:

```
http://api.../zzz?k=v  ->  301  https://api.../zzz?k=v
http://mcp.../zzz?k=v  ->  301  https://mcp.../zzz?k=v
```

**This is not the Workbench rule.** That rule rewrites to a literal
`workbench.*` URL; anything it matched would be sent there. These preserve each
hostname's own host, and they answer `301` where the Workbench rule answers
`308` — a different layer (they also carry `alt-svc: h3=":443"`, which the
Workbench `308` does not).

**Honest gap:** no plain-HTTP baseline for `api.*` or `mcp.*` was ever captured
— not by this card's first pass, which compared HTTPS responses only, and not
anywhere else in the repo. So it cannot be *proven* from evidence whether that
`301` predates the Workbench rule. What is proven is that it is neither the
Workbench rule nor the zone-wide toggle, and that both hostnames still end at
their established protected responses:

```
http://api.*  -L  ->  cis-live.cloudflareaccess.com/cdn-cgi/access/login/…  (200)
http://mcp.*  -L  ->  https://mcp.*  403
https://api.*     ->  302 Access      (identical to the pre-rule baseline)
https://mcp.*     ->  403             (identical to the pre-rule baseline)
```

The likely explanation is Cloudflare Access, which forces HTTPS on the
hostnames it protects because its session cookies are `Secure`-only. §4 of this
document records exactly the right split: `api.*` has the "Eric only" Allow
application and `mcp.*` has the MCP Service Token application, while
`workbench.*` has **no** Access application at all. The two hostnames that
`301` are precisely the two with Access in front; the one that did not redirect
until a rule was added is precisely the one without. That asymmetry *is*
discovery 44.

If you want this closed off completely, confirm in the dashboard that
SSL/TLS → Edge Certificates → **Always Use HTTPS** reads OFF and that Redirect
Rules contains `workbench-https-only` and nothing targeting `api.*` or `mcp.*`.

### If the rule ever needs rebuilding

Re-verify with (no `-k`):

```bash
curl -sS -D - -o /dev/null http://workbench.creative-intelligence-system.com/
curl -sS -D - -o /dev/null 'http://workbench.creative-intelligence-system.com/login?next=%2Fcards'
curl -sSL -o /dev/null -w '%{http_code} ssl_verify=%{ssl_verify_result}\n' \
  http://workbench.creative-intelligence-system.com/
```

Expect `308` with `Location` on the same host and path, then `200 ssl_verify=0`.

No credential on this host can create or read that rule: the cloudflared origin
certificate's embedded token is denied on Rulesets, Page Rules, Worker routes
and Zone Settings. Changing it is a dashboard action, or needs a token scoped to
Zone → Rules → Ruleset:Edit stored outside the repo.


## 9. Access remains off the Workbench hostname

`workbench.creative-intelligence-system.com` intentionally has **no Cloudflare
Access application**. The authentication path is:

```
Browser → Cloudflare Tunnel → CIS Workbench → Auth0/OIDC
```

not a Cloudflare Access login in front of it. Verified unchanged before and
after this card's work: `api.*` still `302`s to
`cis-live.cloudflareaccess.com`, `mcp.*` still returns `403` at the edge, and
`workbench.*` still returns `200` with no Access interception. No Access
application was created, modified or deleted.
