"""Deploy current aicore + mebus + cognitive_matrix_repo to the CM5 over SFTP (paramiko)."""
import os, zipfile, paramiko

ROOT = r"C:\Users\Vi Chi\Desktop\Projectz\A.i"
AICORE = os.path.join(ROOT, "aicore")
MEBUS  = os.path.join(ROOT, "Ai_Stack", "MEBUS", "mebus", "src", "mebus")
CMREPO = os.path.join(ROOT, "Ai_Stack", "Urbi", "cognitive_matrix_repo")
ZIP = os.path.join(os.environ["TEMP"], "aicore_deploy.zip")
REMOTE = "/home/vichi/aicore-live"

EXCL_DIRS = {"__pycache__", ".git", ".venv", "node_modules", "data", "backups",
             "archive", "archives", "staging", "source_tree", "doc", "reports", ".pytest_cache"}
EXCL_EXT = (".pyc", ".bak", ".log")

def add_tree(z, base, prefix):
    n = 0
    for dp, dns, fns in os.walk(base):
        dns[:] = [d for d in dns if d not in EXCL_DIRS]
        for fn in fns:
            if fn.endswith(EXCL_EXT):
                continue
            full = os.path.join(dp, fn)
            arc = os.path.join(prefix, os.path.relpath(full, base)).replace("\\", "/")
            z.write(full, arc); n += 1
    return n

with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
    a = add_tree(z, AICORE, "aicore")
    m = add_tree(z, MEBUS, "mebus_src/mebus")
    c = add_tree(z, CMREPO, "cm_repo")
print(f"zip built: {ZIP}  ({os.path.getsize(ZIP)} bytes)  aicore={a} mebus={m} cm_repo={c}")

cli = paramiko.SSHClient(); cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect("192.168.2.2", username="vichi", allow_agent=True, look_for_keys=True, timeout=12)

def run(cmd, t=120):
    _, so, se = cli.exec_command(cmd, timeout=t)
    return (so.read().decode("utf-8", "replace") + se.read().decode("utf-8", "replace")).strip()

print("mkdir:", run(f"mkdir -p {REMOTE} && echo ok"))
sftp = cli.open_sftp(); sftp.put(ZIP, "/home/vichi/aicore_deploy.zip"); sftp.close()
print("uploaded zip")
print("extract:", run(f"cd {REMOTE} && python3 -c \"import zipfile; zipfile.ZipFile('/home/vichi/aicore_deploy.zip').extractall('.')\" && echo EXTRACTED && find . -maxdepth 2 -name '*.py' | wc -l"))
pp = f"{REMOTE}:{REMOTE}/mebus_src:{REMOTE}/cm_repo"
print("import-check:", run(f"cd {REMOTE} && PYTHONPATH={pp} python3 -c \"import ai_chi, mebus; from ai_chi.urbi.pattern.aggregator import PhiAggregator; print('IMPORTS_OK', mebus.__version__)\" 2>&1"))
cli.close()
print("DEPLOY_DONE")
