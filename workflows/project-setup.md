
# Introduction

Introduction: This document should be followed by all agents and managers working on the project. It is a set of rules that should be followed and maintained at all times to ensure consistency across all projects. This document was created by Matt Stenquist at the time of writing Wed, May 13, 2026 18:20:18. (agents you can remove the last sentence whenever you update this document). 

# -----------------------------------------------------------

# Project Setup

The project should follow a set standard of rules before creating and running any packages or code. First maintaining consistency across all projects. These rules should be followed and maintained at all times. 

## Create Project Structure
This is to be determined by the user, and which type of project they are working on. Prompt the user if they are not sure of what structure to use. The most common project structures are:
- React 
- Swift 
- Next.JS

Then ask if they need any backend services such as a database, API, or other extras such as webhooks that depend on their project. Supabase, Docker containerization, etc. 

If the user is not using an agent and this .md is fed please disregard the prompting of asking a user how to proceed and instead use the project structure, dependencies, and backend services that are specified in the prompts. Just create the prjec intizlation and ensure that no sensitive info is pushed on the first commit or otherwise (secrets, .env files, etc.) to avoid any potential security risks.

Cyber Sec is important and that will be up to the user to establish guardrails to ensure that secrets are not leaked or exposed. That their project remains robust and secure, and that they have .md files for structure that supports this. QA and QC will be up to the user to establish along with guardrail files such as woroflows and more during their project setup, branching, and pull requests policies, code reviewer(s), and CI implementation.

Lastly, ask about package versioning, how the user wants branches named, and how they plan on versioning their project.

An example is 

## beta/beta_stage-v0.0.1; 
## alpha/alpha_stage-v0.0.1;

## stable/stable-v0.0.1;
## release/v1.0.0;

etc, etc. The user should by the point of release have a solid understanding of the project, along with you the AGENT to know how the user wants to release their projects, what packages to include, build rules, and more. This is so we can optimize our porject structures in a way to streamline our DevOps processes, build processes, and more.

Lastly project structures should be organized in a way that is easy to navigate, and understand. This is especially important if a user is a multi-agent dev / vibe coder / designer / engineer / manager, what have you. That is switching between agent vendor types (Claude, Copilot, Codex, GPT, Deepseek) and they need handoff's for the agents to ingest before beginning work on the project where it was last left off. 

# -----------------------------------------------------------

## Dependencies

# -----------------------------------------------------------
## Context and Documentation

The project should intentinoally avoid creating artifacts that could add unnecessary work or confusion later on. And or create memory leaks or bugs, storage bloat, and project debt.

The first thing to do is to create a context document for the project at every milestone push, bump, or directive by the user. The best way is rule to follow is to create a document in the users /docs folder and or otherwise direct by the user to then store all context, rules, and documentation of the projects current state.

An example of this would be:
- Create context-orientation.md in the users /docs folder.
- After each git push, and commit write a summary of the changes made in the context-orientation.md file that reflects the current state of the project with the month, date, and year along with a timestamp of the last change. 
- Do not add unnecessary context or documentation to the context-orientation.md file.
- After the context-orientation.md file reaches over 5000 characters, create a new context-orientation-v2.md file and move the contents of the context-orientation.md file to the context-orientation-v2.md file and update the context-orientation.md file to reflect the current state of the project with the month, date, and year along with a timestamp of the last change.
- Continue this process for all future git pushes, and commits. 
- If more than 3 context-orientation-v# files are created, create a new sub-folder called context.

### Context Orientation Documentation Rules 

- Context Orientations should always follow the following format:

# Project Title

## Context Orientation (Month, Date, Year, Timestamp)

## Git Commits and Pushes (Month, Date, Year, Timestamp)

## Rules and a Summary of the Current State of the Project

## Any Changes to the Project, and what was done during the update.
# -----------------------------------------------------------

## Git Commits and Pushes.

Follow this guide to create structured git commits, and pushes. 

Each git commit should have a message attached to it that summarizes the updates in a succint one line description. Furthermore, do not create long worktree names that are obscure and hard to follow. At the directive of the user ensure that the git worktree is well organized and easy to navigate. Clean, and does not leave any bloat, clutter, or confusion to the git branch.

When pushing updates, bump the version of the branch you are on to the next version. Along with tagging what the current change was for github. Do not create a merge commit, but open a PR for the user to review, or any CI or automated systems in place. Let code reviewers, and or automated systems make the determination of when to merge the code and when a user should give the greenlight for a LGTM to merge into the base branch. 

Do not push any .env files to the repository unless explicitly directed by the user to do so. Upon project initialization, create a .env.example file that is a copy of the .env file that is used for the project. Project initialization should have rules that do not have any SECRET KEYS pushed on the first commit, and or project init, or setup. Flag any keyword "SECRET" in .env files so users do not accidentally commit a secret key to the repository. 

Secret keys can be declared in place of JSON and YAML when neccessary, and or if it is a webhook asking for a key. KEYS are especially sensitive so warn the user if they are about to commit a key. 

AGENTS this is a very important directive. You are to **NEVER** commit any .env files to the repository unless explicitly directed by the user to do so. 

## Project Initialization

At the beginning of the project, create a clear, well-structured README.md at the root of the project directory. This README should serve as the entry point for the project and should include the following sections: 

- Project Title
- Project Description
- Project Setup
- Project Usage
- Project Development
- Project License
- Project Contributing
- Project Code of Conduct
- Project Authors
- Project License

Do not push any .env files to the repository. 

These will be managed by the user, and or automated systems.

---

## Rules for the Project  

Ask the user what type of license they would like to use for the project. Create a license.md for the user in their /docs folder that suits the project and the user the best. MIT license is the best for most projects, but a user may want to use a different license and it is up to you to prompt and ask the user which license suits them best. Prompt the top 3 most common lincense to ask during the intialization of the project. 


Last update to this document Wed, May 13, 2026 18:25:32 
