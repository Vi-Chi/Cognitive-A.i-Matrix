"""Run a minimal SIGMABUS CM negotiation trace."""

from __future__ import annotations

import json

from sigmabus_core import SigmaBusMessage, is_actionable


def collision_avoidance_trace() -> list[dict]:
    propose = SigmaBusMessage(
        msg_type="PROPOSE",
        sender_uid="agt-wibo835-nav-001",
        receiver_uid="agt-mv_osprey-nav-001",
        path="wibo835.cm.collision_avoidance",
        priority=2,
        payload={
            "conversation_id": "conv-collision-001",
            "proposal_id": "prop-collision-001",
            "subject": "collision_avoidance_manoeuvre",
            "situation": {"cpa_nm": 0.28, "tcpa_min": 8.2},
            "fallback": {"autonomous_action": "reduce_speed_to_3kn_and_alert_crew"},
        },
    ).to_envelope()

    agree = SigmaBusMessage(
        msg_type="AGREE",
        sender_uid="agt-mv_osprey-nav-001",
        receiver_uid="agt-wibo835-nav-001",
        path="mv_osprey.cm.collision_avoidance",
        priority=2,
        payload={
            "conversation_id": "conv-collision-001",
            "reply_to": propose["payload"]["msg_id"],
            "proposal_id": "prop-collision-001",
            "commitment": {"action": "maintain_course_and_speed"},
        },
    ).to_envelope()

    return [propose, agree]


def main() -> None:
    trace = collision_avoidance_trace()
    for message in trace:
        if not is_actionable(message):
            raise SystemExit(f"message failed trust gate: {message['identity']['msg_id']}")
    print(json.dumps(trace, indent=2))


if __name__ == "__main__":
    main()
