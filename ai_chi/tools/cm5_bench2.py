"""Streamed inter-token benchmark (warm) — Hailo-10H vs CPU — over paramiko."""
import os, paramiko
HOST, USER = "192.168.2.2", "vichi"

REMOTE = r'''
python3 - <<'PYEOF'
import json, time, urllib.request
PROMPT = "Write a detailed 120-word explanation of COLREGs crossing-situation rules for an autonomous sailing vessel."
def warm(url, model):
    b = json.dumps({"model": model, "prompt": "hi", "stream": False, "options": {"num_predict": 1}}).encode()
    try: urllib.request.urlopen(urllib.request.Request(url+"/api/generate", data=b, headers={"Content-Type":"application/json"}), timeout=300).read()
    except Exception as e: return f"warm_err {e}"
    return "warm_ok"
def stream_bench(url, model, npred=120):
    b = json.dumps({"model": model, "prompt": PROMPT, "stream": True, "options": {"num_predict": npred, "temperature": 0.0}}).encode()
    req = urllib.request.Request(url+"/api/generate", data=b, headers={"Content-Type":"application/json"})
    t0=time.time(); tf=None; tl=t0; n=0; ec=ed=None
    try:
        for line in urllib.request.urlopen(req, timeout=300):
            line=line.strip()
            if not line: continue
            o=json.loads(line)
            if o.get("response"):
                n+=1; tl=time.time()
                if tf is None: tf=tl
            if o.get("done"):
                ec=o.get("eval_count"); ed=o.get("eval_duration"); break
    except Exception as e:
        return f"ERROR {type(e).__name__}: {e}"
    gen = (n-1)/(tl-tf) if (tf and n>1) else None
    api = ec/(ed/1e9) if (ec and ed) else None
    return {"tokens": n, "ttft_s": round(tf-t0,3) if tf else None,
            "gen_tok_s": round(gen,2) if gen else None,
            "api_tok_s": round(api,2) if api else None}
def temp():
    try: return round(int(open("/sys/class/thermal/thermal_zone0/temp").read().strip())/1000.0,1)
    except Exception: return "?"
print("warm hailo:", warm("http://127.0.0.1:8000","qwen2.5-coder:1.5b"))
print("warm cpu  :", warm("http://127.0.0.1:11434","qwen2.5:1.5b"))
print("temp_before_C:", temp())
print("HAILO-10H :8000 ->", stream_bench("http://127.0.0.1:8000","qwen2.5-coder:1.5b"))
print("temp_mid_C   :", temp())
print("CPU    :11434 ->", stream_bench("http://127.0.0.1:11434","qwen2.5:1.5b"))
print("temp_after_C :", temp())
PYEOF
'''
cli = paramiko.SSHClient(); cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect(HOST, username=USER, allow_agent=True, look_for_keys=True, timeout=12)
_, so, se = cli.exec_command(REMOTE, timeout=320)
print((so.read().decode("utf-8","replace")+se.read().decode("utf-8","replace")).strip())
cli.close()
