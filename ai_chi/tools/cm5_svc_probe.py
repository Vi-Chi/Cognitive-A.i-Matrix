"""Read-only probe: how is hailo-ollama actually run? (to draft a systemd unit). No sudo."""
import paramiko
REMOTE = r'''
echo ===RUNNING-PROC===
pgrep -af hailo-ollama || echo none
echo ===HELP===
hailo-ollama --help 2>&1 | head -25
echo ===UNIT-FILES===
systemctl list-unit-files 2>/dev/null | grep -i hailo || echo no-unit-files
ls -l /usr/lib/systemd/system/*hailo* /etc/systemd/system/*hailo* 2>/dev/null || echo no-unit-on-disk
echo ===PKG-CONTENTS===
dpkg -L hailo-h10-all hailo-gen-ai-model-zoo 2>/dev/null | grep -iE 'service|hailo-ollama|/bin/' | head
echo ===BIN-TYPE===
file /usr/bin/hailo-ollama; head -5 /usr/bin/hailo-ollama 2>/dev/null
echo ===LISTEN===
ss -ltnp 2>/dev/null | grep :8000 || echo not-listening
echo ===WHOAMI-NOPASS-SUDO-CHECK===
sudo -n true 2>&1 | head -1 || true
'''
cli = paramiko.SSHClient(); cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect("192.168.2.2", username="vichi", allow_agent=True, look_for_keys=True, timeout=12)
_, so, se = cli.exec_command(REMOTE, timeout=60)
print((so.read().decode("utf-8", "replace") + se.read().decode("utf-8", "replace")).strip())
cli.close()
