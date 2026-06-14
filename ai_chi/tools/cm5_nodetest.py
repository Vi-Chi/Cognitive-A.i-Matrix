"""Run the aicore suite, live run_core, and Hailo endpoint check ON the CM5 (paramiko)."""
import paramiko
D = "/home/vichi/aicore-live"
PP = f"{D}:{D}/mebus_src:{D}/cm_repo"
REMOTE = f'''
echo ===TESTS_ON_CM5===
cd {D} && PYTHONPATH={PP} python3 -m unittest discover -s aicore/tests -p "test_*.py" 2>&1 | tail -6
echo
echo ===RUN_CORE_LIVE_CPU_AUDITOR===
cd {D} && PYTHONPATH={PP} python3 -m ai_chi.run_core 2>&1 | tail -8
echo
echo ===ENDPOINT_RESOLVE_WITH_HAILO_SET===
cd {D} && PYTHONPATH={PP} URBI_HAILO_OLLAMA=http://127.0.0.1:8000 python3 -c "from bridge.endpoint import resolve_ollama_base; print(resolve_ollama_base())" 2>&1
echo
echo ===LEDGER_STREAMS===
ls -1 {D}/data/ledger 2>/dev/null
echo "--- last verdict ---"; tail -1 {D}/data/ledger/audit_verdicts.jsonl 2>/dev/null
echo "--- last calibration ---"; tail -1 {D}/data/ledger/calibration.jsonl 2>/dev/null
'''
cli = paramiko.SSHClient(); cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect("192.168.2.2", username="vichi", allow_agent=True, look_for_keys=True, timeout=12)
_, so, se = cli.exec_command(REMOTE, timeout=300)
print((so.read().decode("utf-8", "replace") + se.read().decode("utf-8", "replace")).strip())
cli.close()
