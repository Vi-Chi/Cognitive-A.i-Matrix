# Screenshot Capture Policy

## Default

Agents may create local screenshots when they improve evidence, documentation, demo quality, or public communication.

Agents may not publish or upload screenshots externally without approval or an explicit repository policy.

## Private Evidence

Private screenshots may include internal UI and development state, but must be stored under an evidence folder and flagged if they contain sensitive information.

## Public Evidence

Public screenshots must be redacted or generated with safe sample data.

Block public use if a screenshot shows:

- secrets, tokens, keys, cookies, session IDs,
- emails, private usernames, chat logs,
- private Google Drive/GitHub links,
- local filesystem paths revealing identity,
- internal IPs, VPN/Tailscale details,
- billing, exchange, wallet, or account pages,
- exact vessel/home/location identifiers,
- unsafe physical/security/maritime control details,
- private/copyrighted documents not cleared for release.

## Naming

Use numbered names:

```text
screenshots/001_before.png
screenshots/002_after.png
screenshots/003_benchmark.png
```

## Required Caption

Every screenshot used in public material should have:

- what it shows,
- commit/date,
- whether data is real/sample/synthetic,
- claim classification,
- limitation note if needed.
