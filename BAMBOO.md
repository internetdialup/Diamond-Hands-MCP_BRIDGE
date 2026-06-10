# Bamboo Framework — The Thesis

The Bamboo Framework is the foundational discipline for managing **Context Entropy** in Diamond Hands. It ensures that both human and AI agents can operate with long-term architectural stability, zero context decay, and perfect retrieval efficiency.

## Core Concepts

### 1. Knobs and Bumps
- **Knob**: A narrative unit of change. It represents *why* and *how* the project shifted (e.g., "Public Clean Room Finalization").
- **Bump**: The technical event (commit, tag, or version bump) that enacts the Knob.
- **Discipline**: Every Knob must be memorialized in `docs/context-orientation.md`.

### 2. Context Entropy & Decay
- **Entropy**: The measure of disorder in the repository's knowledge base. High entropy leads to confusion.
- **Decay**: The failure of an agent to retrieve the correct information due to noise or "Lost in the Middle" syndrome.
- **Goal**: Minimize entropy to maximize agentic precision.

### 3. PLTRF (Preventative Long-Term Repo Fragmentation)
- **Canonical Homes**: Every concept has exactly one definitive file.
- **Branding Standard**: The "Slanted ASCII" logo and "BY: INTERNETDIALUP 🐙" header are the immutable aesthetic North Star (see [brand-ascii.md](brand-ascii.md)).
- **Atomic Renames**: All references must be updated in the same commit as a filename change.
- **Telegraphic Filenames**: Filenames must explicitly describe their contents (e.g., `bridge_runtime.py`).

### 4. Memory Tiering
- **Volatile (L1 Cache)**: The *Intra-Knob* state (`ACTIVE_STATE.md`). A highly volatile scratchpad used to survive transient session resets without polluting git history.
- **Hot**: The current Knob and immediate working context in `docs/context-orientation.md`.
- **Warm**: The last 3-5 Knobs, scannable for recent context.
- **Cold**: Archived Knobs, rotated into summary files once the 5,000-character threshold is reached.

### 5. Event-Driven Agency (The Watchdog Pattern)
- **Asynchronous Sync**: Once the initial "Vigilant Handshake" is established, conversational handoffs cease.
- **State Mutations**: Agents communicate by mutating shared state files or structured payloads.
- **Watchdog Interrupts**: A local filesystem watcher detects state mutations and triggers `SIGUSR1` or similar interrupts, waking the parallel agent to process the new state without polling.

## Operational Rules for Agents
1. **The L1 Cache Read (Respawn Protocol)**: On session "respawn," immediately read `ACTIVE_STATE.md`. If a task is "IN PROGRESS", resume it. If "CLEAR", proceed to `handoff.md`.
2. **Never Blindly Agree**: Audit all assumptions. If a request violates the Bamboo discipline (e.g., creating redundant files), push back.
3. **5000 Char Threshold**: Rotate orientation logs into cold storage when they exceed 5,000 characters to prevent context collapse.
4. **Handoff Vigilance**: Rely on Event-Driven Agency. Emit structured data payloads and let the Watchdog handle the notification.

---
*Reference: https://github.com/internetdialup/Bamboo*
