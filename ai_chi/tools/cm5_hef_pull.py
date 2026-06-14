"""Kick off a HEF model pull on the node via the hailo-ollama API (no sudo). Best-effort."""
import paramiko
MODEL = "qwen2.5-instruct:1.5b"
REMOTE = (
    "echo ===ENDPOINTS===; "
    "curl -s -o /dev/null -w 'pull_http=%{http_code}\\n' -X POST http://127.0.0.1:8000/api/pull "
    "-d '{\"name\":\"" + MODEL + "\",\"stream\":false}' --max-time 6 || true; "
    "echo ===BG_PULL===; "
    "nohup curl -s -X POST http://127.0.0.1:8000/api/pull -d '{\"name\":\"" + MODEL + "\"}' "
    "> /home/vichi/hef_pull.log 2>&1 & echo started_pid=$!; "
    "sleep 6; echo ---log_tail---; tail -c 400 /home/vichi/hef_pull.log 2>/dev/null; "
    "echo; echo ===TAGS_NOW===; curl -s -m5 http://127.0.0.1:8000/api/tags"
)
cli = paramiko.SSHClient(); cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect("192.168.2.2", username="vichi", allow_agent=True, look_for_keys=True, timeout=12)
_, so, se = cli.exec_command(REMOTE, timeout=40)
print((so.read().decode("utf-8", "replace") + se.read().decode("utf-8", "replace")).strip())
cli.close()
