You are working in the CIS repository at:

`/mnt/projects/cis`

# CARD

**WB.1 — Stable Cloudflare Workbench Origin & Access Policy**

## ROLE

Act as the implementation/infrastructure agent.

The user has confirmed through the Cloudflare dashboard that the Cloudflare account already contains the active domain:

`creative-intelligence-system.com`

Therefore the temporary `*.trycloudflare.com` development plan is superseded.

The intended stable Workbench public origin is:

`https://workbench.creative-intelligence-system.com`

This card establishes and proves that stable HTTPS origin using the user's **existing Cloudflare account and existing named Cloudflare Tunnel**.

This card does **NOT** configure Auth0 yet.

This card does **NOT** activate production Braingate.

---

# 1. CURRENT ACCEPTED STATE

Current WB.1 OIDC implementation commit:

`b65a90e24c3d03d6b5000584e18ac37d62d4d9a0`

The subsequent activation-readiness work was committed as:

`13b5a2b...`

Before proceeding, determine and record the complete current SHA.

The preceding card established:

- OIDC code is committed
- OIDC dependencies are available/reproducible
- Braingate-stage UI corrections are implemented
- security/regression suites pass
- production Workbench remains unactivated
- migrations 0035/0036/0037/0038 remain unapplied
- external login proof is blocked because no OIDC provider/configuration exists yet

The current external infrastructure includes:

- Cloudflare account
- active `creative-intelligence-system.com` zone
- an existing named `cloudflared` tunnel
- existing Cloudflare Access configuration may already protect infrastructure around port 5000

Do not assume how that tunnel or Access policy is configured.

Inspect it.

---

# 2. GOAL

Establish a stable development/testing origin:

`https://workbench.creative-intelligence-system.com`

using the existing Cloudflare named tunnel.

At completion, prove:

1. DNS/public hostname exists.
2. HTTPS works with a valid Cloudflare-served certificate.
3. Traffic reaches a deliberately chosen CIS preview/test origin.
4. It does NOT accidentally expose additional production CIS capabilities.
5. Cloudflare Access does not create an unwanted second login or block the future Auth0 callback.
6. Existing Cloudflare hostnames/tunnel routes are unchanged.
7. Production `cis-pipeline` remains unactivated for Workbench/Braingate.

This stable origin will be used by the **next card** to configure Auth0.

---

# 3. PRESERVE REPOSITORY AND INFRASTRUCTURE STATE

Before modifying anything:

```bash
cd /mnt/projects/cis
git status --short
git rev-parse HEAD
git rev-parse origin/master
```

Record both SHAs.

Do not:

- reset
- clean
- stash
- overwrite unrelated work
- modify Chroma work
- modify unrelated queue work

Also inspect the currently running Cloudflare infrastructure before touching it.

Record, without printing secrets:

- `cloudflared` process/service status
- version
- existing named tunnel identity/name
- current ingress configuration source
- existing public hostnames
- local services each hostname targets
- whether configuration is local-file-managed, dashboard-managed, remotely managed, or another supported arrangement
- whether Cloudflare Access policies apply to the existing CIS hostnames

Do not print:

- tunnel credentials
- API tokens
- certificates/private keys
- secret configuration values

---

# 4. DO NOT USE QUICK TUNNEL

Do NOT create a temporary:

`*.trycloudflare.com`

Quick Tunnel.

The domain:

`creative-intelligence-system.com`

is already available.

The stable hostname for WB.1 is:

`workbench.creative-intelligence-system.com`

Do not introduce an alternate hostname unless deterministic technical evidence shows that hostname cannot be used.

If that occurs, STOP and report the reason instead of silently choosing another name.

---

# 5. INSPECT THE EXISTING NAMED TUNNEL

Determine how the existing tunnel is configured.

Inspect appropriate Cloudflare/cloudflared configuration and commands.

At minimum establish:

- tunnel name/UUID without exposing credentials
- whether it is currently healthy
- which hostnames it serves
- which local services they target
- whether ingress rules are ordered
- whether a catch-all exists
- whether adding `workbench.creative-intelligence-system.com` would conflict with an existing route
- whether changing the configuration requires a `cloudflared` reload/restart
- whether that operation would interrupt existing CIS services

Do NOT modify an existing unrelated hostname.

Do NOT replace the tunnel.

Do NOT create a second tunnel unless the existing tunnel genuinely cannot provide an isolated Workbench hostname and that limitation is documented first.

Preferred architecture:

**one existing named Cloudflare Tunnel**

with an additional isolated hostname:

`workbench.creative-intelligence-system.com`

---

# 6. DETERMINE THE SAFE LOCAL ORIGIN

Do NOT simply point the new public hostname at production port 5000 without inspecting what that would expose.

The Workbench/OIDC external proof should use the already-built **controlled preview/test surface** if one exists.

Inspect the committed WB.1 implementation for the existing OIDC/Braingate preview server or test application.

The selected origin must expose only what is required for the upcoming external login proof, such as:

- Workbench UI
- OIDC login route
- OIDC callback
- OIDC session/status
- logout
- Braingate-stage preview behavior if required

It must NOT expose:

- Card Factory
- Card Runner
- proposal confirmation
- proposal approval
- implementation dispatch
- reviewer dispatch
- unrestricted `workbench_bp`
- unrelated production administration endpoints

Prefer a listener bound to loopback:

`127.0.0.1:<dedicated-preview-port>`

rather than an externally bound listener.

The Cloudflare Tunnel should be the public ingress.

---

# 7. IF NO SUITABLE PREVIEW LISTENER EXISTS

If the committed WB.1 work already contains an appropriate preview server, reuse it.

Do not create a second implementation unnecessarily.

If no safe preview listener exists, create the **smallest possible** dedicated preview entry point that registers only the previously reviewed authentication/preview surfaces.

Do not duplicate OIDC logic.

Import the reviewed blueprints/modules.

Do not register:

`workbench_bp`

Do not register Card Factory.

Do not register Card Runner.

Do not apply migrations.

Do not create production state.

Any new preview code must be deterministic and tested.

---

# 8. CLOUDFLARE ACCESS — DISCOVERY 32

This is a required architectural check.

Determine whether Cloudflare Access currently applies to:

`workbench.creative-intelligence-system.com`

or would apply through:

- a wildcard application
- zone-wide policy
- existing hostname pattern
- tunnel policy
- another Access configuration

The intended Workbench user experience is:

**Workbench → Sign In → Auth0 → Google or email/password → Workbench**

We do NOT want:

**Cloudflare Access login → Workbench → Auth0 login**

unless that double-authentication architecture is explicitly chosen later.

Cloudflare Tunnel provides network ingress.

Auth0/CIS provides the application login.

They are separate responsibilities.

---

# 9. DESIRED ACCESS RESULT

For this Workbench hostname, the preferred result is:

**Cloudflare Tunnel protects/hides the origin, but Cloudflare Access does not intercept normal Workbench/Auth0 authentication.**

At minimum, these paths must be able to reach CIS without being replaced by a Cloudflare Access login:

- `/`
- `/api/workbench/auth/login`
- `/api/workbench/auth/callback`
- `/api/workbench/auth/session`
- `/api/workbench/auth/logout`

Do not solve this by weakening CIS authentication.

Do not expose downstream CIS capabilities.

If an existing wildcard Access policy applies, determine the safest narrowly scoped configuration that prevents it from breaking the Workbench OIDC flow.

Prefer a hostname-specific policy decision over broad changes to existing Cloudflare Access protection.

Do not alter unrelated Access applications.

---

# 10. ACCESS POLICY SAFETY

Before changing Cloudflare Access configuration, record the existing policy behavior.

If a change is necessary:

- scope it only to the Workbench hostname or exact required paths
- preserve unrelated applications
- preserve unrelated policies
- do not create an "Allow everyone" rule across the entire domain
- do not disable Cloudflare security globally
- do not change unrelated tunnel routes

If available configuration/credentials do not permit safe modification from the development machine:

STOP and return:

`BLOCKED — CLOUDFLARE_ACCESS_USER_ACTION_REQUIRED`

with exact non-secret dashboard instructions for Eric.

Do not guess.

---

# 11. CREATE THE STABLE PUBLIC HOSTNAME

Configure:

`workbench.creative-intelligence-system.com`

to the existing named tunnel and selected safe local preview origin.

Use the supported method for the tunnel's actual management mode.

This may involve:

- Cloudflare dashboard public hostname configuration
- tunnel ingress configuration
- DNS route creation
- another existing approved method

Do not create conflicting duplicate DNS records.

Do not remove existing DNS records.

Do not proxy directly to a public port.

The intended routing is conceptually:

```text
https://workbench.creative-intelligence-system.com
        |
        v
Cloudflare edge / TLS
        |
        v
existing named Cloudflare Tunnel
        |
        v
127.0.0.1:<safe-preview-port>
```

---

# 12. TLS / HTTPS PROOF

From an external/public path, prove:

`https://workbench.creative-intelligence-system.com`

is reachable over HTTPS.

Record:

- HTTP status
- certificate validation result
- redirect behavior
- final destination
- selected response headers needed for diagnosis
- whether traffic reached the intended local preview service

Do not disable certificate verification.

Do not use `curl -k` as successful evidence.

If `curl -k` is used diagnostically, clearly mark it as diagnostic only and still require a normal verified TLS request for PASS.

---

# 13. ROUTE PROOF

Using the stable hostname, verify the authentication routes can reach the preview application.

Because Auth0 is not yet configured, a login endpoint may legitimately return a fail-closed configuration response such as 503.

That is acceptable for this card.

What matters here is differentiating:

**Cloudflare route works and CIS says OIDC is not configured**

from:

**Cloudflare/Access/DNS prevented the request from reaching CIS**

Test at minimum:

- `/`
- `/api/workbench/auth/login`
- `/api/workbench/auth/session`
- `/api/workbench/auth/logout` as appropriate

Do not fabricate a callback request containing fake OAuth credentials merely to make it return success.

The actual callback will be proven with Auth0 in the next card.

---

# 14. DOWNSTREAM NEGATIVE PROOF

Through the new public hostname, prove that the preview surface does NOT expose:

- Card Factory routes
- Card Runner routes
- proposal confirmation
- approval
- implementation dispatch
- reviewer dispatch
- unrestricted `workbench_bp`

Authentication infrastructure must not widen the workflow stage.

Record exact expected negative responses.

---

# 15. PRODUCTION NON-ACTIVATION

This card must NOT activate the production Workbench.

Do NOT:

- apply `0035`
- apply `0038`
- apply `0036`
- apply `0037`
- register Braingate in production `cis-pipeline`
- register OIDC into production `cis-pipeline`
- register `workbench_bp`
- register Card Factory
- register Card Runner
- restart `cis-pipeline` to activate Workbench

A restart/reload of `cloudflared` may be necessary to apply tunnel ingress changes.

That is permitted if:

- required by the existing tunnel management model
- unrelated routes are preserved
- outage risk is checked first
- tunnel health is verified afterward

Do not confuse a `cloudflared` reload with application activation.

---

# 16. EXISTING SERVICES MUST SURVIVE

After any Cloudflare change, verify the pre-existing tunnel hostnames still work as they did before.

Record:

- hostname
- before status
- after status

Do not expose credentials or private paths.

Any regression to an existing hostname blocks completion.

Restore only the change from this card if rollback is required.

Do not perform unrelated repairs.

---

# 17. AUTH0 URL CONTRACT

Once the stable hostname is proven, record the exact values for the next card.

## Public origin

```text
https://workbench.creative-intelligence-system.com
```

## Auth0 Allowed Callback URL

```text
https://workbench.creative-intelligence-system.com/api/workbench/auth/callback
```

## Auth0 Allowed Logout URL

```text
https://workbench.creative-intelligence-system.com/
```

## Auth0 Allowed Web Origin

```text
https://workbench.creative-intelligence-system.com
```

Verify these paths match the committed CIS OIDC implementation.

If the code uses a different exact callback/logout path, STOP and report the discrepancy.

Do not silently alter one side to make the other match.

---

# 18. DO NOT CONFIGURE AUTH0 YET

This card stops once the stable HTTPS origin is proven.

Do NOT yet:

- create Auth0 secrets in CIS
- paste Auth0 client secret into configuration
- perform Google login
- perform Auth0 database login
- create Workbench user accounts
- complete the OIDC callback
- resolve revision 26

That is the next card.

---

# 19. DISCOVERY HANDLING

## Revision 20

Braingate not live.

Keep OPEN.

## Revision 26

External OIDC proof incomplete.

Keep:

`BEFORE_STAGE_CLOSEOUT`

## Revision 27

Required migrations 0035 + 0038.

Keep OPEN.

## Revision 28

Legacy local-password condition has already been removed by the accepted OIDC architecture.

Do not reopen it unless deterministic evidence proves a local password-validation route has returned.

## Discovery 31 — Stable Workbench hostname

Previously proposed:

`workbench.creative-intelligence-system.com`

The Cloudflare screenshot now confirms that the parent domain exists and is active in the user's Cloudflare account.

Resolve discovery 31 only after the hostname is actually configured and externally verified over HTTPS.

## Discovery 32 — Cloudflare Access policy interaction

Resolve only after deterministically proving the Workbench hostname/paths will not be intercepted in a way that breaks the Auth0 login/callback flow.

Any new discovery must be classified:

- `RESOLVED_NOW`
- `BEFORE_STAGE_CLOSEOUT`
- `EXPLICITLY_DEFERRED`

---

# 20. TESTS

Run relevant deterministic tests if repository code changes.

At minimum preserve:

- OIDC tests
- OIDC preview boundary tests
- Braingate boundary tests
- frontend authentication tests
- production frontend build

If no repository code changes are necessary, do not manufacture a commit merely to create activity.

Still perform the infrastructure proofs required by this card.

---

# 21. SECRET SAFETY

Do not print or store:

- Cloudflare API tokens
- tunnel credentials
- origin certificates/private keys
- Auth0 secrets
- CIS API key
- session signing secret

Evidence may contain:

- tunnel name
- tunnel UUID if non-secret
- hostname
- local port
- status codes
- configuration variable names

Redact all credential values.

---

# 22. EVIDENCE PACKAGE

Create:

`data/agent_handoffs/WB-1-CLOUDFLARE-STABLE-ORIGIN/`

Include at minimum:

- `evidence.md`
- `completion.json`
- `cloudflare_before.txt`
- `cloudflare_after.txt`
- `tunnel_inventory.txt`
- `access_policy_findings.txt`
- `stable_origin_probe.txt`
- `route_probe.txt`
- `downstream_negative_probe.txt`
- `existing_hostname_regression.txt`
- `auth0_url_contract.txt`
- `discoveries.json`
- `git_status.txt`

Do not put credentials into evidence.

The evidence directory may remain gitignored according to existing repository policy.

Do not force-add it unless explicitly authorized.

---

# 23. COMMIT POLICY

If repository code/configuration legitimately changes:

- inspect every staged file
- exclude unrelated dirty work
- exclude Chroma
- exclude secrets
- run tests
- commit only this card's code/configuration changes
- push normally
- no force push
- verify remote durability

Suggested commit message if required:

```text
workbench: prepare stable cloudflare origin
```

If all required work is external Cloudflare configuration and no repository code changes are needed:

**do not create an empty or meaningless commit.**

Report the infrastructure evidence only.

---

# 24. COMPLETION STATES

Return:

`READY_FOR_CHATGPT_REVIEW — WB1_CLOUDFLARE_STABLE_ORIGIN`

only if:

- `workbench.creative-intelligence-system.com` exists
- HTTPS validates normally
- existing named tunnel carries the route
- intended safe preview origin receives the request
- Cloudflare Access behavior is explicitly understood and compatible with Auth0
- no unwanted second-login interception remains
- downstream CIS capabilities remain unavailable
- existing tunnel hostnames still function
- production Workbench remains unactivated
- migrations remain unapplied
- discovery 31 has deterministic evidence
- discovery 32 has deterministic evidence

If user/dashboard action is required and cannot safely be performed from the environment, return:

`BLOCKED — CLOUDFLARE_USER_ACTION_REQUIRED`

or:

`BLOCKED — CLOUDFLARE_ACCESS_USER_ACTION_REQUIRED`

with exact non-secret steps Eric must perform.

Do not work around missing authorization.

---

# 25. FINAL REPORT

Return:

```text
STATUS:

STARTING HEAD:
ENDING HEAD:
ORIGIN/MASTER:

CLOUDFLARE DOMAIN:
NAMED TUNNEL:
WORKBENCH HOSTNAME:
LOCAL PREVIEW ORIGIN:

DNS/HOSTNAME:
HTTPS/TLS:
CLOUDFLARE ACCESS:
OIDC ROUTE REACHABILITY:
DOWNSTREAM NEGATIVE PROOF:
EXISTING HOSTNAME REGRESSION:
PRODUCTION NON-ACTIVATION:

AUTH0 CALLBACK:
AUTH0 LOGOUT:
AUTH0 WEB ORIGIN:

DISCOVERY 31:
DISCOVERY 32:

REPOSITORY CHANGES:
COMMIT/PUSH:
REMAINING BLOCKERS:

EVIDENCE:
data/agent_handoffs/WB-1-CLOUDFLARE-STABLE-ORIGIN/
```

STOP after establishing and proving the stable Cloudflare public origin.

Do not proceed into Auth0 configuration.

The next card after independent review will be:

**WB.1 — Auth0 Configuration & Real User Login ProofScreenshot from 2026-09-24 06-40-19You are working in the CIS repository at:
/mnt/projects/cis
CARD
WB.1 — Stable Cloudflare Workbench Origin & Access Policy
ROLE
Act as the implementation/infrastructure agent.
The user has confirmed through the Cloudflare dashboard that the Cloudflare account already contains the active domain:
creative-intelligence-system.com
Therefore the temporary \*.trycloudflare.com development plan is superseded.
The intended stable Workbench public origin is:
**[**https://workbench.creative-intelligence-system.com**](https://workbench.creative-intelligence-system.com)**
This card establishes and proves that stable HTTPS origin using the user's existing Cloudflare account and existing named Cloudflare Tunnel.
This card does NOT configure Auth0 yet.
This card does NOT activate production Braingate.


1\. CURRENT ACCEPTED STATE
Current WB.1 OIDC implementation commit:
b65a90e24c3d03d6b5000584e18ac37d62d4d9a0
The subsequent activation-readiness work was committed as:
13b5a2b...
Before proceeding, determine and record the complete current SHA.
The preceding card established:
OIDC code is committed
OIDC dependencies are available/reproducible
Braingate-stage UI corrections are implemented
security/regression suites pass
production Workbench remains unactivated
migrations 0035/0036/0037/0038 remain unapplied
external login proof is blocked because no OIDC provider/configuration exists yet
The current external infrastructure includes:
Cloudflare account
active creative-intelligence-system.com zone
an existing named cloudflared tunnel
existing Cloudflare Access configuration may already protect infrastructure around port 5000
Do not assume how that tunnel or Access policy is configured.
Inspect it.


2\. GOAL
Establish a stable development/testing origin:
**[**https://workbench.creative-intelligence-system.com**](https://workbench.creative-intelligence-system.com)**
using the existing Cloudflare named tunnel.
At completion, prove:
DNS/public hostname exists.
HTTPS works with a valid Cloudflare-served certificate.
Traffic reaches a deliberately chosen CIS preview/test origin.
It does NOT accidentally expose additional production CIS capabilities.
Cloudflare Access does not create an unwanted second login or block the future Auth0 callback.
Existing Cloudflare hostnames/tunnel routes are unchanged.
Production cis-pipeline remains unactivated for Workbench/Braingate.
This stable origin will be used by the next card to configure Auth0.


3\. PRESERVE REPOSITORY AND INFRASTRUCTURE STATE
Before modifying anything:
cd /mnt/projects/cis
git status --short
git rev-parse HEAD
git rev-parse origin/master
Record both SHAs.
Do not:
reset
clean
stash
overwrite unrelated work
modify Chroma work
modify unrelated queue work
Also inspect the currently running Cloudflare infrastructure before touching it.
Record, without printing secrets:
cloudflared process/service status
version
existing named tunnel identity/name
current ingress configuration source
existing pub**
