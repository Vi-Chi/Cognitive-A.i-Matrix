import csv
import re
from pathlib import Path

ledger_md = Path("docs/PUBLIC_RELEASE_LEDGER.md").read_text(encoding="utf-8")
blocks = ledger_md.split("## ")

data = []
for block in blocks[1:]:
    lines = block.split("\n")
    title = lines[0].strip()
    entry = {"Date_Title": title}
    
    for line in lines[1:]:
        if line.startswith("- "):
            parts = line[2:].split(":", 1)
            if len(parts) == 2:
                key = parts[0].strip()
                val = parts[1].strip()
                entry[key] = val
    data.append(entry)

out_file = Path("workspace_staging/PUBLIC_RELEASE_LEDGER.csv")
out_file.parent.mkdir(parents=True, exist_ok=True)

with open(out_file, "w", newline="", encoding="utf-8") as f:
    if not data:
        writer = csv.writer(f)
        writer.writerow(["No data found"])
    else:
        # get all unique keys
        keys = ["Date_Title"]
        for d in data:
            for k in d.keys():
                if k not in keys:
                    keys.append(k)
        
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data)

print(f"Generated {out_file}")
