You are working in the CIS repository at:

`/mnt/projects/cis`

## CARD
**WB.1 — OIDC Activation Readiness & External Login Proof**

### ROLE

Act as the implementation agent.

ChatGPT has independently reviewed and **PASSED** the committed WB.1 OIDC implementation at:

`b65a90e24c3d03d6b5000584e18ac37d62d4d9a0`

`origin/master` was independently verified at that commit.

This card does **NOT** activate Braingate.

Your job is to make the committed OIDC/browser-login implementation demonstrably ready for activation and to prove the external human login path works, while keeping all Workbench application routes unactivated.

---

# 1. CURRENT ACCEPTED STATE

The following are already accepted and must not be redesigned unless deterministic evidence proves a defect.

## Authentication architecture

Workbench browser authentication is:

**Browser → CIS → OpenID Connect provider/Auth0 → CIS callback → server-validated Workbench session**

CIS does not authenticate or store the user's password.

The committed OIDC design includes:

- Authorization Code flow with PKCE
- OIDC `state`
- nonce validation
- issuer validation
- audience validation
- expiry validation
- asymmetric JWT signature verification through provider JWKS
- server-side email allowlist
- server-side owner/collaborator role assignment
- no browser exposure of:
  - `CIS_PIPELINE_API_KEY`
  - OIDC client secret
  - Workbench session signing secret
  - provider access token
  - provider refresh token
  - ID token
- signed finite Workbench session
- HttpOnly cookie
- Secure-by-default cookie
- SameSite protections
- per-session CSRF
- no local/shared-password login route

Do not reintroduce a password-authentication path.

## Braingate boundary

The accepted Braingate activation seam is:

`runtime/braingate_conversation.py`

It exposes only the conversation/project surface.

It must continue to enforce:

> conversation may occur; downstream generation and execution cannot occur.

Card Factory, proposal actions, confirmation, approval, and Card Runner must remain unreachable through the Braingate-only activation surface.

## Schema

The accepted Braingate conversation schema prerequisite is:

- `0035_workbench.sql`
- `0038_workbench_action_proposals.sql`

Do NOT apply them during this card.

Do NOT apply:

- `0036_card_factory.sql`
- `0037_card_runner.sql`

## Live system

The live Workbench/Braingate application routes are still intentionally unactivated.

Do not restart `cis-pipeline` as part of this card unless a read-only container dependency inspection absolutely requires entering the running container. Entering/executing non-mutating commands inside the existing container is permitted.

Do not register the Braingate blueprint.

Do not apply migrations.

Do not expose Card Factory or Card Runner.

---

# 2. CARD GOAL

At completion we need deterministic evidence for all three of these:

1. **The real `cis-pipeline` runtime/container can import and execute the committed OIDC dependency stack.**
2. **The browser UI shown during Braingate-only operation does not advertise downstream features that intentionally remain disabled.**
3. **A real external OIDC login can complete through the HTTPS development origin and establish a valid CIS Workbench session for an authorized person, while unauthorized access remains denied.**

This is an activation-readiness card.

It is not the activation card.

---

# 3. FIRST: PRESERVE REPOSITORY STATE

Before modifying anything:

```bash
cd /mnt/projects/cis
git status --short
git rev-parse HEAD
git rev-parse origin/master
```

Expected accepted baseline:

`b65a90e24c3d03d6b5000584e18ac37d62d4d9a0`

If HEAD has moved legitimately beyond that commit, inspect the intervening commits before proceeding.

Do not reset, clean, checkout over, stash, delete, or overwrite unrelated work.

The working tree previously contained unrelated modified/untracked work, including Chroma work and queue-4.29-related files.

Preserve all of it.

### Known contamination hazard

`tools/export/generate_hcp.py` may still contain unrelated modifications, while the repository pre-commit hook executes that generator.

Before committing this card:

- inspect every staged file;
- inspect every auto-generated projection;
- exclude unrelated content;
- do not force unrelated dirty files into this card.

No destructive Git command is permitted.

---

# 4. TASK A — PROVE THE OIDC DEPENDENCIES EXIST IN THE REAL RUNTIME

The committed OIDC implementation depends on runtime libraries including at least:

- `requests`
- `oauthlib`
- `jwt` / PyJWT
- `PyJWKClient`
- the cryptographic support needed for the configured asymmetric JWT algorithms

Do not assume that because tests pass on the host these packages exist in the production container.

## 4.1 Inspect dependency declaration

Determine exactly how `cis-pipeline` obtains its Python dependencies.

Inspect the relevant:

- Dockerfile(s)
- compose configuration
- requirements files
- pyproject/setup configuration if applicable
- container build scripts

Determine whether every dependency used by `runtime/workbench_oidc.py` is declared as a reproducible application dependency.

### Rule

A package merely existing on this machine is not sufficient.

It must either:

1. already be deterministically installed by the CIS container build/runtime configuration, or
2. be added to the repository's dependency declaration.

Do not install packages manually into the currently running container as the solution.

That would create invisible runtime debt.

## 4.2 Deterministic container import proof

Run a read-only check against the actual runtime/container environment.

At minimum prove successful imports equivalent to:

```python
import requests
import jwt
from jwt import PyJWKClient
from oauthlib.oauth2 import WebApplicationClient
```

Also prove the cryptographic/JWT stack can identify the asymmetric algorithms that the OIDC module permits.

Do not expose secrets while doing this.

Record:

- Python version
- relevant installed package versions
- import result
- whether the dependencies came from declared build dependencies

## 4.3 If dependency changes are required

Make the smallest reproducible dependency change necessary.

Then validate from a fresh/clean dependency installation or container build context where practical.

Do not modify the live container manually as a permanent fix.

---

# 5. TASK B — MAKE THE UI MATCH THE BRAINGATE-ONLY STAGE

The server boundary is authoritative and already correct.

However, the current React UI still contains downstream controls such as:

- `Card Factory (direct requests)`
- proposal-related presentation/actions
- proposal correction paths
- usage displays or navigation tied exclusively to downstream stages

During Braingate-only activation, users must not be presented with controls for functionality deliberately not registered on the server.

This is a UX/stage-coherence correction, not a security substitute.

## 5.1 Requirement

When the Workbench is operating in the current Braingate-only stage, the normal user experience should expose:

- sign in / sign out
- signed-in identity
- projects
- project creation
- project selection
- direction note if already part of the accepted conversation experience
- messages
- ordinary Braingate conversation
- context/source display
- System Context where appropriate

It must NOT visibly offer:

- Card Factory
- proposal generation
- proposal confirmation
- proposal approval
- direct implementation dispatch
- reviewer dispatch
- Card Runner
- downstream-stage controls

## 5.2 Do not delete future functionality

Do not rip out Card Factory/Runner/proposal components.

Those features are intended for later stages.

Use a deterministic stage/capability presentation mechanism.

Prefer a host/server-provided capability or stage value over frontend assumptions.

If an existing authoritative stage/capability source already exists, reuse it rather than creating competing state.

The frontend must not become the security boundary.

Even if a user manipulates JavaScript or sends direct requests, the server's Braingate boundary must remain authoritative.

## 5.3 Tests

Add/adjust tests proving that under the Braingate-only stage:

- Card Factory navigation is absent
- proposal actions are absent
- execution/approval controls are absent
- normal conversation remains available
- frontend manipulation does not make downstream server routes exist

Do not weaken existing assertions.

---

# 6. TASK C — CONFIGURE AND PROVE REAL EXTERNAL OIDC LOGIN

The committed implementation is designed for an HTTPS public development origin, including a Cloudflare development tunnel.

Use the project's existing intended tooling where available.

Do not create a second authentication architecture.

## 6.1 Configuration

Determine the exact required runtime environment variables from the committed implementation.

Expected categories include:

- OIDC issuer
- OIDC client ID
- OIDC client secret
- public HTTPS origin
- Workbench session signing secret
- allowed Workbench email(s)
- owner email(s), if applicable

Never commit secret values.

Never print secret values into evidence.

Never put them into the frontend bundle.

Never put them in Git.

If configuration files already exist outside Git, preserve their established pattern.

## 6.2 HTTPS development origin

Use the approved development HTTPS path.

If the repository includes:

`tools/development/quick_tunnel.py`

or an equivalent committed helper, use it rather than inventing another tunnel workflow.

Determine the exact public origin.

The OIDC callback must be derived from the configured public origin, not incoming `Host` or `X-Forwarded-*` headers.

Record the exact **non-secret** URLs that Auth0 requires for:

- callback
- logout
- allowed web origin, if required by the provider configuration

Do not use wildcard callback URLs.

## 6.3 Provider configuration

Configure Auth0/provider only as needed for the existing implementation.

Do not weaken:

- redirect checks
- issuer checking
- audience checking
- nonce checking
- PKCE
- state
- email verification behavior
- CIS allowlisting

Do not switch to implicit flow.

Do not place the OIDC client secret in JavaScript.

## 6.4 Real human login proof

Perform an actual browser/OIDC round trip using an authorized account.

Prove:

1. Workbench begins unauthenticated.
2. Sign In redirects to the configured provider.
3. Provider authentication succeeds.
4. Callback returns to the configured CIS HTTPS origin.
5. CIS validates the response.
6. CIS establishes the Workbench session.
7. Browser session endpoint identifies the authenticated person.
8. Role is computed by CIS.
9. Normal Braingate UI becomes available.
10. No provider token or CIS secret appears in:
   - browser-visible HTML
   - browser localStorage
   - browser sessionStorage
   - frontend bundle
   - API JSON responses
   - application logs
11. State-changing Workbench requests require valid CSRF behavior.
12. Sign out clears the CIS Workbench session.

Do not put actual secret/token values in evidence.

Use redacted descriptions such as:

`<redacted>`

where needed.

## 6.5 Unauthorized identity proof

Prove the CIS authorization boundary separately from provider authentication.

Using a safe test method, prove that an identity authenticated by the provider but not present in:

`CIS_WORKBENCH_ALLOWED_EMAILS`

does not receive an authorized Workbench session.

Expected result should be a deterministic denial.

Do not weaken the allowlist merely to simplify the test.

If obtaining a second real identity is impractical, use the narrowest deterministic provider/test mechanism available and state exactly what was tested versus what remains external.

Do not claim a real-user unauthorized test if one did not happen.

---

# 7. TASK D — SECURITY REGRESSION TESTS

Run the committed security tests plus any tests required by your changes.

At minimum include:

### OIDC

```bash
python runtime/tests/test_workbench_oidc.py
```

or the repository's actual invocation for that suite.

### OIDC preview/boundary

Run the existing OIDC preview/boundary suite.

### Braingate boundary

Run the full Braingate conversation boundary suite.

### Workbench conversation

Run:

- Workbench API tests
- conversation/action tests relevant to the conversation surface

### Card Factory

Run the full Card Factory suite.

It must remain unchanged/unreachable from Braingate.

### Card Runner

Run the full Card Runner suite.

It must remain unchanged/unreachable from Braingate.

### Frontend

Run:

- frontend unit tests
- production Vite build

The production build must succeed from the committed dependency lockfile.

### Import isolation

Repeat the clean-worktree/import-isolation proof used during the prior card where practical.

The committed WB.1 modules must not depend on untracked Chroma code.

---

# 8. TASK E — LIVE NON-ACTIVATION PROOF

At the end of this card, the production application must still NOT have Braingate activated.

Read-only verify the live service.

Expected:

- existing System Context endpoint continues to behave as before
- Workbench project/conversation routes remain unregistered/404 on the current live application
- Card Factory remains unregistered
- Card Runner remains unregistered
- migrations 0035 and 0038 remain unapplied
- migrations 0036 and 0037 remain unapplied
- `cis-pipeline` has not been restarted merely to activate this work
- no application blueprint activation occurred

The OIDC browser proof may use an isolated preview/test application that registers only the authentication and Braingate preview surfaces required for the proof.

It must not silently turn the production service into the new stage.

---

# 9. DISCOVERY HANDLING

Use the CIS discovery mechanism.

Existing relevant discoveries:

## Revision 20

Conversation is not live.

Keep OPEN until the later activation card.

## Revision 26

Browser authentication/OIDC activation proof.

Current disposition:

`BEFORE_STAGE_CLOSEOUT`

If this card completes the real OIDC human-login proof, update it based on deterministic evidence.

Do not resolve it merely because unit tests pass.

## Revision 27

Required Workbench migrations.

Keep OPEN.

This card must NOT apply them.

## Revision 28

Legacy shared-password-login risk.

The independently reviewed committed OIDC design removed the local/shared-password authentication route.

If repository continuity still shows revision 28 open, resolve it only after proving there is no password-validation/login route remaining in the committed/registered OIDC preview surface.

### New discoveries

Any new material issue must be structurally dispositioned as exactly one of:

- `RESOLVED_NOW`
- `BEFORE_STAGE_CLOSEOUT`
- `EXPLICITLY_DEFERRED`

Do not leave important findings only in prose.

---

# 10. DO NOT DO THESE THINGS

Do NOT:

- apply migration 0035
- apply migration 0038
- apply migration 0036
- apply migration 0037
- register `workbench_bp`
- activate the production Braingate blueprint
- activate Card Factory
- activate Card Runner
- restart production merely to activate Workbench
- force-add gitignored evidence without explicit authorization
- commit secrets
- expose API keys to JavaScript
- expose OIDC client secret to JavaScript
- expose session signing secret
- weaken PKCE/state/nonce/JWT verification
- create another login/password path
- add wildcard OIDC redirects
- use frontend hiding as the security boundary
- manually install an undeclared dependency into the production container and call that complete
- clean/reset/delete unrelated dirty work
- modify Chroma work
- modify unrelated queue 4.20 or 4.27 work
- mark WB.1 DONE

---

# 11. REQUIRED EVIDENCE PACKAGE

Create:

`data/agent_handoffs/WB-1-OIDC-ACTIVATION-READINESS/`

At minimum include:

## `evidence.md`

Human-readable evidence containing:

- starting HEAD
- ending HEAD
- origin/master
- exact files changed
- dependency declaration findings
- actual container dependency/import proof
- package versions
- stage-aware UI behavior
- OIDC configuration names, with values redacted
- public non-secret origin/callback/logout URLs used
- authorized real-login result
- unauthorized-login/allowlist result
- session result
- CSRF result
- secret-exposure checks
- live non-activation probes
- test results
- discovery dispositions
- remaining blockers
- unrelated dirty/untracked files preserved

## `completion.json`

Machine-readable summary containing at least:

```json
{
  "card": "WB.1 — OIDC Activation Readiness & External Login Proof",
  "status": "READY_FOR_CHATGPT_REVIEW",
  "starting_head": "",
  "ending_head": "",
  "origin_master": "",
  "files_changed": [],
  "tests": {},
  "oidc_dependencies": {},
  "authorized_login_proof": {},
  "unauthorized_login_proof": {},
  "live_non_activation": {},
  "discoveries": {},
  "remaining_blockers": []
}
```

Do not put secrets or tokens in either evidence file.

The evidence directory is known to be gitignored.

Do not force-add it merely to make it durable.

---

# 12. COMMIT REQUIREMENTS

If implementation changes are required and all local deterministic tests pass:

1. inspect every diff;
2. inspect every staged file;
3. inspect every pre-commit-generated projection;
4. ensure no unrelated dirty work entered;
5. commit only this card's repository changes;
6. push by normal fast-forward;
7. verify `origin/master`;
8. verify the pushed files from the remote, not merely the local index.

Suggested commit message:

```text
workbench: prove oidc activation readiness
```

If this card requires more than one logically isolated commit, that is acceptable, but keep them narrowly scoped and report every SHA.

No force push.

No history rewrite.

---

# 13. COMPLETION STANDARD

Do not declare this card complete merely because the code compiles.

Return:

`READY_FOR_CHATGPT_REVIEW — WB1_OIDC_ACTIVATION_READINESS`

only if all of the following are true:

- OIDC dependencies are reproducibly declared
- actual CIS runtime/container imports them successfully
- no undeclared/manual runtime dependency remains
- Braingate-stage UI no longer advertises unavailable downstream capabilities
- authorized external OIDC login was actually exercised
- CIS server-side allowlisting was exercised
- session + CSRF behavior was exercised
- no secrets/tokens leaked
- all required tests pass or any pre-existing environmental failures are independently controlled against the parent
- production Workbench/Braingate remains unactivated
- 0035/0038 remain unapplied
- Card Factory remains unactivated
- Card Runner remains unactivated
- all discoveries are structurally dispositioned
- evidence package exists
- repository changes are committed and pushed cleanly without unrelated contamination

If a real external OIDC login cannot be completed because of provider configuration, credentials, DNS/tunnel state, or another external dependency, do NOT improvise around it and do NOT mark the card passed.

Return instead:

`BLOCKED — WB1_OIDC_EXTERNAL_PROOF`

with:

- exactly what succeeded
- exactly what failed
- the external action still required
- deterministic evidence that the CIS implementation itself reached the expected boundary

---

# 14. FINAL REPORT FORMAT

Return a concise report containing:

```text
STATUS:
STARTING HEAD:
ENDING HEAD:
ORIGIN/MASTER:

DEPENDENCY PROOF:
UI STAGE-BOUNDARY PROOF:
AUTHORIZED OIDC LOGIN:
UNAUTHORIZED/ALLOWLIST PROOF:
SESSION/CSRF PROOF:
SECRET SCAN:
LIVE NON-ACTIVATION:
MIGRATIONS:
TESTS:
DISCOVERIES:
COMMIT/PUSH:
REMAINING BLOCKERS:

EVIDENCE:
data/agent_handoffs/WB-1-OIDC-ACTIVATION-READINESS/
```

Do not mark WB.1 itself DONE.

After independent review of this card, the next separate card will be the small operational activation:

**WB.1 — Braingate Live Activation**

That later card, not this one, may apply 0035 + 0038, register only the accepted authentication + Braingate conversation surfaces, restart the service, and prove downstream routes remain unreachable.