# ICP Compute Registry Spec

## Purpose

Describe a future ICP-facing registry without requiring canister deployment in
v0.

## Registry Objects

- Provider capability profile.
- Job lifecycle record.
- Compute decision record.
- Public benchmark summary.
- Reputation event.

## Local First

The local schemas in `specs/` are the source of truth for v0. A canister model
can mirror a subset later.

## Privacy Boundary

Only sanitized metadata may leave local storage. Private job payloads, memory,
logs, and credentials remain local.
