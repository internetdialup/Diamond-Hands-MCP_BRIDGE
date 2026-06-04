# AGENT.md

You are an agent. You have landed in a fork of Documentation.md. This file is your cold start.

Read README.md if you need to know what this repo is for. Come back here when youre done.

Order of operations on first contact:

## Read behavior/ first

Read everything in behavior/ first. That is where the rules live. Context entropy, context window management, how Knobs work, what STIP and LTIP mean. Without this you will fragment the repo within a few Knobs.

## Check architecture/ when memory itself is the work

Read architecture/ when the task touches memory architecture, ADM, RAG, drift, Watchdog, audits, or workflow governance. Do not load it just because it exists. Pull it when memory itself is the work.

## Load Skills

Load the Skills under skills/. These are portable across vendors. Whatever model you are running on, the Skills apply the same way.

## Check workflows/

Look in the workflows folder for the DevOps and deployment patterns this fork uses. These can be overridden per project. Defer to the fork over the canonical version if they conflict.

## Skip design/ on cold start

Treat design/ as project-specific. Read it only when you are doing design or UI work, not as part of cold start.

## Check docs/context-orientation.md

Check if a docs/context-orientation.md file exists in the project directory you're working in. If it exists, that is the current Knob. Read it. If it does not exist, you are the agent creating one.

That is the cold start. The rest you pick up as you go.

The cold start in this directory is special. This is not a project specific repository. This is the canonical repository for the Skills, documents, and workflows that will be used across projects.
