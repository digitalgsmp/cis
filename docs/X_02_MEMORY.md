
---

## Parking Lot — Application Layer Future Features

### Feature: Cloudflare Tunnel — Full Remote Dashboard Access
Current state: Tunnel serves CIS_LIVE.md only.
Prerequisite: Stable modular backend (complete). Authentication layer required.
Deferred: Security review needed before exposing full app externally.

### Feature: CIS_LIVE — Auto-fetch Model Responses
Current state: Not viable. Major models do not expose stable public share URLs.
Deferred: Manual paste remains correct approach until model APIs make this practical.

### Feature: CIS_LIVE — QR Code / Shareable URL Display
Current state: URL returned by push endpoint but not displayed in UI.
Deferred: Low effort — add in next Live panel iteration.

### Feature: Remote Field Access Workflow
Concept: Review records, approve knowledge objects, trigger lightweight pipeline jobs remotely.
Prerequisite: Cloudflare full tunnel + authentication layer.
Deferred: Authentication design not yet started.
