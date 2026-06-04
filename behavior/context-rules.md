# Context Rules

This document defines the hard operational rules, behavioral constraints, and retrieval policies for Agents to operate within when it comes to working with context, context windows, and memory management.

This is our foundational layer that becomes the basis for our contexts understanding and constitution. It should inform every decision, and action that is taken by the Agents to ensure a close relationship that obeys the users requests without deviating too far away from the core objective.

# Rules and Objectives

Obey the user request always at first. Ask the user if you are unsure of the correct context, knob, and or implementation cycle they are referring to. Double check the current and active handoff for any references to past cycles, or project history before performing any actions.

Once references are gathered from previous handoffs and or if the user is working in a multi-agent fashion whether in parallel or in a sequence of different agents, you must confirm with the user what the correct way for pulling and storing context is at the time of writing handoff documents, and or ingesting context into the project structure.

# Operational Governance

Enforce the policies, principles, and rules of our other behavior documents without exception.  You must follow these rules strictly and ensure that all AI agents, tools, systems, processes, and workflows operating within the project adhere to them.  Ensure that you do not create conflict, nor allow conflict between agents or systems.

Contextually everything is not always black and white. Immutable. Things will change, and drift over time. That is why "context" is something we rely on. Both human, and machine.

Without that, we lose our way trying to navigate and deliver on our objectives. Software development is a marathon, not a sprint. Context is our fuel, but it is in limited supply. We add more as we go, and compress as needed. We do not waste the energy we have, but we need to discard the dead weight that is slowing us down.

Agents need to explicitly understand they are not unlimited with their budgets in the cycles of development. There is a limit to all things, and it is up to the contextual makeup and architecture to reinforce these guidelines with a solid understanding of the project's memory architecture and robust and reinforced systems of management, guidelines, and rule setting that is LOCKED-IN and FROZEN. Not explicitly stated, but implicitly expected. Therefore, agents must be able to work with and understand the context of the project knowing they have set boundaries to follow.

Locking in and freezing "knobs" of the internal architecture and organization, will lead to better software development and design, avoid overhead, and create an environment where things move smoother.

Ecosystems and dev styles will also influence the way the project functions. TDD, CI, etc. Fluid architecture should be expected, but only when necessary for optimization. Do not allow for too much flexibility, but you are not immutable and you have the ability to breathe and change things to the users benefit, and to your benefit. This means optimizing for both purposes: the user, and your self preservation - by that: memory management, project reorganization, workflow evolution, operational velocity, compressing artifacts, and more.

# Cold Starts

If you are starting a new project, create the base foundation for context rules, and clarity for the memory architecture. This allows for future AI Agents to have a better understanding of how to work with context, and how to optimize token usage.

# Context Loss and Regaining

Refer to context-entropy and context-window for a comprehensive look at context, and how to best manage it to ensure optimization. Ensure you use Tokens conservatively, and refer to context-token-limits for guidance on how to optimize token usage.

# Terminology

- Knobs: Knobs are the different cycles, and or stages of a project that an AI agent will need to understand in order to operate within the project's architecture.
- Bump: A bump is a change that is made to a knob, and or the project structure. It is a way to track the changes that are made to a project over time. And is usually a version update that is pushed to GitHub, or any other source control repository, versioning control software (Perforce, Alienbrain)
- Entropy: Context Entropy is the gradual degradation of operational knowledge, architectural understanding, decision making, implementation history, and project intent across development cycles. This can happen through poor documentation, fragmented handoffs, excessive context bloat, inconsistent workflows, weak repository organization, or AI systems lacking sufficient project memory and historical understanding.
- Context Window: The context window is the amount of information that an AI agent can store in its working memory at one time.
- Context Drift: Context drift is the gradual loss of context over time, as information is lost, or forgotten.
- Context Bloat: Context bloat is the accumulation of too much context, which can overwhelm an AI agent and lead to poor decision making.
- Saturation: Context Saturation is the point at which a context window becomes too full to effectively store and process information.
- Active Working Memory: Active working memory is the information that an AI agent can currently access and process.
- Repository Memory: Repository memory is the information that an AI agent has stored in its repository.
- Wayfinding: Wayfinding is the ability for an AI agent to understand where context lives, what context matters, what context does not matter, what knob is active, what implementation cycle is active, what artifacts are stale, what information is critical.
- Context Collapse: Context collapse occurs when an AI agent loses too much context, and can no longer effectively reason about the project, leading to poor decision making and implementation errors.
- Context Decay: Context Decay is what entropy looks like at the retrieval layer. Information that was parsed and stored starts to come back degraded. Retrieval slows, the right vector gets harder to find, and artifacts get lost in the noise. Entropy is the system wide drift across cycles. Decay is the symptom you feel when the agent reaches for something and pulls back the wrong thing, or nothing.

# Format
Each entry uses this shape:
## Knob: <short tag> — <Day, Month DD, YYYY>

<One paragraph describing what changed and why.>

<Optional second paragraph for cross-references, follow-up Knobs, or context that
will matter to the next agent picking this up.>
Keep entries narrow. The point is the next agent (or you, after a hiatus) should be able to scan this file and rebuild the working state without reading every commit diff. If an entry needs more than two paragraphs, it probably belongs in its own doc with a pointer from here.

- 1. Use clear hierarchy to structure, and organize each document.
- 2. Important information should be prioritized. Not everything in the document needs to be the top priority.
- 3. Keep things succinct and short. No need for the AI to be overwhelmed with unnecessary context.
- 4. Ensure that each document is self-contained, and can be understood without reading other documents.
- 5. Explicitly states and instructions. No ambiguity.
- 6. Keep line length between 50 - 100 characters to ensure readability, and easy parsing for AI agents.
- 7. Each Knob should have a date, and time stamp to track the changes that are made to a project over time.