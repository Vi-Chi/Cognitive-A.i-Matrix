"""Hailo-10H vs CPU LLM benchmark on the CM5, over in-process SSH (paramiko)."""
import os, paramiko

HOST, USER = "192.168.2.2", "vichi"
KEY = os.path.expandvars(r"%USERPROFILE%\.ssh\id_ed25519")

REMOTE = r'''
python3 - <<'PYEOF'
import json, time, urllib.request
PROMPT = "Explain, in one short paragraph, the COLREGs give-way obligation for a power-driven vessel in a crossing situation."
def bench(url, model, npred=128):
    body = json.dumps({"model": model, "prompt": PROMPT, "stream": False,
                       "options": {"num_predict": npred, "temperature": 0.0}}).encode()
    req = urllib.request.Request(url + "/api/generate", data=body,
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    try:
        d = json.loads(urllib.request.urlopen(req, timeout=300).read())
    except Exception as e:
        return f"ERROR {type(e).__name__}: {e}"
    wall = time.time() - t0
    ec, ed = d.get("eval_count"), d.get("eval_duration")
    pc, pd = d.get("prompt_eval_count"), d.get("prompt_eval_duration")
    toks = ec / (ed / 1e9) if ec and ed else None
    ttft = (d.get("load_duration", 0) + (pd or 0)) / 1e9
    return {"eval_count": ec, "tok_s": round(toks, 2) if toks else None,
            "ttft_s": round(ttft, 3), "wall_s": round(wall, 2),
            "prompt_tok": pc}
def temp():
    try: return open("/sys/class/thermal/thermal_zone0/temp").read().strip()
    except Exception: return "?"
print("temp_before_mC:", temp())
print("HAILO-10H :8000 qwen2.5-coder:1.5b ->", bench("http://127.0.0.1:8000", "qwen2.5-coder:1.5b"))
print("temp_mid_mC   :", temp())
print("CPU    :11434 qwen2.5:1.5b        ->", bench("http://127.0.0.1:11434", "qwen2.5:1.5b"))
print("temp_after_mC :", temp())
PYEOF
'''

cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect(HOST, username=USER, allow_agent=True, look_for_keys=True, timeout=12)
_, so, se = cli.exec_command(REMOTE, timeout=320)
print((so.read().decode("utf-8", "replace") + se.read().decode("utf-8", "replace")).strip())
cli.close()
