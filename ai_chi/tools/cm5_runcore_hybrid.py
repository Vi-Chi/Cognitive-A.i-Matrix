"""Capstone: full Reality Loop on the CM5 with hybrid NPU auditing (reason->10H, embed->CPU)."""
import paramiko
D = "/home/vichi/aicore-live"
PP = f"{D}:{D}/mebus_src:{D}/cm_repo"
HEADER = (
    f"cd {D}\n"
    f"export PYTHONPATH={PP}\n"
    "export URBI_HYBRID=1\n"
    "export URBI_HAILO_OLLAMA=http://127.0.0.1:8000\n"
)
BODY = r'''
echo ===RUN_CORE_HYBRID_NPU===
python3 -m ai_chi.run_core 2>&1 | tail -6
echo ===LAST_BELIEF===
tail -1 data/ledger/audit_verdicts.jsonl
'''
cli = paramiko.SSHClient(); cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect("192.168.2.2", username="vichi", allow_agent=True, look_for_keys=True, timeout=12)
_, so, se = cli.exec_command(HEADER + BODY, timeout=200)
print((so.read().decode("utf-8", "replace") + se.read().decode("utf-8", "replace")).strip())
cli.close()
