"""Live hybrid audit on the CM5: reason->Hailo-10H :8000, embed->CPU :11434."""
import paramiko
D = "/home/vichi/aicore-live"
PP = f"{D}:{D}/mebus_src:{D}/cm_repo"

# Interpolated header only (no braces collisions); body is a raw literal (no f-string).
HEADER = (
    f"cd {D}\n"
    f"export PYTHONPATH={PP}\n"
    "export URBI_HYBRID=1\n"
    "export URBI_HAILO_OLLAMA=http://127.0.0.1:8000\n"
)
BODY = r'''python3 - <<'PYEOF'
import time
from bridge.endpoint import apply_hybrid
info = apply_hybrid()
print("ROUTING:", info)
import audit
print("generate_fn:", audit.ollama_generate.__name__, "| embed_base:", audit.OLLAMA_BASE, "| REASON_MODEL:", audit.REASON_MODEL)
print("npu_generate_probe:", repr(audit.ollama_generate("Reply with the single word OK.")[:40]))
a = audit.TriStateAuditor()
for claim in [
    "A power-driven vessel in a crossing situation gives way to the vessel on its starboard side.",
    "This boat will absolutely never capsize under any conditions whatsoever.",
]:
    t = time.time(); v = a.audit(claim); dt = time.time() - t
    print("[%s] conf=%s route=%s (%.1fs) :: %s" % (v["state"], v["confidence"], v["route"], dt, claim[:48]))
PYEOF
'''
cli = paramiko.SSHClient(); cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect("192.168.2.2", username="vichi", allow_agent=True, look_for_keys=True, timeout=12)
_, so, se = cli.exec_command(HEADER + BODY, timeout=200)
print((so.read().decode("utf-8", "replace") + se.read().decode("utf-8", "replace")).strip())
cli.close()
