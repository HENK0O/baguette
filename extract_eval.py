"""Extrait le VRAI texte de validation, jamais vu a l'entrainement.

encode_pretrain() consomme les .jsonl en entier et tire au sort les documents de
validation avec random.Random(1234). Lire la fin des fichiers bruts ne donne donc
PAS des donnees tenues a l'ecart : ce sont des donnees d'entrainement.

Ce script rejoue exactement le meme tirage (meme seed, meme ordre de fichiers,
meme taille de lot) et recupere le texte brut des documents partis en validation.

Usage : python extract_eval.py <data_dir> <sortie.txt> [n_chars]
"""
import random
import sys
from pathlib import Path

import data as D

data_dir = Path(sys.argv[1])
out_path = Path(sys.argv[2])
n_chars = int(sys.argv[3]) if len(sys.argv) > 3 else 400_000

VAL_FRAC = 0.005          # valeurs par defaut de encode_pretrain
MIN_VAL_TOKENS = 32768
BATCH = 1000
SEED = 1234

tok = D.load_tokenizer(data_dir / "tokenizer.json")
eot = tok.token_to_id(D.EOT)
raw = data_dir / "raw"

# meme ordre que le mix passe a prepare : fineweb, wiki, chat
paths = [raw / f"{n}.jsonl" for n in ("fineweb", "wiki", "chat")
         if (raw / f"{n}.jsonl").exists()]
print("[i] sources :", [p.name for p in paths])

rng = random.Random(SEED)
val_tokens = 0
textes, total, buf, fini = [], 0, [], False

for p in paths:
    if fini:
        break
    for rec in D.iter_jsonl(p):
        buf.append(rec["t"])
        if len(buf) < BATCH:
            continue
        for txt, enc in zip(buf, tok.encode_batch(buf)):
            ids = enc.ids + [eot]
            # reproduction fidele : le or court-circuite, donc rng.random()
            # n'est PAS appele tant que le plancher n'est pas atteint
            to_val = val_tokens < MIN_VAL_TOKENS or rng.random() < VAL_FRAC
            if to_val:
                val_tokens += len(ids)
                textes.append(txt)
                total += len(txt)
        buf = []
        if total >= n_chars:
            fini = True
            break

texte = "\n\n".join(textes)[:n_chars]
out_path.write_text(texte, encoding="utf-8")
print(f"[i] {out_path} : {len(texte)} caracteres, {len(textes)} documents de validation")
