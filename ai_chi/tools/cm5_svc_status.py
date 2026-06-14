"""Read-only status of hailo-ollama service + :8000 (no sudo, no host-side $() pitfalls)."""
import paramiko
REMOTE = (
    "echo ACTIVE=; systemctl is-active hailo-ollama; "
    "echo ENABLED=; systemctl is-enabled hailo-ollama 2>/dev/null; "
    "echo ---STATUS---; systemctl status hailo-ollama --no-pager 2>&1 | head -8; "
    "echo ---LISTEN8000---; ss -ltnp 2>/dev/null | grep :8000 || echo NONE; "
    "echo ---TAGS---; curl -s -m4 http://127.0.0.1:8000/api/tags 2>&1 | head -c 200; "
    "echo; echo ---PROC---; pgrep -af hailo-ollama || echo no-proc"
)
cli = paramiko.SSHClient(); cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect("192.168.2.2", username="vichi", allow_agent=True, look_for_keys=True, timeout=12)
_, so, se = cli.exec_command(REMOTE, timeout=40)
print((so.read().decode("utf-8", "replace") + se.read().decode("utf-8", "replace")).strip())
cli.close()
