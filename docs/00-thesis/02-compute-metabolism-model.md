# Compute Metabolism Model

## Purpose

Describe compute as a budgeted metabolic cost instead of an unlimited resource.

## Model

```text
expected_net_value =
  expected_reward_or_value
  - compute_cost
  - storage_cost
  - bandwidth_cost
  - verification_cost
  - operational_overhead
  - risk_buffer
```

## Cost Classes

| Cost | Meaning |
| --- | --- |
| Compute | CPU, GPU, accelerator, API, or rented node cost. |
| Storage | Local disk, remote object storage, archive, or chain state. |
| Bandwidth | Network transfer and sync overhead. |
| Verification | Extra checks needed to trust the output. |
| Operational overhead | Setup, monitoring, queueing, retries, and cleanup. |
| Risk buffer | Privacy, legal, safety, and provider uncertainty. |

## Output

The first implementation should produce a local compute-decision record. That
record is enough for simulation, testing, and later audit.
