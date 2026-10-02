import { useEffect, useRef, useState } from "react";

/** Mermaid, rendered client-side, with the source itself as the fallback.
 *
 * Shared by the two Build Path tabs (BuildPath.jsx and
 * DestinationArchitecture.jsx) because both draw a server-generated diagram
 * and neither should carry its own copy of this. The source always comes from
 * a read model — this component never composes a diagram, it only asks Mermaid
 * to lay one out.
 *
 * If Mermaid cannot lay the diagram out — an older browser, a parse error, a
 * chunk that failed to load — the error is stated and the generated source is
 * shown as text rather than leaving an empty box that looks like "nothing is
 * recorded". The source stays reachable either way, because it is the thing
 * that is actually derived from authority.
 *
 * `testIdPrefix` keeps each tab's diagram addressable on its own in tests;
 * `emptyNote` is what to say when the read model carried no source at all. */
export default function MermaidDiagram({ source, testIdPrefix = "bp", emptyNote }) {
  const [svg, setSvg] = useState("");
  const [error, setError] = useState("");
  const [showSource, setShowSource] = useState(false);
  // Each render needs a DOM id unique to this mount; Mermaid uses it for the
  // temporary element it measures in.
  const idRef = useRef(`${testIdPrefix}-mermaid-${Math.random().toString(36).slice(2)}`);

  useEffect(() => {
    let cancelled = false;
    if (!source) {
      setSvg("");
      setError("");
      return undefined;
    }
    (async () => {
      try {
        // Imported here, not at module scope: Mermaid and its parser are by
        // far the largest thing in this bundle, and the conversation screen —
        // which every user loads — has no use for them. This keeps the cost
        // on the screens that draw a diagram. A failed chunk load lands in the
        // same catch as a parse failure, and shows the source instead.
        const { default: mermaid } = await import("mermaid");
        mermaid.initialize({
          startOnLoad: false,
          theme: "dark",
          // Labels come from this project's own spine, but the strict setting
          // is kept anyway: it is the right default for anything injected as
          // markup, and nothing here needs the relaxed one.
          securityLevel: "strict",
          flowchart: { useMaxWidth: true, htmlLabels: true },
        });
        const result = await mermaid.render(idRef.current, source);
        if (!cancelled) {
          setSvg(result.svg);
          setError("");
        }
      } catch (e) {
        if (!cancelled) {
          setSvg("");
          setError(e?.message || String(e));
        }
      }
    })();
    return () => { cancelled = true; };
  }, [source]);

  if (!source) {
    return (
      <div className="muted">
        {emptyNote || "The read model carried no diagram source."}
      </div>
    );
  }

  return (
    <>
      {error && (
        <div className="inline-error">
          Could not draw the diagram: {error} — the generated source is shown below instead.
        </div>
      )}
      {svg && (
        /* Mermaid's own SVG output, from source this app generated server-side. */
        <div className="bp-diagram" data-testid={`${testIdPrefix}-diagram`}
             dangerouslySetInnerHTML={{ __html: svg }} />
      )}
      {(error || showSource) && (
        <pre className="bp-mermaid-source" data-testid={`${testIdPrefix}-mermaid-source`}>
          {source}
        </pre>
      )}
      {!error && (
        <button className="link-btn" onClick={() => setShowSource((s) => !s)}>
          {showSource ? "Hide" : "Show"} Mermaid source
        </button>
      )}
    </>
  );
}
