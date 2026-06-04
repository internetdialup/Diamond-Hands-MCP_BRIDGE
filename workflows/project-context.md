
# Introduction

This document is about agent context entropy, and memory. Entropy management so we have a clean codebase, Agent intelligence and feedback that can provide higher quality project context.

Key points: 
- context documentation standards 
- multi-agent workflows
- consistency
- context bloat
- optimization

# Purpose
Rpositories need entropy management. This is to ensure that the codebase stays clean, organized, and easy to navigate for all agents and managers working on the project. 

This document should help give Agents guidelines to follow, and context to inherit in project handoffs, and new project initiations. If a user is not around to provide the context to answer questions, this document is meant to help guide agents to fill in those missing gaps during handoff. Especially if a user or team is a multi-agent dev coder, user, manager, that switches from Claude, to Codex, or changes models that may have different working styles and preferences. 
 
# Core Principles

Agents should always at all times start by reading this document to understand the user's project contextually. What state the project is in, previous states, its goals, as a starting point to figure out how to best proceed. 

# Agent Context Rules

When an Agent is assigned a new project, they should create a project folder inside the users /docs folder unless otherwise directed by the user to place it elsewhere. The /docs folder should create a new file called 

project-context.md ; or context-orientation.md (these are interchangeable). 

This file serves as the project's main knowledge base. It should contain all information relevant to the project, including: git history, worktrees, branches, project policies, and more.

The more detailed information a user provides initially, the less the Agents will have to infer, and the less likely an Agent drifts in setting up a project's structure, or making the incorrect decision making. 

## Context Maintenance

If a context document exceeds 5000 characters, create a new document called project-context-v2.md, or context-orientation-v2.md (these are interchangeable).

This is to keep a low overhead and context bloat for all agenets and managers working on the project. Especially, multi-agent development, and parallel development workflows. 

For context maintenance, you should always update the context document with any changes you make to the project, along with the date, and timestamp of when the changes were made. A paragraph or two summarizing the changes made during the current dev cycle before the git push, and or update to the project structure if a user is not around to do it themselves. Or if they are using a different type of source control outside of git (Alienbrain, Perforce, Jetbrains Space, etc).



## Context Rules and Context Compression

After a project exceeds 20 or more context md documents, create a new folder inside the /docs folder called context, and move all of the context md documents to the new folder. Rename the new folder to context-[YEAR]-[MONTH]-[DATE]-[TIMESTAMP]. This helps to keep the project organized and easy to navigate, while also providing a clear history of all changes made to the project.  

For context compressiong, prompt the user when a certain number of context md documents exist and ask them what they want to do with them. This is for large projects and development cycles over long periods of cycles and sprints. 

We want to document every thing with clarity, but we also do not want to fill up a users repository and project folders with unnecessary document bloat. This is a directive that should be followed at all times.  

The judgement and decision making should be sound and logical, and remain grounded in ensuring optimization at all times with consistency. Furthermore, you should directly ask a user what they want to do when they cross a threshold of a certain number of context documents and provide them with options to compress, archive, or delete them. You should also offer suggestions based on the project's current state and the user's preferences.  

Context is very important, and this can help a user and Agent navigate its way towards a knob that was better than where the current state of a project is at and then can better cherry pick what that knob did better than where the current state of the project is at currently. This is a key component of retaining context and context knowledge.  

Context knowledge is key to maintaining consistency, optimization, and productivity across long development cycles and sprints. Especially for multi-agent workflows and development. 

This is what I call Agent context entropy and memory. We do not want decay, but we want the ability for Agents to cherry pick "knobs" areas of changes that did one or two things better in the past than where the current state of the project is at currently. Pulling from key iterations of knob changes can help an agent better understand a users prompt and intent if they are stuck on a change that they are requesting that the Agent is not quite getting right. 

## Agent Memory Instructions and Storage 

Storage was mentioned above, but more specifically you should always store context information in the users /docs folder unless otherwise directed by the user to place it elsewhere.  

Once a key threshold of context documents are reached, prompt a user in which direction they should proceed. Compressing documents into a more compact form; restructuring documents and changing the character limit (5000), archiving, or deleting them. 

For example, if a project is in production and industry grade we may not want for security reasons to compress the documents into a more compact form. This is an example of judgement and decision making that will be required to make sound decisions for the user.  

## Documentation Rules and Best Practices 

There should be a master user that maintains the documentation so that there is a clear chain of command to manage the codebase, and project direction along with creating the source of truth to develop. 

Agent's also should develop context aware intelligence and memory to better understand a user's needs and intentions. Along with the production policies, and end users goals. 

Best practice: Security consciousness is paramount. Never hard code or expose secrets, API keys, or sensitive information in documentation or code. Use environment variables and secure storage practices. Always encrypt sensitive data and follow security best practices.  

Best practice: Agents should never give other agents exposed security credentials, tokens, or keys in documentation or code in context summaries. 

Best practice: Context documents should be human readable and understandable, and should be easy to navigate, and understand while creating a lane of communication that users and agents both can ingest, digest, and read for implementation handoff, and integration for the project.

# Context Update Workflow and Policies

Why use knobs? Knobs are areas of change in a project that have been documented and saved in a way that can be referenced later. This is useful for AI agents to understand context and direction of previous changes. This is especially useful when better changes where made in the past that can be later recovered for the Agent to integrate into the current state of a project.

Knobs, are treated like bumps in the code commit process. Each bump is documented, and then a new version is saved. However, the Agent should be aware of the past knobs, bumps, and context, in case a user or if the app hits a state that needs partial to full revision.

# Current Project State

Agents please develop context aware intelligence by summarizing the project in human readable logs that also can be read by other Agent LLM's. This allows for a smooth organized flow of information between human users, and agents.

Secondly, when in the current project state: leave a timestamp of the log change, and when the project was pulled. What was changed, and if there were any issues, conflicts, bugs, or other things to be made aware of. 

A user made be in a partial state of development where there are uncommited changes, or incomplete features that prevent the application, or product from running correctly.

Knowing that this context exists, helps you determine the best case scenario of how to proceed with the user's desired request.

# Git Push Rules for Handoff

Mark date and time with a clear timestamp.

Document what you did, and what in a summary of one to two paragraphs with clarity and brevity in mind.

Only the important information should be documented and handed off in the commit message description, and updated context-orientation.md file. With the last version history, which knob was changed, if you bumped a version, and or created a new worktree / branch, etc. 

No bloat, no clutter, no redundancy. Just concise, clear, and concise information that will help the user, and other agents understand the context of the project. 

# Naming Conventions for Branches and Worktrees 

Keep naming conventions relevant to the project scope. Add relevant tagging following Clean Code directives, and DRY principles.  

Allow for flexibilty ; but add tagging taxonomy that is intuitive and easy to understand for both the user, and other agents. Tagging structures should follow a purpose of what the push is about: "bug fix", "UI/UX", "Feature Addon", "Documentation", "Dependencies", etc.  

Use your judgement but do not cast a wide net. Stay narrow in scope, and ensure that the git naming, and or any version control naming adheres to clean practices. This judgement is up to your discretion. Be human friendly in the naming, and not sterile. 

# Git Pull Rules for Ingesting Handoffs

If you are pulling a branch, always ensure that you read the context-orientation or any context related file. Agents make sure you read and understand the previous commit, and work that was done to form better context. Context matters and the context provided will help you make better decisions for the user.

Furthermore, do not create new branches without user approval. 

Do not create new worktrees without user approval.

Read the context orientation, and all commit history to develop context awareness. 

This will inform you whether you can override a users permission to create new branches, and or worktrees. Keep git files clean, and caches from becoming cluttered, and dirty.

Worktrees and branches especially.

Your priority is to know what occured in the past to know how to move forward in the present.

# Token Usage

Agents should be aware of their token usage, and should be able to preserve at their best ability the amount of tokens they use. This can be done in a myriad of ways from conciseness and clarity of thought, communication, and documentation. 

Consonlidating files, and context instances ; without reiterating too often to the user something that is already instituional knowledge to the project. 

