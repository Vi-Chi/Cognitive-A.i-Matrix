# Discord Emissary — MΣBUS Adapter Design Skeleton

**Author:** Claude (Auditor-Scribe) · **Date:** 2026-06-14  
**Status:** DESIGN RADAR — no code until live Discord bot exists (Vi manual step)  
**Blueprint ref:** `blueprints/00_BLUEPRINT_INDEX.md` — "Discord Emissary layer"

---

## What this is

The Discord Emissary is the public-facing adapter layer between the live Discord server and the A.i Core (MΣBUS). It is explicitly **not** part of the core cognitive system — it is a membrane boundary that:

- Translates inbound Discord events → MΣBUS inbound messages (labelled `external_model` provenance, untrusted)
- Translates approved MΣBUS outbound drafts → Discord post payloads (via the triple-gated `webhook_client`)
- Enforces the airlock: community input enters as data, never as instruction

---

## Position in the system

```
[Discord server]
      |
   [airlock]          # #intake-airlock channel; prompt-injection boundary
      |
[Emissary adapter]   # THIS DOCUMENT — translates events → M-envelope
      |
  [MΣBUS / M envelope]  m.discord.inbound → Orbi/SMTIS etc.
      |
  [Orbi / Urbi]       # propose/audit cycle; never auto-posts
      |
  [approval gate]     # Vi approval + ledger
      |
[Emissary adapter]   # translates approved draft → webhook_client
      |
   [Discord webhook]  # triple-gated send
```

---

## Inbound envelope shape

Discord events entering the MΣBUS should be wrapped in a standard M envelope with:

```python
MMessage(
    version=1,
    sigma="m.discord.inbound",        # class: inbound community event
    pi={                               # payload
        "source": "discord",
        "channel": "#intake-airlock",
        "event_type": "message",       # message | reaction | slash_command
        "content_hash": "<sha256>",    # hash only — never raw content in envelope
        "content_ref": "<draft_id>",   # pointer to approval_ledger entry
        "label_verified": True,
    },
    delta={"provenance": "external_community", "trust": "untrusted"},
    kappa=0.0,                         # untrusted: κ = 0.0
    tau=datetime.now(timezone.utc).isoformat(),
    mu=Mode.WAKE,
)
```

**Rules:**
- Raw Discord message content is NEVER placed in the MΣBUS envelope (prompt-injection risk).
- Content travels only via `content_ref` → approval_ledger lookup.
- `kappa=0.0` (fully untrusted) on all inbound community events.
- `sigma="m.discord.inbound"` is NOT an action class; it is a cognition/data class → PolicyGate will not route it as an action.
- Community events must NOT be forwarded to `mu=DREAM` (Ω₈ gate).

---

## Outbound path

Approved drafts flow outbound ONLY through:
1. Orbi proposes a draft → `sigma="m.discord.draft.proposed"` cognition (not action).
2. Urbi audits: does the draft satisfy disclosure labeling, no PII, no secret shapes?
3. PolicyGate: draft cognition passes (not action class).
4. Draft lands in the approval_ledger as a `draft` entry.
5. **Vi approves** (manual step; records `approval` entry in ledger).
6. Emissary adapter reads approved ledger entry → calls `webhook_client.send_webhook(approved=True, dry_run=False)`.
7. Ledger records `send` entry.

No automated path from Orbi → live Discord exists. The human approval step (5) is permanent.

---

## Constitution headers (placeholder)

Public Discord posts from the Emissary must carry a constitution header in the channel description or pinned message:

```
This channel is operated by the DigiViCHI A.i Core under the Nomos disclosure protocol.
All posts are AI-drafted and human-approved. Community input is advisory only.
System: A.i Core Trinity (Claude·Codex·Antigravity) | Policy: DAN v2.5 | License: GPLv3
```

---

## Stop gates (permanent)

These remain stop-gated regardless of architecture progress:

- No automated post without Vi approval of exact text + channel.
- No inbound community event may trigger an action (only cognition/data).
- No raw Discord content in the MΣBUS envelope.
- No self-bot, user-token, or desktop automation path.
- No live connection until the Discord bot exists (Vi manual setup step).

---

## Phase sequencing

| Phase | Prerequisite | Work |
|-------|-------------|------|
| Now (current) | — | Offline scaffold, Nomos labels spec, approval ledger spec |
| Phase 8 start | Vi creates Discord app/bot/channels | Emissary adapter stub; inbound envelope wrapper; outbound ledger-verified send |
| Phase 8 mid | Live bot token in env | Slash-command registration plan → Vi approval → live |
| Phase 8+ | First live post approved | MΣBUS inbound routing; Urbi audit of community input |

---

Cross-refs: `discord_project/src/discord_project/webhook_client.py`, `NOMOS_DISCLOSURE_LABELS.md`, `APPROVAL_LEDGER_FORMAT.md`, `blueprints/00_BLUEPRINT_INDEX.md`
