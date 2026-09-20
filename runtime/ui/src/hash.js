// Matches runtime/card_runner.py's `_sha256_text` (hashlib.sha256 over UTF-8
// bytes). The approve step must send the fingerprint of exactly the card
// text Eric was shown — never a value recomputed by anyone else — so this
// runs client-side against the text actually rendered on screen.
export async function sha256Hex(text) {
  const bytes = new TextEncoder().encode(text);
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return Array.from(new Uint8Array(digest))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}
