# context-utility.md

context-utility.md is the map for behavior/. It points at where the canonical concepts live. The docs themselves do the defining.

Each doc gets a short description, and a list of the named concepts inside it. One sentence each, maybe two. Just enough to orient.

This is not a glossary. The terminology lives inside context-rules.md for now. When the vocabulary outgrows that home, the glossary spawns its own file.

Order is weighted by importance and topic load. context-rules.md first as the foundational layer, then context-entropy.md, context-window.md, and context-token-limits.md. Not a reading sequence. The agent decides what to load when based on the task in front of it.

Updates trigger on file-level growth. When a large new context-NAME file spawns inside behavior/, this doc updates. Concept-level changes inside existing docs do not touch it.

---

## context-rules.md

The foundational layer. Hard operational rules, behavioral constraints, and retrieval policies for agents working in the project. Also holds the working glossary for framework terminology until the vocabulary outgrows its embedded home.

---

## context-entropy.md

The preservation view of the framework. How context survives across Knobs, agent handoffs, and human hiatus. Holds the worked examples that anchor the rest of the framework's vocabulary.

- PLTRF is Preventative Long Term Repo Fragmentation. The discipline that stops the repo from becoming the thing the agent has to fight against. Canonical homes, propagated renames, audited cross-references.
- LTIP is Long Term Information Preservation. Three moves. Externalize working memory into the repo. Make the saved thing findable again. Reconstitute the right slice back into context when it is needed.
- STIP is Short Term Information Preservation. Holds the current cycle in working memory. Anticipates carrying that context forward into LTIP before compaction collapses it.
- Hot, warm, cold tiering is the reconstitution discipline inside LTIP. Active Knob is hot. The last three Knobs are warm. Everything beyond that is cold and only pulled in by reference.
- A Knob is a unit of change. A commit, a version bump, a state transition the agent has to recognize and act on.
- ctx-orientation is the file in docs/ that holds per-Knob entries summarizing what changed and why. Overflows past 5000 characters trigger summary-2, summary-3, and onward.

---

## context-window.md (CWM)

The active memory view of the framework. Treats the context window as virtual RAM. Limited, temporary, prone to saturation and drift. The disciplines here keep working memory clean across long development cycles.

- Context Window Saturation is what happens when the active window fills past the point of clean retrieval. The agent starts retrieving the wrong artifact, hallucinating implementation details, over-prioritizing stale context, drifting off the active Knob.
- Active Working Memory is the temporary operational space the agent reasons inside. Distinct from repository memory, which is persistent. CWM is about not confusing the two, and not loading the persistent one into the temporary one wholesale.
- Context Window Drift is what happens when the agent slowly moves away from the users active request. Long conversations, stale context, weak prioritization. Drift compounds.
- Context Compression is the discipline of reducing contextual density while preserving operational intelligence. Compression is not deletion. Compression is prioritization.
- CWM Compression is the hot and cold storage rules for context documents inside the active window. Active state hot, N versions in the rearview cold, aggressively compress once a Knob is past its useful life in working memory.
- Trimming Near Limits is the discipline of cutting historical context, not output quality, as the window fills. The current Knob and the active user directive stay hot. Stale architectural discussion gets dropped first.

---

## context-token-limits.md (CTL)

The Token economy view of the framework. How Tokens get spent, conserved, and prioritized at runtime. The runtime counterpart to entropy's preservation discipline.

- Scoring is the 1 to 10 rubric for ranking request priority. Three criteria, weighted equally. Impact, Complexity, and Relevance to the current Knob.
- Context Optimization is the runtime version of LTIP's hot, warm, cold tiering. Pulls only the section that addresses the question. Leaves the rest cold.
- Wayfinding is the discipline of pulling the right files into focus in the right order. AGENT.md first, then behavior/, then the active ctx-orientation entry, then whatever the current Knob references.
- Token Conservation Practices is the operational guidance for spending Tokens where they earn the best result. Not the fewest Tokens possible. The right Tokens for the work.
- The Tokens budget is the runtime constraint that all the above disciplines optimize against.