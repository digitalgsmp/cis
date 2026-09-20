import { uuid } from "./id";

function storageKey(scope, id) {
  return `cis-workbench-reqid-${scope}-${id}`;
}

// A request_id bound to `fingerprint` — a JSON-serializable description of
// exactly what this attempt is (project/proposal/card revision plus every
// parameter that changes what would actually be sent or spent). The same
// id is returned across retries and page reloads as long as the
// fingerprint is unchanged, so a lost or failed response can be retried
// safely — the server's own request_id dedup guarantees at most one model
// call / one dispatch for it. The moment the fingerprint changes (a
// correction, a different target, a different file list, a newer
// revision) this mints a fresh id instead — a deliberately different
// attempt is never merged into an old one just because it shares a scope.
export function getRequestId(scope, id, fingerprint) {
  const key = storageKey(scope, id);
  const fp = JSON.stringify(fingerprint);
  try {
    const raw = localStorage.getItem(key);
    if (raw) {
      const saved = JSON.parse(raw);
      if (saved && saved.fp === fp && saved.requestId) return saved.requestId;
    }
  } catch {
    // corrupt/unreadable storage — fall through to minting a fresh id
  }
  const requestId = uuid();
  localStorage.setItem(key, JSON.stringify({ requestId, fp }));
  return requestId;
}

export function clearRequestId(scope, id) {
  localStorage.removeItem(storageKey(scope, id));
}
