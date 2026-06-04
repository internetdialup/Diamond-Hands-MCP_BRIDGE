# Documentation.md — Context Orientation

The running per-Knob log for this repository. Each Bump (commit, version push, state transition) earns a one-to-two paragraph summary with date and timestamp. Brief, concrete, no bloat. Any agent (or human) reading this file should be able to trace what happened at any Knob in the repo's history and why.

When this file crosses 5000 characters of per-Knob entries, spawn `context-ori-summary-2.md` and continue here. Then `-3.md`, `-4.md`, `-5.md` as the repo grows. The current Knob and the last three stay hot in this file. Older entries migrate to the numbered summary files as cold storage.

Read in reverse chronological order — newest at the top. The active Knob is whatever appears first.

---

## Knob: typo pass + memory-tal rename — Sunday, May 31, 2026

Ran a correction pass over `context-rules.md` and the `architecture/memory/` docs. Scope was objective errors only. Misspellings, a few broken grammar spots that made a sentence hard to parse, nothing else. Left the voice alone on purpose. The run-ons, the fragments, the period-as-emphasis, the "and or" constructions, the dropped possessive apostrophes, and the all-caps emphasis in `context-rules.md` all stay. A pass that flattened those would read like a machine wrote it, which is the opposite of the point. `memory-rag.md` and `memory-crud.md` were already clean and went untouched.

Renamed the orphan `memory-tsq.md` to `memory-tal.md`, which was the name intended. It was an empty zero-byte file with an acronym nothing explained. Gave it a short planned-stub header naming its scope, temporal memory queries, and mapped it in `repo-organization.md` as planned. It is not loaded by anything yet. Still open after this Knob: the empty unmapped `development/` folder, and the unsettled question of whether `repo-cognition` ships standalone, which decides whether the `references/` stubs stay or get deleted.

---

## Knob: references dedup + glossary split — Sunday, May 31, 2026

Killed the duplication in `skills/repo-cognition/references/`. The four reference docs were byte for byte copies of the `behavior/` docs, which is the exact fragmentation PLTRF exists to prevent. Replaced each with a short pointer stub that names its canonical home in `behavior/` and redirects there. Repointed `SKILL.md` and the Claude, Codex, and Gemini overlays to load from `../../behavior/` directly, so agents get one hop to source instead of reading a mirror that can drift. Updated `repo-organization.md` so the map calls them pointers, not mirrors.

Two smaller fixes rode along. `memory-adm.md` was pointing at `memory-context-preservation.md` and `memory-manifest.md`, neither of which exists. Moved those under a planned note so the intent stays on record without leaving a broken pointer an agent would chase. And `context-rules.md` had Entropy and Context Decay defined with identical glossary text. Split them. Entropy is the system wide drift across cycles, Decay is the retrieval-layer symptom, which is how `context-entropy.md` already frames it. Still open after this Knob: the empty unmapped `development/` folder, the orphan `memory-tsq.md`, and a typo and voice pass on `context-rules.md` and the `architecture/memory/` docs.

---

## Knob: memory Skills + map hygiene — Thursday, May 28, 2026, 07:52 PM CDT

Added two separate Skills instead of bloating `repo-cognition`: `memory-context` for Knob-aware retrieval, ADM/RAG alignment, hot/warm/cold memory, and handoffs; `memory-watchdog` for stale maps, broken references, missing Knob entries, duplicate concepts, and memory rot. Updated `skills/skill-map.md` so Skills are now mapped instead of living behind a stub.

Added Map Hygiene rules to `docs/repo-organization.md`. New folders, moved files, new Skills, and new architecture memory docs now have explicit map-update expectations. This is the OSS governance edge of the repo: if the map lies, the memory system rots.

---

## Knob: ADM/RAG memory folder — Thursday, May 28, 2026

Moved the memory architecture docs into `architecture/memory/` so Memory, Drift, Watchdog, ADM, RAG, and CRUD live in one place instead of scattering across the top of `architecture/`. `workflow-tools.md` stays directly under `architecture/` because it is about tool friction and workflow surfaces, not the memory store itself.

Added the first pass of ADM, RAG, and CRUD memory docs. ADM carries episodic chapters and active memory banks. RAG carries semantic and procedural memory. CRUD is the keep-it-alive loop so stale memory gets created, read, updated, or destroyed instead of quietly rotting.

---

## Knob: architecture map + PLTRF cleanup — Thursday, May 28, 2026, 06:53 PM CDT

Added `architecture/` to the repo's cold-start map as the fifth working folder. It now shows up in `README.md`, `AGENT.md`, `CLAUDE.md`, and `docs/repo-organization.md`, but it is selective cold-start material. Agents load it when memory itself is the work: drift, Watchdog, audits, workflow governance, or memory architecture. Otherwise it stays cold so the Token budget does not get eaten just because a folder exists.

Cleaned up early PLTRF drift before it became normal. Fixed the broken `references/context-token-limits.md` pointers, corrected the long-term preservation acronym split, synced the repo-cognition reference mirrors back to canonical `behavior/`, and turned the Codex/Claude/Gemini overlays into thin wrappers around `SKILL.md`. Same hooks, fewer duplicated rules, less chance the repo becomes the thing the agent fights.

---

Older entries moved to `docs/context-ori-summary-2.md` as cold storage. Pull that file only when the current Knob references older scaffolding or prior release history.
