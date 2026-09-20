import "@testing-library/jest-dom/vitest";

if (!window.crypto.randomUUID) {
  window.crypto.randomUUID = () => `test-${Math.random().toString(16).slice(2)}`;
}
if (!window.crypto.subtle) {
  window.crypto.subtle = {
    digest: async () => new Uint8Array(32).buffer,
  };
}
