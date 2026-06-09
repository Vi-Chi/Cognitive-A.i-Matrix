# Security Policy

## Private Repository Boundary

This repository is intended to remain private. It contains source code, design notes, and knowledge artifacts for the Cognitive Matrix module.

## Secrets

Do not commit live credentials, API keys, tokens, SSH keys, local `.env` files, runtime logs, or generated context stores.

Use `.env.example` as the only committed environment template. Runtime state belongs in `context_store.json` on the deployed host and is intentionally ignored.

## Network Exposure

The default agent server listens on port `8888` and does not implement authentication by itself. Bind locally or place it behind an authenticated reverse proxy before exposing it on a network.

## Reporting

Report suspected credential exposure, unsafe network exposure, or trust-boundary failures directly to the repository owner. Do not paste secrets into issues, pull requests, logs, or chat transcripts.
