# Secrets and Environment

Duplicate this into your Private Repo to ensure your MCP Agent follows all of the trade rules, security protocols, and best practices. 

## Requirements

- never store broker secrets in docs or committed config files
- use local private environment variables or secret stores
- keep machine-specific paths out of committed runtime code when avoidable
- audit any shell command that could leak credentials through logs
- treat Robinhood credentials, tokens, MFA material, account numbers, account identifiers, private `.env` files, and local broker config as non-committable secrets
- redact account-identifying values from logs, generated bridge artifacts, test fixtures, screenshots, and support output

## Local Setup Expectations

- sibling Analyzer checkout available
- Python runtime available in both repos
- private broker configuration handled outside committed examples
- Robinhood account wiring handled through private local secret storage or runtime environment variables only

## Prohibited Patterns

- copying secrets into Analyzer
- storing private credentials in markdown runbooks
- embedding live broker identifiers in public-facing code or docs
- pushing `.env`, local broker config, account numbers, API tokens, session cookies, MFA recovery material, screenshots, or generated artifacts that expose the Robinhood account