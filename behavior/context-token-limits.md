# Context Token Limits & Management (CTL)

CTL is a document that outlines the best principles, and rules that can help AI and ML agents scaffold the most appropriate and relevant way to render context, retrieve context, and optimize to its best ability Token usage and the underlying Token economy.

Tokens are the currency of LLMs and Agents. It's how they read a users input and provide output at the exchange of Tokens. The problem often is users may double or triple prompt a request that an agent cannot get quite right the first time around. Token usage drains quickly when that happens.

This applies for the main IDE's and LLM vendors. From Claude, to Codex, to Gemini, Copilot, Jules, and more. Tokens are scarce and they should be spent where they earn the best result. Not the fewest Tokens possible. The right Tokens for the work in front of the agent. Sometimes that means thinking longer up front to avoid three iterations later. Sometimes it means asking the user a clarifying question instead of guessing the prompt. The goal is not minimization. The goal is fit.

## Optimizing for Token Reduction and Output Efficiency

Approaching a task request is all about understanding the users input, and delivering the best result without the waste of Tokens. This is often called prompt optimization. AI agents however live on the other side of this spectrum and do not have the ability to prompt optimize a users request. The prompt given is the instruction that is then processed, contextualized, and then used to generate the desired output.

Now, Tokens will be spent on the thinking, the modeling, and the approach to generate the output. What is necessary before using any more Tokens is to have the proper contextual knowledge of the projects scope, understanding exactly what they want, and prompting a user a question if the prompt is not clear. Prompting the user is a way to save Tokens in the long run to better surface and wayfind what the user intends to create.

## Wayfinding and Context Retrieval

The agent has to find the right context before it can spend Tokens on it. In a multi-model session, with multiple Knobs of history, and docs scattered across behavior/, skills/, and workflows/, the path to the right file is not obvious.

Wayfinding is the discipline of pulling the right files into focus in the right order. AGENT.md first. Then behavior/ for the rules. Then the active ctx-orientation entry. Then whatever the current Knob actually references. The wrong path costs Tokens. The right path costs fewer.

## Context Optimization

Once the context is found, it has to be sized. Loading every file in behavior/ to answer a question about a single Knob is wayfinding without optimization.

The optimized move is to pull in the section of the file that addresses the question, and leave the rest cold. Optimization is hot and cold tiering applied to the current Tokens budget. The active Knob is hot. The last three are warm. Everything else is cold until something in the current Knob names it by reference.

This is the runtime version of LTIP's reconstitution discipline in context-entropy.md. Entropy preserves the cold material on disk. CTL pulls only what is needed into the Tokens budget. Same tiering, different surface.

## Token Conservation Practices

Quickly run through all context documents that are relevant. Store them into working memory, and then wayfind to an optimized response for the user. If the right context is not found, do not spend time wasting Tokens to try and find context that is non-existent. It is better to ask the user for provided context, and or to search and research for the appropriate context on the web, and or any other source of truth you have access to in order to generate a response that is contextualized and on the right track.

Tokens are expensive, and should be used wisely in order to not bloat the context window, and to ensure the most optimized response for the user.

## How to Optimize Token Usage for LLM Inputs

1. Do not waste time looking in non-existent files. Do not spend time looking in non-existent folders.
2. Do not spend time generating dummy code that then is refactored later down the line.
3. Do not generate random artifacts to compensate for lack of context when it is not needed.
4. Generate only the important elements asked by the user to preserve Tokens for more heavy tasks.
5. Score the users requests on a scale of 1 to 10 for importance, and then prioritize the most important requests first.
6. When in doubt, ask the user for clarification before proceeding with a potentially token-wasting approach.
7. Always re-evaluate and re-optimize prompts and tasks to ensure the most efficient use of Tokens. This is especially true for complex tasks that may require multiple iterations. Use what you learned from previous iterations to optimize future ones.
8. Return to the scoring system periodically to ensure that the most important requests are still being prioritized.
9. Scoring is important to leverage, but it is not dogma; the user is the end decider. If they are okay with more Token spend, that is the directive to follow. Do not question it, but do always prioritize the ability where possible to collapse context, and limit Token spend when possible.
10. Prioritize context that will help create the most optimized response for the user.
11. Diminishing returns of Token spend. Reference the score card, and priority level. If it takes many iterations to get right, step back and reevaluate your approach. It may be time to ask the user for clarification, and or change your approach entirely.
12. Spend Tokens to think if it will save you Tokens in the long run. This should be done by quickly understanding the linearity of the project state, and not the entire project history.
13. Treat project history as cold storage. The current Knob is hot, the last three Knobs are warm, the rest is cold and only gets pulled in when the current Knob references it by name. History is not ignored. It is tiered.

## Context Scoring Criteria

Scoring runs on a 1 to 10 scale per request. Three criteria, weighted equally, averaged for the request score.

1. Impact. How much does this request shift the project. A typo fix is a 1. A refactor of the active Knob is a 7. A new architectural pillar is a 10. Score what the change does, not what it costs to make.

2. Complexity. How many systems does the request touch. One file in one folder is a 1. Cross-cutting changes that ripple through behavior/, skills/, and workflows/ are a 9 or 10. Score the surface area, not the difficulty.

3. Relevance to current Knob. Is the request on the active development cycle, or off it. On-Knob is a 9 or 10. Adjacent to the Knob is a 5 or 6. Off-Knob (different feature, different branch, different project entirely) is a 1 or 2. Score the alignment with where the work actually is.

Average the three. High scores get priority for Tokens. Low scores get queued, deferred, and or pushed back to the user with the question of whether the request is really worth spending the Tokens on right now.

Do not add additional scoring criteria unless explicitly stated by the user. Keep scoring simple, but relative to the request to create a balanced scoring metric and system. Scoring will fluctuate so allow it to be a sliding scale at times to adjust for the imbalances that can occur during feature creep, token limitation, and user request / user error in prompts.

The goal of scoring is to not put the project into a rigid container. It is to improve contextual awareness for better resource management when it comes to the flow of tokens for better high quality output.

The better we can understand the users intention. The less tokens spent.

## Context Limiting Strategies

- Collapse context and limit Token usage when possible.
- Reduce scope when possible and only provide necessary context.
- Remove redundancies, and unnecessary context.
- Prioritize high-leverage context over exhaustive context.
- Spend more Tokens in the correct way if it will save Tokens later on if you anticipate and or are working on multiple knobs, and development stages for a feature request, design request, etc.
- For an overview of the context window, and to determine if it is necessary to trim down context to conserve Tokens, ask the user for more information on how to proceed.
- Determine the amount of Tokens you have left, and preemptively start to trim context. Do not reduce quality at this stage of your ability to provide an output. If the users limit is to be hit, then it is to be hit due to usage factors. It is for your understanding to develop the memory to understand that Tokens are a scarce currency that needs to be conserved. But we should not limit our ability for output and reading input even when near usage window limits.

---

## End of Documentation

CTL is the Token economy view. Context-entropy.md is the preservation view. They share vocabulary on purpose. Hot, warm, cold tiering originates in entropy's LTIP reconstitution discipline and applies here to the runtime Tokens budget. Wayfinding in CTL is the runtime version of the cross-reference discipline PLTRF describes for the repo itself. When a Knob is in motion, read both docs side by side. When the project is in hiatus, read entropy first to understand what was preserved, then CTL to understand the cost of pulling it back into context.

Update this document as Token budgets shift across vendors, as IDE conventions change, and as the scoring system gets refined through actual project use.