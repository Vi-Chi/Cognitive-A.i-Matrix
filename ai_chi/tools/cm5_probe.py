"""Read-only CM5 node probe over in-process SSH (paramiko) — no ssh.exe needed."""
import os, sys, paramiko

HOST, USER = "192.168.2.2", "vichi"
KEY = os.path.expandvars(r"%USERPROFILE%\.ssh\id_ed25519")

CMDS = [
    ("NODE", "hostname; uname -r; uptime"),
    ("DISK", "df -h / /home 2>/dev/null"),
    ("MEM", "free -h"),
    ("THERMAL", "vcgencmd measure_temp 2>/dev/null || cat /sys/class/thermal/thermal_zone0/temp"),
    ("THROTTLE", "vcgencmd get_throttled 2>/dev/null"),
    ("FAILED-UNITS", "systemctl --failed --no-legend || true"),
    ("HAILO-DEV", "ls -l /dev/hailo* 2>&1"),
    ("HAILO-ID", "hailortcli fw-control identify 2>&1 | head -25"),
    ("HAILO-SCAN", "hailortcli scan 2>&1 | head -6"),
    ("OLLAMA", "ollama list 2>&1 | head -10"),
    ("HAILO-OLLAMA", "command -v hailo-ollama; dpkg -l 2>/dev/null | grep -i hailo | awk '{print $2,$3}'; "
                     "systemctl is-active hailo-ollama 2>&1; ss -ltnp 2>/dev/null | grep -E ':8000|:11434' || true; "
                     "curl -s -m3 http://127.0.0.1:8000/api/tags 2>&1 | head -c 200"),
    ("AICORE-RUNS", "ls -1dt ~/aicore-runs/* 2>/dev/null | head -5"),
    ("PY-HAILO", "python3 -c \"import importlib.util as u; print('hailo_py', bool(u.find_spec('hailo_platform')))\" 2>&1"),
]

try:
    pkey = paramiko.Ed25519Key.from_private_key_file(KEY)
except Exception as e:
    print("KEYLOAD_NOTE:", e); pkey = None

cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect(HOST, username=USER, pkey=pkey, allow_agent=True, look_for_keys=True, timeout=12)
print("CONNECTED", HOST)
for name, cmd in CMDS:
    _, so, se = cli.exec_command(cmd, timeout=40)
    out = (so.read().decode("utf-8", "replace") + se.read().decode("utf-8", "replace")).strip()
    print(f"\n===== {name} =====")
    print(out or "(no output)")
cli.close()
print("\n=====DONE=====")
