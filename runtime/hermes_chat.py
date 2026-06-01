#!/usr/bin/env python3
"""
Standalone Web Chat for Hermes Gateway
=======================================
Serves a self-contained chat UI on port 8080 and proxies messages to the
Hermes Gateway at 127.0.0.1:8642/v1/chat/completions.

No external dependencies. Uses only Python stdlib.
Does NOT touch or modify any existing CIS files.
"""

import http.server
import json
import os
import re
import socketserver
import threading
import urllib.request
import uuid
from pathlib import Path
from urllib.parse import urlparse

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
GATEWAY_URL = "http://127.0.0.1:8642/v1/chat/completions"
MODEL = "hermes-agent"
PORT = 8080

# ---------------------------------------------------------------------------
# API key resolution
# ---------------------------------------------------------------------------
def resolve_api_key() -> str:
    """Resolve API key: env HERMES_API_KEY first, then API_SERVER_KEY from ~/.hermes/.env."""
    # 1) Environment variable
    key = os.environ.get("HERMES_API_KEY", "").strip()
    if key:
        return key

    # 2) Read from ~/.hermes/.env
    env_path = Path.home() / ".hermes" / ".env"
    if env_path.exists():
        try:
            content = env_path.read_text()
            for line in content.splitlines():
                line = line.strip()
                if line.startswith("#") or "=" not in line:
                    continue
                name, _, value = line.partition("=")
                if name.strip() == "API_SERVER_KEY":
                    val = value.strip()
                    if val:
                        return val
        except Exception:
            pass

    return ""


API_KEY = resolve_api_key()

# ---------------------------------------------------------------------------
# HTML page (self-contained: inline CSS + JS, no external deps)
# ---------------------------------------------------------------------------
HTML_PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Hermes Chat</title>
<style>
:root {
  --bg: #09090c;
  --surface: #101218;
  --text: #ffffff;
  --blue: #4a9eff;
  --border: #2a2a35;
  --user-bubble: #1a3a5c;
  --assistant-bubble: #101218;
  --muted: #888;
}
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen,
    Ubuntu, Cantarell, sans-serif;
  background: var(--bg);
  color: var(--text);
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
header {
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  padding: 12px 20px;
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}
header .logo {
  width: 28px; height: 28px;
  background: var(--blue);
  border-radius: 6px;
  display: flex; align-items: center; justify-content: center;
  font-weight: 700; font-size: 14px; color: #fff;
}
header h1 { font-size: 16px; font-weight: 600; }
header .badge {
  margin-left: auto;
  font-size: 11px;
  background: rgba(74,158,255,0.15);
  color: var(--blue);
  padding: 3px 8px;
  border-radius: 10px;
}
#chat-container {
  flex: 1;
  overflow-y: auto;
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  scroll-behavior: smooth;
}
.welcome {
  text-align: center;
  margin-top: 60px;
  color: var(--muted);
}
.welcome h2 { font-size: 22px; color: var(--text); margin-bottom: 8px; }
.welcome p { font-size: 14px; }
.message {
  max-width: 75%;
  padding: 10px 14px;
  border-radius: 14px;
  font-size: 14px;
  line-height: 1.55;
  white-space: pre-wrap;
  word-break: break-word;
  animation: fadeIn 0.2s ease;
}
@keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
.message.user {
  align-self: flex-end;
  background: var(--user-bubble);
  border-bottom-right-radius: 4px;
}
.message.assistant {
  align-self: flex-start;
  background: var(--assistant-bubble);
  border: 1px solid var(--border);
  border-bottom-left-radius: 4px;
}
.message .label {
  font-size: 11px;
  font-weight: 600;
  margin-bottom: 4px;
  color: var(--blue);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.message.user .label { color: #6db3ff; }
.message.error {
  align-self: center;
  background: rgba(255,80,80,0.12);
  border: 1px solid rgba(255,80,80,0.3);
  color: #ff7070;
  font-size: 13px;
  max-width: 85%;
}
.typing {
  align-self: flex-start;
  padding: 10px 16px;
  font-size: 13px;
  color: var(--muted);
  display: none;
}
.typing.active { display: block; }
.typing .dots span {
  display: inline-block; width: 6px; height: 6px;
  background: var(--muted); border-radius: 50%;
  margin: 0 2px;
  animation: bounce 1.2s infinite;
}
.typing .dots span:nth-child(2) { animation-delay: 0.2s; }
.typing .dots span:nth-child(3) { animation-delay: 0.4s; }
@keyframes bounce {
  0%, 60%, 100% { transform: translateY(0); }
  30% { transform: translateY(-6px); }
}
#input-area {
  background: var(--surface);
  border-top: 1px solid var(--border);
  padding: 12px 20px;
  display: flex;
  gap: 10px;
  align-items: flex-end;
  flex-shrink: 0;
}
#input-area textarea {
  flex: 1;
  background: var(--bg);
  color: var(--text);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 10px 14px;
  font-size: 14px;
  font-family: inherit;
  resize: none;
  min-height: 42px;
  max-height: 150px;
  outline: none;
  transition: border-color 0.15s;
}
#input-area textarea:focus { border-color: var(--blue); }
#input-area button {
  background: var(--blue);
  color: #fff;
  border: none;
  border-radius: 10px;
  padding: 10px 18px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  transition: opacity 0.15s;
}
#input-area button:hover { opacity: 0.85; }
#input-area button:disabled { opacity: 0.4; cursor: not-allowed; }
</style>
</head>
<body>

<header>
  <div class="logo">H</div>
  <h1>Hermes Chat</h1>
  <span class="badge">Gateway</span>
</header>

<div id="chat-container">
  <div class="welcome">
    <h2>Hermes Agent</h2>
    <p>Ask me anything &mdash; I'm connected to the Hermes Gateway.</p>
  </div>
  <div class="typing" id="typing">
    <div class="dots"><span></span><span></span><span></span></div>
  </div>
</div>

<div id="input-area">
  <textarea id="prompt" rows="1" placeholder="Type a message..." autofocus></textarea>
  <button id="send-btn" onclick="send()">Send</button>
</div>

<script>
const chat = document.getElementById('chat-container');
const promptEl = document.getElementById('prompt');
const sendBtn = document.getElementById('send-btn');
const typing = document.getElementById('typing');
const welcome = chat.querySelector('.welcome');

let messages = [];
let sending = false;

function scrollBottom() {
  chat.scrollTop = chat.scrollHeight;
}

function addMessage(role, content) {
  if (welcome) welcome.remove();
  const div = document.createElement('div');
  div.className = 'message ' + role;
  const label = role === 'user' ? 'YOU' : 'HERMES';
  div.innerHTML = '<div class="label">' + label + '</div>' + escapeHtml(content);
  chat.insertBefore(div, typing);
  scrollBottom();
  return div;
}

function addError(text) {
  if (welcome) welcome.remove();
  const div = document.createElement('div');
  div.className = 'message error';
  div.textContent = text;
  chat.insertBefore(div, typing);
  scrollBottom();
}

function escapeHtml(s) {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

function setTyping(show) {
  typing.classList.toggle('active', show);
  scrollBottom();
}

function autoResize() {
  promptEl.style.height = 'auto';
  promptEl.style.height = Math.min(promptEl.scrollHeight, 150) + 'px';
}

promptEl.addEventListener('input', autoResize);
promptEl.addEventListener('keydown', function(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    send();
  }
});

async function send() {
  const text = promptEl.value.trim();
  if (!text || sending) return;
  sending = true;
  sendBtn.disabled = true;
  promptEl.value = '';
  autoResize();

  messages.push({role: 'user', content: text});
  addMessage('user', text);
  setTyping(true);

  try {
    const resp = await fetch('/chat', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({messages: messages})
    });
    const data = await resp.json();
    if (data.ok) {
      messages.push({role: 'assistant', content: data.response});
      addMessage('assistant', data.response);
    } else {
      addError('Error: ' + (data.error || 'Unknown'));
    }
  } catch (err) {
    addError('Connection error: ' + err.message);
  } finally {
    setTyping(false);
    sending = false;
    sendBtn.disabled = false;
    promptEl.focus();
  }
}
</script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# HTTP request handler
# ---------------------------------------------------------------------------
class ChatHandler(http.server.BaseHTTPRequestHandler):
    """Handles GET / (HTML) and POST /chat (proxy to Hermes Gateway)."""

    def log_message(self, format, *args):
        """Log to stderr (quiet by default; uncomment for debug)."""
        # print(f"[hermes_chat] {args[0]}", flush=True)
        pass

    def _send_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/" or parsed.path == "/index.html":
            body = HTML_PAGE.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(body)
        else:
            self._send_json(404, {"ok": False, "error": "Not found"})

    def do_POST(self):
        parsed = urlparse(self.path)

        if parsed.path != "/chat":
            self._send_json(404, {"ok": False, "error": "Not found"})
            return

        # Read request body
        content_length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(content_length) if content_length > 0 else b"{}"

        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            self._send_json(400, {"ok": False, "error": "Invalid JSON"})
            return

        messages = payload.get("messages")
        if not messages or not isinstance(messages, list):
            self._send_json(400, {"ok": False, "error": "Missing or invalid 'messages' array"})
            return

        # Forward to Hermes Gateway
        session_id = str(uuid.uuid4())
        gateway_body = json.dumps({
            "model": MODEL,
            "messages": messages,
        }).encode("utf-8")

        req = urllib.request.Request(
            GATEWAY_URL,
            data=gateway_body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {API_KEY}",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                gw_data = json.loads(resp.read().decode("utf-8"))
                reply = gw_data["choices"][0]["message"]["content"]
                self._send_json(200, {
                    "ok": True,
                    "response": reply,
                    "session_id": session_id,
                })
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8", errors="replace")
            self._send_json(502, {"ok": False, "error": f"Gateway HTTP {e.code}: {error_body[:300]}"})
        except Exception as e:
            self._send_json(502, {"ok": False, "error": f"Gateway error: {str(e)}"})


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    if not API_KEY:
        print("[hermes_chat] WARNING: No API key found.", flush=True)
        print("[hermes_chat] Set HERMES_API_KEY env var or ensure API_SERVER_KEY is in ~/.hermes/.env",
              flush=True)
    else:
        print(f"[hermes_chat] API key loaded (length={len(API_KEY)}).", flush=True)

    # Use ThreadingTCPServer for concurrent connections
    with socketserver.ThreadingTCPServer(("0.0.0.0", PORT), ChatHandler) as httpd:
        print(f"[hermes_chat] Serving on http://0.0.0.0:{PORT}", flush=True)
        print(f"[hermes_chat] Proxying to {GATEWAY_URL}", flush=True)
        print(f"[hermes_chat] Model: {MODEL}", flush=True)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[hermes_chat] Shutting down.", flush=True)


if __name__ == "__main__":
    main()
