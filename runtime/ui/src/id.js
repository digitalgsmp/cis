export function uuid() {
  if (window.crypto?.randomUUID) return window.crypto.randomUUID();
  return `req-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}
