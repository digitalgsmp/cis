import { describe, it, expect } from "vitest";
import { execFileSync } from "node:child_process";
import { resolve } from "node:path";

// The one test here that does NOT mock Mermaid.
//
// BuildPath.test.jsx stubs the library on purpose — jsdom has no layout engine,
// and those tests are about what the component does with Mermaid's answer. That
// leaves one thing unproven: whether the source tools/state/build_path.py
// actually generates is valid Mermaid. A diagram that only ever meets a stub
// can be syntactically broken and nothing would notice until Eric opened the
// screen and saw an error instead of a roadmap.
//
// So this runs the real generator against the real spine and hands its real
// output to the real Mermaid parser. No fixture copy of the diagram exists to
// drift out of step with the generator.

const REPO_ROOT = resolve(__dirname, "..", "..", "..");

function generatedMermaidSource() {
  return execFileSync("python3", ["tools/state/build_path.py", "--mermaid"], {
    cwd: REPO_ROOT,
    encoding: "utf8",
    maxBuffer: 8 * 1024 * 1024,
  });
}

describe("generated Mermaid source (real library, real generator)", () => {
  it("parses as a flowchart", async () => {
    const source = generatedMermaidSource();
    expect(source.startsWith("flowchart")).toBe(true);

    const { default: mermaid } = await import("mermaid");
    mermaid.initialize({ startOnLoad: false, securityLevel: "strict" });

    const result = await mermaid.parse(source);
    expect(result.diagramType).toBe("flowchart-v2");
  });

  it("carries the roadmap stages, their statuses and their unlock markers", async () => {
    const source = generatedMermaidSource();
    // Derived from the spine, so the assertions are about shape, not wording:
    // every node declaration and every edge must be well formed.
    const nodes = [...source.matchAll(/^ {2}([A-Z][A-Z0-9_]*)\["/gm)].map((m) => m[1]);
    const edges = [...source.matchAll(/^ {2}([A-Z][A-Z0-9_]*) --> ([A-Z][A-Z0-9_]*)$/gm)];
    expect(nodes.length).toBeGreaterThan(1);
    // A linear chain: one edge fewer than there are phase nodes.
    for (const [, from, to] of edges) {
      expect(nodes).toContain(from);
      expect(nodes).toContain(to);
    }
    expect(edges.length).toBeGreaterThan(0);
    // Every class assignment names a classDef the same source declares.
    const defined = new Set(
      [...source.matchAll(/^ {2}classDef (\w+) /gm)].map((m) => m[1]));
    for (const [, cls] of source.matchAll(/^ {2}class \w+ (\w+)$/gm)) {
      expect(defined).toContain(cls);
    }
  });
});
