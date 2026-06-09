# Compute Cost Estimator

## Purpose

Estimate the cost of running a task on each candidate compute tier.

## Inputs

- Runtime class.
- Model or tool.
- Expected duration.
- Memory requirement.
- Accelerator requirement.
- Local power estimate.
- Network transfer estimate.
- Verification overhead.
- Privacy risk buffer.

## Outputs

- Local CPU estimate.
- Local accelerator estimate.
- Local x86/GPU estimate.
- Decentralized compute estimate.
- Commercial API estimate.
- Refusal reason when no safe tier exists.

## v0 Implementation

Use static tables and conservative defaults. Replace with measured benchmarks
only after local tests exist.
