"""Exporte un checkpoint d'entrainement en poids fp16, prets a publier.

Un checkpoint d'entrainement embarque l'etat de l'optimiseur (momentums Muon,
moments AdamW), les etats RNG et les compteurs : ~1 Go pour un modele de 123M.
L'inference n'a besoin que des poids. En fp16, on tombe autour de 250 Mo — assez
pour une GitHub release (limite 2 Go), alors que le depot lui-meme refuse tout
fichier au-dela de 100 Mo.

Usage : python export_weights.py runs/gpu1/sft/ckpt_best.pt baguette-123m-sft.pt
"""
import sys
from pathlib import Path

import torch

src = Path(sys.argv[1])
dst = Path(sys.argv[2] if len(sys.argv) > 2 else "baguette-123m-sft.pt")

ck = torch.load(src, map_location="cpu", weights_only=False)

poids = {k: (v.half() if v.is_floating_point() else v)
         for k, v in ck["model"].items()}

torch.save({
    "model": poids,
    "model_cfg": ck["model_cfg"],
    "step": ck.get("step"),
    "tokens_seen": ck.get("tokens_seen"),
    "val_loss": ck.get("val_loss"),
    "stage": ck.get("stage"),
}, dst)

avant = src.stat().st_size / 2**20
apres = dst.stat().st_size / 2**20
print(f"[i] {src.name} : {avant:.0f} Mo -> {dst.name} : {apres:.0f} Mo "
      f"({avant / apres:.1f}x plus petit)")
print(f"[i] step {ck.get('step')} · val loss {ck.get('val_loss', float('nan')):.4f}")