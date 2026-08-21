"""Rebinarise le corpus SFT en incluant les sources supplementaires.

Ne retouche PAS au tokenizer : le modele pre-entraine ne serait plus compatible.

La source `reasoning` est volontairement exclue : ses blocs <think> font 300 mots
de monologue hesitant, et le modele avait appris a les imiter sur des questions
triviales. Le benchmark a confirme le gain apres retrait.

Usage : python rebuild_sft.py <data_dir> [repeat_distill] [repeat_math]
"""
import sys
from pathlib import Path

import data as D

data_dir = Path(sys.argv[1])
rep_distill = int(sys.argv[2]) if len(sys.argv) > 2 else 25
rep_math = int(sys.argv[3]) if len(sys.argv) > 3 else 1
raw = data_dir / "raw"

tok = D.load_tokenizer(data_dir / "tokenizer.json")

paths = []
for name in ("chat", "alpaca"):
    p = raw / f"{name}.jsonl"
    if p.exists():
        paths.append(p)

for name, rep in (("distill", rep_distill), ("math", rep_math)):
    p = raw / f"{name}.jsonl"
    if p.exists():
        paths.extend([p] * rep)
        print(f"[i] {name}.jsonl inclus {rep}x")
    else:
        print(f"[!] {name}.jsonl absent de {raw}")

print("[i] sources :", [p.name for p in paths])
report = D.encode_sft(tok, paths, data_dir, max_len=1024)
print(report)
