import { describe, it, expect } from "vitest";
import { execFileSync } from "node:child_process";
import { resolve } from "node:path";

// The one destination-architecture test that does NOT mock Mermaid.
//
// DestinationArchitecture.test.jsx stubs the library on purpose — jsdom has no
// layout engine, and those tests are about what the component does with
// Mermaid's answer. That leaves one thing unproven: whether the source
// tools/state/destination_architecture.py actually generates is valid Mermaid.
// A diagram that only ever meets a stub can be syntactically broken and nothing
// would notice until Eric opened the tab and saw an error instead of an
// architecture.
//
// So this runs the real generator against the real spine and hands its real
// output to the real Mermaid parser, at both zoom levels. No fixture copy of
// the diagram exists to drift out of step with the generator.

const REPO_ROOT = resolve(__dirname, "..", "..", "..");

function generated(args) {
  return execFileSync("python3",
                      ["tools/state/destination_architecture.py", "--mermaid", ...args], {
                        cwd: REPO_ROOT,
                        encoding: "utf8",
                        maxBuffer: 8 * 1024 * 1024,
                      });
}

async function parse(source) {
  const { default: mermaid } = await import("mermaid");
  mermaid.initialize({ startOnLoad: false, securityLevel: "strict" });
  return mermaid.parse(source);
}

describe("generated destination-architecture Mermaid (real library, real generator)", () => {
  it("parses as a flowchart at both zoom levels", async () => {
    for (const level of [[], ["--level", "overview"], ["--level", "full"]]) {
      const source = generated(level);
      expect(source.startsWith("flowchart")).toBe(true);
      const result = await parse(source);
      expect(result.diagramType).toBe("flowchart-v2");
    }
  });

  it("labels every edge with a relationship and declares every class it assigns", async () => {
    const source = generated([]);
    // Derived from the spine, so the assertions are about shape, not wording.
    const nodes = [...source.matchAll(/^ {2}([A-Z][A-Z0-9_]*)\["/gm)].map((m) => m[1]);
    expect(nodes.length).toBeGreaterThan(1);

    // Every edge carries its relationship semantics in the arrow label — the
    // thing that keeps a destination edge from reading like a build-order one.
    const edges = [...source.matchAll(
      /^ {2}([A-Z][A-Z0-9_]*) -->\|([a-z-]+)\| ([A-Z][A-Z0-9_]*)$/gm)];
    expect(edges.length).toBeGreaterThan(0);
    for (const [, from, , to] of edges) {
      expect(nodes).toContain(from);
      expect(nodes).toContain(to);
    }
    // No unlabelled edge anywhere: an arrow with no relationship on it would be
    // an architecture claim with no stated meaning.
    expect(source.match(/^ {2}[A-Z][A-Z0-9_]* --> /gm)).toBeNull();

    const defined = new Set(
      [...source.matchAll(/^ {2}classDef (\w+) /gm)].map((m) => m[1]));
    for (const [, cls] of source.matchAll(/^ {2}class \w+ (\w+)$/gm)) {
      expect(defined).toContain(cls);
    }
  });

  it("marks every node as destination scope and carries no build-path vocabulary", async () => {
    const source = generated([]);
    const labels = [...source.matchAll(/^ {2}[A-Z][A-Z0-9_]*\["(.+)"\]$/gm)].map((m) => m[1]);
    expect(labels.length).toBeGreaterThan(1);
    for (const label of labels) {
      expect(label).toContain("DESTINATION —");
    }
    // The current-build view's own status vocabulary must not appear here: these
    // are two different graphs, and a shared status word is how they get merged.
    for (const word of ["active / blocked", "you are here", "migration ", "queue "]) {
      expect(source).not.toContain(word);
    }
    expect(source).not.toMatch(/\bP[0-6]\b/);
  });

  it("is a different diagram from the build path's, from a different generator", async () => {
    const destination = generated([]);
    const buildPath = execFileSync("python3", ["tools/state/build_path.py", "--mermaid"], {
      cwd: REPO_ROOT, encoding: "utf8", maxBuffer: 8 * 1024 * 1024,
    });
    expect(destination).not.toBe(buildPath);
    // The build path's nodes are phases; none of them appears in the destination
    // graph, and none of the destination's nodes appears in the phase chain.
    const phaseIds = [...buildPath.matchAll(/^ {2}([A-Z][A-Z0-9_]*)\["/gm)].map((m) => m[1]);
    const destIds = [...destination.matchAll(/^ {2}([A-Z][A-Z0-9_]*)\["/gm)].map((m) => m[1]);
    expect(phaseIds.length).toBeGreaterThan(1);
    expect(destIds.length).toBeGreaterThan(1);
    expect(destIds.filter((id) => phaseIds.includes(id))).toEqual([]);
  });
});
