# Remote UI Access — Sunshine + Moonlight + Tailscale

**Researched:** 2026-07-10
**Updated:** 2026-07-10 (two-user setup)
**Decision driver:** Eric wants low-latency real-time monitoring of the control plane UI. Sunshine/Moonlight was previously identified as best for the creative pipeline due to lowest monitor latency.

## Host Hardware (creative-vm)

- **GPU:** NVIDIA GeForce RTX 4090 (AD102) — 7th gen NVENC, hardware encoding
- **CPU:** AMD Ryzen 9 7950X 16-Core
- **OS:** Ubuntu 24.04 LTS
- **Network:** 192.168.1.15 (LAN), Proxmox VM on wander (192.168.1.200)
- **Current displays:** DP-0 (5120x1440), HDMI-0 (1920x1080) — dual monitor
- **X display:** :1 active
- **Sunshine:** Already installed (v2025.924.154138) but service disabled, not running
- **Tailscale:** NOT installed

## Two-User Setup

### Users
- **User 1 "vector" (Eric):** Works from local monitor directly on the server, or remote via Moonlight on laptop/phone. Uses existing physical display (DP-0).
- **User 2 "pirate":** Always remote (from another state). Needs a virtual headless display since they're never physically at the machine. Linux account to be created (UID 1001).
- Both need simultaneous access at times.

### Architecture (Two Simultaneous Sessions)

```
Eric (local or remote)          Pirate (always remote)
    ↓                                ↓ Tailscale tunnel
Display :1 (DP-0)               Display :2 (virtual, NVIDIA dummy)
    ↓                                ↓
Sunshine port 47990            Sunshine port 47994
    ↓                                ↓ NVENC hardware encode
Moonlight client               Moonlight client
    ↓                                ↓
Browser → localhost:5000/ui    Browser → localhost:5000/ui
```

### Setup Steps (require sudo — agent cannot run sudo)

**Step 1: Create pirate Linux user**
```bash
sudo useradd -m -s /bin/bash -u 1001 pirate
sudo passwd pirate
sudo usermod -aG video,audio,input pirate
```

**Step 2: Install Tailscale**
```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
# Follow the auth link to join your tailnet
```

**Step 3: Set up virtual display for pirate**
- Use NVIDIA dummy display (custom EDID) or X virtual framebuffer (Xvfb)
- Create a second X session on display :2 for pirate user
- Add a second Sunshine instance configured for display :2, base port 47994
- Eric's Sunshine stays on display :1, base port 47990

**Step 4: Configure Sunshine credentials**
- Eric's Sunshine: username "vector" (already has "sunshine" user — reconfigure)
- Pirate's Sunshine: username "pirate"

**Step 5: Pair Moonlight clients**
- Install Moonlight on each user's device(s)
- Add creative-vm's Tailscale IP as host
- Pair with respective Sunshine instance (enter PIN from Sunshine web UI)

**Step 6: Access the CIS Control Plane**
From the streamed desktop session, open browser to:
- `http://localhost:5000/ui/relay` — pipeline relay control plane
- `http://localhost:5000/api/health` — health check
- `http://localhost:5000/api/relay/guardrails` — guardrail outcomes

### Agent Limitation
The Hermes agent cannot run `sudo` commands — it requires Eric's password and the security layer blocks stdin password piping. All sudo-requiring setup steps must be run manually by Eric in a terminal. The agent can prepare the commands and configuration files, but Eric must execute them.

## Why Sunshine/Moonlight (not RDP/VNC/Tailscale-serve)

Per research (2026-07-10):
- Moonlight + Sunshine produces "the most responsive out-of-the-box GPU remote desktop experience" for interactive work
- NVENC hardware encoding on RTX 4090 = ~5-10ms encode latency
- Self-hosted, no account required (unlike Parsec)
- Free and open-source (unlike Parsec Warp at $9.99/mo)
- Works over Tailscale for secure remote access from anywhere
- Better for UI interaction than Tailscale Serve (which just proxies HTTP) because you get full desktop + browser
- Multi-monitor support (Sunshine 0.20+)

## Notes

- Sunshine is already installed on creative-vm but service is disabled. Enable with `systemctl --user enable sunshine` (may need lingering enabled for user services).
- Sunshine requires a desktop environment (X11 or Wayland session). creative-vm has X11 on display :1.
- For pirate's headless virtual display: feed a custom EDID to NVIDIA driver or use Xvfb. The RTX 4090 supports multiple NVENC streams simultaneously, so two simultaneous Sunshine instances are feasible.
- The UI will likely need major redesign once Eric gets hands-on with it through this remote access path.
- The existing `docs/REMOTE_ACCESS_SETUP.md` documents Tailscale Serve, nginx, and SSH tunnel as alternatives — Sunshine/Moonlight supersedes these for the interactive UI use case.
