# Cloudflare Connections — CIS

Authoritative inventory of every Cloudflare connection CIS depends on: the
zone, the tunnels, every public hostname, what each one points at, and which
Access policy guards it.

Last verified **2026-10-11** against the live system (WB1-REV127 edge-containment
closeout; supersedes the public-listener containment card of 2026-10-10, the
tunnel-durability card of 2026-09-25, and the stable-origin card of 2026-09-24).

> **Read §10 before trusting §3, §5, §8's `api.*`/`mcp.*` subsection or §9.**
> Those sections were written when `workbench.*` had no Cloudflare Access
> application — first while it pointed at the loopback-only OIDC preview on
> port 5055, then after it was repointed at the authoritative production
> listener on port 5000 (2026-10-01, WB1-D17), which is what made the absence
> expensive. **That is no longer the configuration.** `workbench.*` now has a
> whole-host Access application, verified 2026-10-11. §5 and §9 are retained
> as superseded history and must not be read as current state. §10 records
> what was exposed, the application-layer containment, and the edge
> containment that now sits in front of it.

Discovery status as of this revision:

| Discovery | State |
|---|---|
| **127 — public trust-boundary exposure on the authoritative listener** | **CONTAINED AT BOTH LAYERS** — Access at the edge *and* fail-closed application authorization; pending independent review, not self-accepted (§10) |
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
| `workbench.creative-intelligence-system.com` | `localhost:5000` | **Authoritative production listener** (`runtime/container_app.py` in `cis-pipeline`) since 2026-10-01, WB1-D17 — *not* the port-5055 preview any more | **"Eric only" Allow**, whole host, no path exception — `GET` on *any* path returns 302 to the Access login. See §10. |

Ingress is first-match and ordered; the catch-all must stay last:

```yaml
ingress:
  - hostname: mcp.creative-intelligence-system.com
    service: http://localhost:8888
  - hostname: api.creative-intelligence-system.com
    service: http://localhost:5000
  - hostname: workbench.creative-intelligence-system.com
    service: http://localhost:5000     # was 127.0.0.1:5055 until WB1-D17
  - service: http_status:404
```

The live file carries a long comment on the `workbench.*` rule. As of the
revision-127 containment that comment states the SEVEN blueprints the listener
actually registers; it previously claimed two, and that false claim is why the
exposure in §10 was not visible at the point of the ingress change.

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
| Eric only | Allow | 2 — `api.*` and `workbench.*` (the latter added 2026-10-11, §10) |
| API Service Token | Service Auth | 0 — currently inert |
| MCP Service Token | Service Auth | 1 — `mcp.*` |

The "Eric only" policy is a **reusable** policy: both applications reference the
same policy object rather than carrying a copy, so its include selector is
defined once. That selector is a single **exact email** — the operator's own
address, one address and no other (the value is in the dashboard, not here).
Critically it is **not** an email-*domain* selector, so no one else at that mail
provider inherits access. There is no service-auth policy and no bypass policy
on either application.

Access is applied **per application**, and all three public hostnames now have
one:

| Application | Hostname | Action | Scope |
|---|---|---|---|
| CIS Workbench | `workbench.*` | Allow — "Eric only" | whole host, no path |
| (api) | `api.*` | Allow — "Eric only" | whole host |
| (mcp) | `mcp.*` | Service Auth — MCP Service Token | whole host |

There is still no zone-wide or wildcard application; each is scoped to its own
hostname, and each therefore presents its **own** Access audience (`aud`/`kid`).
A differing audience between these hostnames is expected and is not a fault.

---

## 5. Why the Workbench hostname had no Access policy — SUPERSEDED

> **SUPERSEDED BY §10 — this is history, not current state.** `workbench.*`
> now **has** a whole-host Access application. Two claims below are now false
> and are kept only to show what was believed and why:
>
> 1. "**reversing it would break the product**" — measured false on
>    2026-10-11. Access in front of the hostname does *not* break the Auth0
>    callback, because the browser that reaches the callback is already
>    carrying the Cloudflare authorization cookie from the Access login it
>    completed moments earlier. The full flow was driven end to end. See §10.
> 2. "the origin binds `127.0.0.1:5055` only" and "the preview app registers
>    *only* the auth surface" — both stopped being true on 2026-10-01
>    (WB1-D17), when the hostname was repointed at the authoritative
>    production listener. Revision 127 is the consequence.
>
> What survives from this section is the *cost* it correctly identified: Access
> does insert a second, unrelated login. That cost was weighed and
> **deliberately accepted** rather than disproved. See §10.

This was intentional, and the belief at the time was that reversing it would
break the product.

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
hostnames it protects because its session cookies are `Secure`-only. At the
time this was written the split was: `api.*` had the "Eric only" Allow
application and `mcp.*` had the MCP Service Token application, while
`workbench.*` had **no** Access application at all. The two hostnames that
`301` were precisely the two with Access in front; the one that did not
redirect until a rule was added was precisely the one without. That asymmetry
*is* discovery 44.

> **Correction, 2026-10-11.** The premise of that asymmetry no longer holds:
> `workbench.*` now has its own whole-host Access application (§4, §10), so all
> three hostnames have Access in front of them. This does **not** invalidate
> discovery 44 or its resolution — the hostname-scoped `308` Redirect Rule is
> still in place and still the thing that closed it, and the explanation above
> remains the best account of why only `workbench.*` ever needed one. It does
> mean the sentence "`workbench.*` has no Access application at all" must not
> be lifted out of this section as current state. The open question that
> remains is unchanged and still only cosmetic: whether `api.*`/`mcp.*` would
> now be reached by their own `301` or by Access's HTTPS enforcement first.

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


## 9. Access was off the Workbench hostname — RETIRED, NO LONGER TRUE

> **RETIRED 2026-10-11. Do not act on this section.** Its central claim —
> that `workbench.creative-intelligence-system.com` has no Cloudflare Access
> application — is **false as of 2026-10-11**. The hostname has a whole-host
> Access application using the reusable exact-email "Eric only" Allow policy.
> The authoritative description of the current edge posture and the
> authentication path is **§10**. This heading is kept, rather than deleted,
> so that anything citing "§9" lands on the correction instead of silently
> reading stale state.

The retired claim, for the record, was: this hostname intentionally has no
Access application, and the authentication path is

```
Browser → Cloudflare Tunnel → CIS Workbench → Auth0/OIDC
```

with no Access login in front of it. The current path has an Access login in
front of it and is recorded in §10.

---

## 10. Revision 127 — the public listener exposure, and what contains it

Recorded at `dev_continuity_events` revision 127 (`task='WB.1'`,
`kind='unfinished_work'`, `status='BEFORE_STAGE_CLOSEOUT'`). Contained in the
application on **2026-10-10** by the WB.1-TRUST-127 card, and at the edge on
**2026-10-11** by the WB1-REV127 edge-containment closeout. Both halves of the
defence-in-depth requirement are now in place and verified.

**Revision 127 is nevertheless not closed by this document.** It is *ready for
independent review*. The sessions that implemented the containment do not
accept their own work, and no Eric Gate approval was written. Do not read this
section as "revision 127 is resolved".

### What was exposed

At the time of the exposure `workbench.*` had no Access application, and since
WB1-D17 it forwards to the authoritative production listener. That listener registers **seven**
blueprints, not the two §5/§6 describe, and before this card only two of the
seven checked a credential. Measured at the edge on 2026-10-10, with no
credential presented, every one of these answered `200` with real data:

| Surface | Route | Response |
|---|---|---|
| Canonical state | `/api/workbench/system-context` | 200, 295 KB |
| Recovery packet | `/api/workbench/system-context/recovery-packet` | 200 |
| Build path | `/api/workbench/build-path` | 200, 126 KB |
| Destination architecture | `/api/workbench/destination-architecture` | 200, 183 KB |
| Project intelligence | `/api/workbench/project-intelligence` | 200, 960 KB |
| Enforcement/security audit | `/api/relay/system/security` | 200 |
| Gateway health | `/api/relay/system/health`, `/api/relay/health` | 200 |
| Gateway logs | `/api/relay/system/logs/<container>` | 200, 4.8 KB of pipeline log |
| Relay runs / metrics / KB decisions | `/api/relay/runs`, `/metrics`, `/kb/decisions` | 200, 123 KB on decisions |
| Guardrails / DLQ / projects | `/api/relay/guardrails`, `/dlq`, `/api/projects` | 200 |

The cause was not an oversight on one route. `runtime/api/relay.py::_check_auth`
was fail-open **by construction** —

```python
def _check_auth():
    if not API_KEY:
        return None          # unset key = auth skipped entirely
```

— and `CIS_PIPELINE_API_KEY` is empty in the running container, so *every*
relay route was unauthenticated, including `POST /api/relay/start` and
`/api/relay/run` (which begin a real pipeline run and spend model tokens),
`POST /api/relay/<run_id>/gate` (the Eric Gate approval path), `/answer`,
`/decompose` and `POST /api/projects`. **The mutating routes were never
exercised against the live system, by this card or the one that found it.**

### What contains it now (application layer)

Every route above is behind `runtime/workbench_auth.check_auth()` — the same
reviewed contract `workbench_app`, `card_factory_app`, `card_runner` and
`braingate_conversation` already used. No parallel identity system was added
and no bypass flag exists. The contract:

| Condition | Result |
|---|---|
| Valid `Bearer` matching `CIS_PIPELINE_API_KEY` | allowed |
| Valid Workbench session cookie, identity still on the allowlist | allowed (+ CSRF on mutations) |
| A mechanism configured, credential absent or wrong | **401** |
| No mechanism configured at all | **503** — still a denial, never anonymous access |

The browser path is unaffected because the session cookie is scoped to
`/api/workbench`, which is exactly where the four read models live. The SPA
never calls `/api/relay/*`.

The complete unauthenticated surface of the listener is now, and is asserted
to be exactly:

- fixed-result liveness — `/api/relay/ping`, `/api/ping`, `/health`, `/api/health`;
- the OIDC sign-in lifecycle — `/api/workbench/auth/{login,callback,session,logout}`,
  which cannot sit behind the credential check because it is how a credential
  is obtained, and which guards itself (issuer/audience/nonce/PKCE + the
  server-side allowlist);
- the static SPA shell — `/`, `/ui/`, `/ui/<path>`, `/dashboard/`.

`runtime/tests/test_revision_127_containment.py` pins that set. A route added
later without a credential check fails check C3 rather than quietly joining the
public surface.

Verified live at the edge after deployment, no credentials sent: all 18
protected GETs and all 12 protected POSTs answer `401` with a 95-byte generic
refusal. No workflow run, project, approval or spine row was created by the
verification, and no model token was spent.

### Deny-by-default at the edge — IMPLEMENTED 2026-10-11

Revision 127 calls for defence in depth: fail-closed application authorization
**and** deny-by-default public ingress. **Both are now in place.** The
subsection this replaces recorded the edge half as BLOCKED on two
prerequisites; both were cleared — the credential/authority by performing the
change in the Zero Trust dashboard, and the architect decision by **choosing
the first of the three options it listed: accept the double login.**

| Hostname | Edge posture |
|---|---|
| `api.*` | Cloudflare Access enforced — `302` to `cis-live.cloudflareaccess.com`, `auth_status=NONE` |
| `mcp.*` | Cloudflare Access enforced — `403` at the edge, with `cf-access-aud` |
| `workbench.*` | **Cloudflare Access enforced** — `302` to `cis-live.cloudflareaccess.com` on every path |

#### The application

| Item | Value |
|---|---|
| Name | CIS Workbench |
| Type | Self-hosted |
| Hostname | `workbench.creative-intelligence-system.com` |
| Path | **none — the application protects the entire hostname** |
| Session duration | **8 hours** |
| Policy | the existing **reusable** "Eric only" policy (§4) |
| Policy action | Allow |
| Include selector | **exact email**, one address |
| Identity provider | Cloudflare One-time PIN available; CIS Auth0 remains the *application* login |

What the application deliberately does **not** have — each of these was
considered and rejected, not merely omitted:

- **no bypass policy**;
- **no service-auth policy**;
- **no email-domain selector** (exact email only, so a whole domain cannot
  inherit access);
- **no unauthenticated exception for the Auth0 callback**;
- **no path exception of any kind** — the application is defined with no path,
  which is what makes "every path" the default rather than a list that must be
  maintained.

#### The browser flow, and why the callback survives

```
Browser → Cloudflare Access (one-time PIN)
        → CIS Auth0 login
        → /api/workbench/auth/callback
        → authenticated Workbench SPA
```

§5 predicted that an Access application would intercept the Auth0 callback at
`/api/workbench/auth/callback` and break sign-in. **It does not, and the reason
is specific:** by the time Auth0 redirects the browser back to the callback,
that browser has already completed the Access login and is carrying the
Cloudflare authorization cookie for this application. The callback request
therefore arrives *authorized at the edge* and is passed to the origin like any
other authorized request. Access only intercepts requests that do not yet carry
that cookie — which is exactly the anonymous case it is there to stop. **No
callback bypass was needed, and none was created.**

This is the **deliberately accepted double login**: the first of the three
alternatives the former "BLOCKED" subsection listed. Signing in costs two
logins (Access, then Auth0). That was judged the right trade against leaving
the authoritative listener without deny-by-default ingress. The third option —
splitting the listener so the relay/API surface moves behind `api.*` — remains
the option that removes the tension rather than trading it off, and remains
available as future work; accepting the double login does not foreclose it.

#### Verified 2026-10-11

Driven end to end in a browser: Access one-time PIN → Auth0 → callback →
authenticated SPA, which rendered the owner identity and then loaded **real
data** through that authenticated session on the Project Map, Build Path,
System Context / Recovery, and the Braingate conversation/project list. This is
the positive half of the proof: Access denies anonymous traffic *without*
denying the legitimate user.

Anonymously from outside that session — **no cookie, no `Authorization`
header, no service token, no credential of any kind** — all of the following
return `302` to `cis-live.cloudflareaccess.com` with the CIS Workbench
audience, a 143-byte Cloudflare-generated redirect page, `server: cloudflare`,
`auth_status: NONE`, `service_token_status: false`, and **no origin body and no
operational state**:

```
/                                       /api/workbench/project-intelligence
/ui/                                    /api/relay/ping
/api/workbench/auth/login               /api/relay/health
/api/workbench/auth/callback            /api/relay/runs
/api/workbench/auth/session             /api/relay/system/security
/api/workbench/system-context           /dashboard/
/api/workbench/build-path               /favicon.ico
/api/workbench/destination-architecture /some/random/path
```

The last four are the whole-host check: paths the origin does not even
register, plus `/dashboard/` — which the application layer leaves
unauthenticated by design and which revision 127's containment work had to
declare as a residual item — are now intercepted before the origin sees them,
because the application carries no path and so has nothing to enumerate.

Re-verify with (note: **GET/HEAD only** — do not probe mutating routes):

```bash
for p in / /ui/ /api/relay/runs /api/workbench/system-context /some/random/path; do
  curl -sS -o /dev/null -D - "https://workbench.creative-intelligence-system.com$p" \
    | grep -iE '^HTTP/|^server:|^location:' | cut -c1-80
done
```

Expect `HTTP/2 302`, `server: cloudflare`, and a `Location` on
`cis-live.cloudflareaccess.com/cdn-cgi/access/login/workbench.creative-intelligence-system.com`.
That the redirect is Cloudflare-generated is what proves the origin was not
reached: the origin's own refusal is a 95-byte JSON `401`, never a 302. (The
`cis-pipeline` container does not log inbound requests, so log *absence* proves
nothing here and is not relied on.)

Each hostname presents its own audience; `api.*` and `mcp.*` differing from
`workbench.*` is correct, not a regression (§4).

#### Application authorization is still required

The edge is now the outer of two controls, **not a replacement for the inner
one**. Every protected route must keep calling
`runtime/workbench_auth.check_auth()`, and
`runtime/tests/test_revision_127_containment.py` must keep passing, because:

- an Access application can be edited, scoped, bypassed or deleted in the
  dashboard by anyone with account access, and nothing in this repository would
  notice;
- the origin is reachable from this host and from anything else that can reach
  `localhost:5000` — a path that does not traverse Cloudflare at all;
- defence in depth is the explicit requirement of revision 127. One control is
  not two.

Verified the same day, with the edge deliberately bypassed by requesting
`127.0.0.1:5000` directly and sending no credential: the protected Workbench
read models and the relay surface each answered `401` with the 95-byte generic
refusal. `/api/workbench/auth/session` answered `200` with
`{"authenticated": false, …}`, which is the intended unauthenticated sign-in
lifecycle endpoint and carries no operational state. **Both layers hold
independently.**

#### Machine callers

`CIS_PIPELINE_API_KEY` remains **unset**, so the relay/API surface is closed to
every machine caller, not merely to unauthenticated ones. That is fail-closed
and correct, and nothing currently depends on it. **No key was minted** —
creating a production credential is an operator action and was not requested.
A machine caller would additionally now have to satisfy Access, which for a
non-browser client means a service token; none is configured for this
application, and adding one would be a new decision.
