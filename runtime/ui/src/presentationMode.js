// The presentation-mode contract shared by the Workbench's read-only
// visualization screens.
//
// WHY THIS FILE EXISTS (PM-D3). The Project Map offers one global control —
// Simple / More Detail / Technical — but two of its six areas are not its own
// views: "Current Build" renders <CurrentBuildPanel> from BuildPath.jsx and
// "Destination" renders <DestinationArchitecture/>. The mode predicate used to
// live inside ProjectMap.jsx, so the control could not reach either reused
// component, and the two areas Eric looks at most did not respond to it. The
// fix is to move the predicate here and pass the mode as a prop — NOT to give
// the Project Map its own copy of either view.
//
// THE VOCABULARY IS NOT INVENTED HERE. It is the one the project-intelligence
// read model declares (tools/state/project_intelligence.py, MODES): simple,
// detail, technical. The ranking below is the only thing this module adds. No
// screen may introduce a fourth mode, or a synonym for one of these three.
//
// DISCLOSURE, NOT REMOVAL. A higher mode only ever adds. Nothing is taken out
// of a read model at Simple; it sits one mode away. That is the whole meaning
// of "progressively disclose", and it is why the shared components take a mode
// rather than a filtered model.

/** The declared ids, in order of increasing disclosure. */
export const MODE_IDS = ["simple", "detail", "technical"];

const MODE_RANK = { simple: 0, detail: 1, technical: 2 };

/**
 * The default for a STANDALONE screen.
 *
 * Build Path and Destination Architecture each answer one question in full,
 * for a reader who is already in that screen on purpose, and embedding them in
 * the Project Map must not change what they show on their own screens. So an
 * absent mode means "everything", not "simple": a component that is handed no
 * mode keeps the rendering it had before this contract existed.
 */
export const FULL_DISCLOSURE = "technical";

/**
 * Progressive disclosure, as one predicate.
 *
 * `atLeast(mode, "detail")` is true at More Detail and Technical; an unknown or
 * absent mode is treated as full disclosure, per FULL_DISCLOSURE above.
 */
export function atLeast(mode, needed) {
  const have = MODE_RANK[mode] ?? MODE_RANK[FULL_DISCLOSURE];
  return have >= (MODE_RANK[needed] ?? 0);
}
