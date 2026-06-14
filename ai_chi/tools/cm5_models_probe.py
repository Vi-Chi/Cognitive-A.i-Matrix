"""Read-only: hailo-ollama serve config + available HEF models (for unit + NPU-audit plan)."""
import paramiko
REMOTE = r'''
echo ===CONFIG===
cat /etc/xdg/hailo-ollama/hailo-ollama.json 2>/dev/null
echo ===SERVED-NOW===
curl -s -m4 http://127.0.0.1:8000/api/tags 2>/dev/null
echo
echo ===ZOO-MANIFESTS===
ls -1 /usr/share/hailo-ollama/models/manifests 2>/dev/null
echo ===EMBED-AVAILABLE?===
ls -1 /usr/share/hailo-ollama/models/manifests | grep -iE 'embed|nomic|bge|minilm' || echo NO_EMBED_HEF
'''
cli = paramiko.SSHClient(); cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect("192.168.2.2", username="vichi", allow_agent=True, look_for_keys=True, timeout=12)
_, so, se = cli.exec_command(REMOTE, timeout=40)
print((so.read().decode("utf-8", "replace") + se.read().decode("utf-8", "replace")).strip())
cli.close()
