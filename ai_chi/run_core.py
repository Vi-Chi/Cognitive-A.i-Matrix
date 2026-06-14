"""Run the P0 Reality Loop once.

Use ``--fake-auditor`` for local smoke tests that must not touch the live
Cognitive Matrix context store. Without it, the existing Urbi bridge constructs
the real v2.1 auditor lazily.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Entry-point path hygiene. When run as a script, sys.path[0] is this file's dir
# (aicore/), not the A.i root. Drop the script dir + cwd; ensure the A.i root is
# importable so ``import ai_chi`` resolves and top-level ``mebus`` resolves to the
# real Ai_Stack/MEBUS package.
_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
for _p in (str(_HERE), ""):
    while _p in sys.path:
        sys.path.remove(_p)
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from ai_chi.core.loop import RealityLoop, message_confidence, message_record_id


class FakeSuspendingAuditor:
    """Offline smoke-test auditor that preserves the [=] path."""

    def audit(self, claim: str, **_: object) -> dict:
        return {
            "state": "=",
            "confidence": 0.4,
            "reason": "offline smoke test suspension",
            "route": "dream_layer",
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fake-auditor", action="store_true")
    parser.add_argument("--ledger-dir", default="data/ledger")
    parser.add_argument(
        "--claim",
        default="Claim: The physical CM5 node will stay thermally safe under load next 5 minutes.",
    )
    args = parser.parse_args()

    loop = RealityLoop(
        ledger_dir=args.ledger_dir,
        auditor=FakeSuspendingAuditor() if args.fake_auditor else None,
    )
    _, audit = loop.submit_claim(args.claim, provenance="urn:console:run_core")
    pred_id = message_record_id(audit)
    conf = message_confidence(audit)
    _, cal = loop.record_outcome(
        prediction_id=pred_id,
        confidence=conf,
        actual_state="Thermal safe constraint held true.",
        matched=True,
    )

    print("Reality Loop P0 complete")
    print(f"audit_sigma={audit.sigma} prediction_id={pred_id} confidence={conf:.2f}")
    print(f"cal_sigma={cal.sigma} shift={cal.payload['epistemic_shift']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
