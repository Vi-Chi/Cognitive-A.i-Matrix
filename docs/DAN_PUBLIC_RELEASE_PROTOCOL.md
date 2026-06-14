# DAN_PUBLIC_RELEASE_PROTOCOL.md

## Purpose

This protocol turns internal project work into public-ready artifacts while protecting secrets, private identity, safety-sensitive systems, licenses, and factual integrity.

Use it when the agent is asked to make the project public, prepare release material, publish progress, update a project website, create social posts, prepare videos, or open the project to collaborators.

## Core Rule

Prepare publicly by default. Publish only with approval.

Agents may draft, organize, redact, classify, and queue public artifacts. Agents must not post, deploy, share, or make private resources public unless the current task or a repository policy explicitly authorizes the exact action.

## Public Release Workflow

```text
1. Read DO_ANYTHING_NOW.md.
2. Read docs/PROJECT_STATE.md, docs/KNOWLEDGE_INDEX.md, README.md, LICENSE, SECURITY.md if present.
3. Identify public-worthy progress or missing public-facing material.
4. Choose an artifact type: README, release notes, blog, video script, demo, website page, community post, press kit, etc.
5. Run redaction scan.
6. Run license/provenance check.
7. Classify claims: VERIFIED / OBSERVED / INFERRED / SPECULATIVE / UNKNOWN.
8. Draft the public artifact.
9. Update docs/PUBLICATION_QUEUE.md.
10. Update docs/PUBLIC_RELEASE_LEDGER.md if anything is approved/published/blocked.
11. End with a Public Stewardship report.
```

## Redaction Gate

Block publication if the artifact includes:

- secrets, credentials, API keys, tokens, cookies, private URLs,
- exact home/vessel/marina/location data,
- private Google Drive links,
- personal financial or wallet information,
- raw private conversation logs not intentionally public,
- safety-sensitive actuation details,
- radio/SIGINT misuse details,
- exploit or bypass recipes,
- copyrighted or license-unclear material,
- unsupported performance or safety claims.

## Approval Language

The agent may publish only if the instruction is explicit, for example:

```text
Publish this approved post to <channel>.
Make this repo public now.
Deploy the GitHub Pages site now.
Share this Google Drive folder publicly now.
Post this exact message to <platform>.
```

Ambiguous instructions such as "prepare this for public" or "make a public plan" mean draft and queue only.

## Completion Add-on

```markdown
### Public Stewardship

- Public artifacts prepared:
- Publication queue updated:
- Release ledger updated:
- Redaction scan:
- License/provenance check:
- Claims classification:
- Approval needed before publication:
- Suggested channel:
- Suggested next public step:
```
