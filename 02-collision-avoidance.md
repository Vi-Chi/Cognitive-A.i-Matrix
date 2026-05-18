# Example: Collision Avoidance Negotiation

## Scenario

Vessel **wibo835** (autonomous sailing vessel) and vessel **MV Osprey** (commercial motor vessel) are on converging courses in open water. The geometry is a crossing situation — wibo835 is the give-way vessel under COLREGs Rule 16. Both vessels are running ΣBUS CM Level 2 compliant navigation agents.

**Initial conditions:**
- CPA: 0.28 nm
- TCPA: 8.2 minutes
- Geometry: crossing, wibo835 gives way (port-to-starboard crossing)
- Link: VHF DSC digital, ~1200 baud, ~200ms RTT

---

## Timeline

```
T+00:00  CEP pattern fires on wibo835: cpa_critical (CPA 0.28nm < 0.5nm threshold)
T+00:01  ALERT broadcast on wibo835 internal bus
T+00:02  Navigation agent receives alert, begins reasoning
T+00:04  Navigation agent sends PROPOSE to MV Osprey nav agent
T+00:06  MV Osprey nav agent receives PROPOSE, evaluates
T+00:09  MV Osprey nav agent sends AGREE
T+00:10  wibo835 nav agent receives AGREE, executes course alteration
T+00:11  wibo835 nav agent sends CONFIRM
T+00:12  MV Osprey nav agent logs CONFIRM, continues monitoring
T+08:30  CPA resolves — both agents log RETRACT of commitments
```

---

## Full Message Trace

### Message 1 — ALERT (internal, wibo835 bus)

```json
{
  "msg_type": "ALERT",
  "msg_id": "01HVAK2X-ALERT-CPA-001",
  "sender_uid": "agt-wibo835-cep-001",
  "receiver_uid": null,
  "timestamp_us": 1716123456000000,
  "priority": 1,
  "alert_id": "alert-cpa-001",
  "category": "collision_risk",
  "severity": "urgent",
  "subject": "CPA below safe threshold",
  "data": {
    "target_mmsi": 123456789,
    "target_name": "MV OSPREY",
    "target_uid": "agt-mv-osprey-nav-001",
    "cpa_nm": 0.28,
    "tcpa_min": 8.2,
    "bearing_deg": 047,
    "geometry": "crossing_give_way",
    "colreg_situation": "Rule_15_crossing",
    "recommended_action": "PROPOSE collision avoidance — wibo835 is give-way vessel"
  },
  "expires_us": 1716124056000000,
  "source_pattern": "cpa_critical",
  "evidence_paths": [
    "wibo835.nav.ais.target_123456789.cpa_nm",
    "wibo835.nav.ais.target_123456789.tcpa_min",
    "wibo835.nav.ais.target_123456789.bearing_deg"
  ]
}
```

---

### Message 2 — PROPOSE (wibo835 → MV Osprey)

*Sent at T+00:04 after reasoning cycle. TTL set to 60s to account for HF link latency.*

```json
{
  "msg_type": "PROPOSE",
  "msg_id": "01HVAK2X-PROP-COL-001",
  "sender_uid": "agt-wibo835-nav-001",
  "receiver_uid": "agt-mv-osprey-nav-001",
  "timestamp_us": 1716123460000000,
  "conversation_id": "conv-col-wibo835-osprey-001",
  "conversation_step": 1,
  "priority": 2,
  "proposal_id": "prop-col-001",
  "proposal_ttl_s": 60,
  "subject": "collision_avoidance_manoeuvre",

  "situation": {
    "t_assessment_us": 1716123460000000,
    "cpa_nm": 0.28,
    "tcpa_min": 8.2,
    "bearing_deg_t": 047,
    "relative_bearing_deg": 035,
    "geometry": "crossing_port_to_starboard",
    "give_way_vessel": "wibo835",
    "stand_on_vessel": "mv_osprey",
    "applicable_rules": ["COLREG_Rule_15", "COLREG_Rule_16", "COLREG_Rule_17"]
  },

  "proposed_actions": [
    {
      "agent_uid": "agt-wibo835-nav-001",
      "action": "alter_course_starboard",
      "value": 30,
      "unit": "degrees_relative",
      "new_heading_approx_deg": 215,
      "duration_nm": 2.0,
      "colreg_rule": 16,
      "rationale": "Give-way vessel executes substantial course alteration to starboard per Rule 16",
      "effect_cpa_nm": 1.4
    }
  ],

  "requested_actions": [
    {
      "agent_uid": "agt-mv-osprey-nav-001",
      "action": "maintain_course_and_speed",
      "current_heading_deg": 285,
      "current_speed_kn": 12.4,
      "colreg_rule": 17,
      "rationale": "Stand-on vessel maintains course and speed per Rule 17",
      "monitoring_required": "monitor_give_way_compliance"
    }
  ],

  "fallback": {
    "condition": "no_agreement_by_ttl",
    "autonomous_action": "reduce_speed_to_3kn",
    "rationale": "Speed reduction increases TCPA, allows more time for resolution",
    "effect_cpa_nm": 0.6,
    "will_execute_at_us": 1716123520000000
  },

  "monitoring": {
    "resume_normal_heading_when": "cpa_nm > 1.0",
    "abort_condition": "cpa_nm < 0.1",
    "abort_action": "emergency_stop_and_alert_crew"
  },

  "signature": "base64:ed25519sig..."
}
```

---

### Message 3 — AGREE (MV Osprey → wibo835)

*Received at T+00:09. MV Osprey agent evaluated the proposal, verified geometry, confirmed it is stand-on vessel, accepts.*

```json
{
  "msg_type": "AGREE",
  "msg_id": "01HVAK2X-AGREE-001",
  "sender_uid": "agt-mv-osprey-nav-001",
  "receiver_uid": "agt-wibo835-nav-001",
  "timestamp_us": 1716123469000000,
  "conversation_id": "conv-col-wibo835-osprey-001",
  "conversation_step": 2,
  "reply_to": "01HVAK2X-PROP-COL-001",
  "proposal_id": "prop-col-001",

  "commitment": {
    "action": "maintain_course_and_speed",
    "heading_deg": 285,
    "speed_kn": 12.4,
    "until_cpa_resolved": true,
    "resolution_condition": "cpa_nm > 1.0",
    "monitoring_path": "mv-osprey.nav.position.ais.cog_deg",
    "colreg_rule": 17
  },

  "assessment": {
    "geometry_verified": true,
    "stand_on_confirmed": true,
    "proposed_manoeuvre_adequate": true,
    "projected_cpa_after_manoeuvre_nm": 1.4,
    "notes": "Course alteration 30 deg starboard is appropriate and sufficient."
  },

  "signature": "base64:ed25519sig..."
}
```

---

### Message 4 — CONFIRM (wibo835 → MV Osprey)

*Sent at T+00:11 after course alteration executed and confirmed by autopilot feedback.*

```json
{
  "msg_type": "CONFIRM",
  "msg_id": "01HVAK2X-CONF-001",
  "sender_uid": "agt-wibo835-nav-001",
  "receiver_uid": "agt-mv-osprey-nav-001",
  "timestamp_us": 1716123471000000,
  "conversation_id": "conv-col-wibo835-osprey-001",
  "conversation_step": 3,
  "reply_to": "01HVAK2X-AGREE-001",
  "proposal_id": "prop-col-001",

  "result": {
    "executed": true,
    "action_taken": "alter_course_starboard_30_deg",
    "execution_time_us": 1716123470500000,
    "new_heading_deg": 215,
    "autopilot_confirmed": true,
    "current_cpa_estimate_nm": 1.38,
    "current_tcpa_min": 9.1,
    "monitoring_active": true
  },

  "signature": "base64:ed25519sig..."
}
```

---

### Message 5 — RETRACT of commitments (T+08:30)

*Both agents send RETRACT when CPA resolves above 1.0nm. Conversation closes.*

**wibo835 → MV Osprey:**

```json
{
  "msg_type": "RETRACT",
  "msg_id": "01HVAK2X-RETR-001",
  "sender_uid": "agt-wibo835-nav-001",
  "receiver_uid": "agt-mv-osprey-nav-001",
  "timestamp_us": 1716123966000000,
  "conversation_id": "conv-col-wibo835-osprey-001",
  "conversation_step": 4,
  "proposal_id": "prop-col-001",
  "reason": "Situation resolved. CPA now 1.42nm. Resuming original heading.",
  "outcome": {
    "minimum_cpa_achieved_nm": 1.38,
    "situation_duration_min": 8.4,
    "manoeuvre_successful": true
  }
}
```

---

## State Machine Trace

```
[wibo835 nav agent]                    [MV Osprey nav agent]
      │                                       │
      │  CEP fires: cpa_critical              │
      │  Reasoning cycle: ~450ms             │
      │                                       │
      ├──── PROPOSE ──────────────────────────►│
      │     T+00:04                           │  Receiving PROPOSE
      │                                       │  Verify geometry: ✓
      │                                       │  Verify authority: ✓
      │                                       │  Evaluate proposal: adequate ✓
      │                                       │
      │◄──── AGREE ───────────────────────────┤
      │     T+00:09                           │
      │                                       │
      │  Execute course alteration            │  Monitor wibo835 AIS track
      │  Autopilot confirms new heading       │
      │                                       │
      ├──── CONFIRM ──────────────────────────►│
      │     T+00:11                           │  Log outcome
      │                                       │
      │  [Both monitoring CPA]                │
      │                                       │
      │  CPA resolves > 1.0nm at T+08:30     │
      │                                       │
      ├──── RETRACT ──────────────────────────►│
      │◄──── RETRACT ──────────────────────────┤
      │                                       │
   [COMPLETE]                             [COMPLETE]
```

---

## Decision Journal Entry (wibo835)

```json
{
  "journal_type": "decision",
  "timestamp_us": 1716123470500000,
  "decision_id": "dec-001",
  "conversation_id": "conv-col-wibo835-osprey-001",
  "decision": "alter_course_starboard_30_degrees",
  "inputs": {
    "cpa_nm": {"value": 0.28, "trust": 0.94, "source": "wibo835.nav.ais.target_123456789.cpa_nm"},
    "tcpa_min": {"value": 8.2, "trust": 0.94, "source": "wibo835.nav.ais.target_123456789.tcpa_min"},
    "geometry": {"value": "crossing_give_way", "trust": 0.92},
    "peer_agreement": {"msg_id": "01HVAK2X-AGREE-001", "trust": 0.87}
  },
  "rules_applied": ["COLREG_Rule_15", "COLREG_Rule_16"],
  "alternatives_considered": [
    {"action": "reduce_speed", "rejected_reason": "insufficient CPA improvement"},
    {"action": "maintain_course", "rejected_reason": "violates Rule 16 give-way duty"}
  ],
  "confidence": 0.91,
  "human_notified": false,
  "human_override_active": false,
  "outcome_pending": true
}
```

---

## Notes for Implementors

1. The `proposal_ttl_s` of 60 seconds accounts for the ~200ms RTT of the VHF link plus reasoning time. On a lower-bandwidth link (HF, satellite), increase TTL accordingly.

2. The fallback action (reduce_speed_to_3kn) is specified in the PROPOSE so MV Osprey's agent knows what wibo835 will do autonomously if negotiation fails. This supports COLREGs compliance even without agreement.

3. Both agents continue monitoring after CONFIRM. If MV Osprey's agent detects that wibo835 is NOT executing the agreed manoeuvre, it SHOULD send an ALERT internally and consider whether to escalate to human.

4. The `effect_cpa_nm` in the PROPOSE gives the peer a verifiable prediction. If the actual CPA after manoeuvre significantly differs from the prediction, this is evidence of a world-model discrepancy and should reduce trust.

5. Both agents log the full conversation to their decision journals. This produces a complete audit trail that could be presented to a maritime authority if the encounter were later reviewed.
