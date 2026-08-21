"""
data.py — Téléchargement des corpus français, tokenizer BPE maison, binarisation.

Pourquoi un tokenizer maison plutôt que celui de Qwen3 ?
  Le vocab de Qwen3 fait 151 936 tokens. Sur un modèle de 60M params, la matrice
  d'embedding ferait à elle seule 87M params (soit 60% du modèle pour du chinois,
  de l'arabe et du code qu'on n'utilisera jamais). Un BPE de 16k entraîné sur du
  français pur donne une meilleure compression sur NOS données et libère tout le
  budget de params pour les couches transformer.

Corpus retenus (tous vérifiés existants sur le Hub) :
  fineweb  HuggingFaceFW/fineweb-2  config fra_Latn   -> web français filtré, très gros
  wiki     wikimedia/wikipedia      config 20231101.fr -> français propre et bien écrit
  chat     angeluriot/french_instruct                  -> 275k conversations FR multi-tours
  alpaca   jpacifico/French-Alpaca-dataset-Instruct-110K -> 110k paires instruction/réponse
"""

from __future__ import annotations

import json
import os
import random
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np

# ---- tokens spéciaux (format ChatML + balises de réflexion, comme Qwen) ---------------
EOT = "<|endoftext|>"
IM_START = "<|im_start|>"
IM_END = "<|im_end|>"
THINK = "<think>"
THINK_END = "</think>"
SPECIALS = [EOT, IM_START, IM_END, THINK, THINK_END]

DTYPE = np.uint16  # suffit jusqu'à 65 535 tokens de vocab


# --------------------------------------------------------------------------------------
# Sources de données
# --------------------------------------------------------------------------------------
@dataclass
class Source:
    name: str
    repo: str
    config: str | None
    split: str
    kind: str  # "text" | "chat" | "alpaca"


SOURCES: dict[str, Source] = {
    "fineweb": Source("fineweb", "HuggingFaceFW/fineweb-2", "fra_Latn", "train", "text"),
    "wiki": Source("wiki", "wikimedia/wikipedia", "20231101.fr", "train", "text"),
    "chat": Source("chat", "angeluriot/french_instruct", None, "train", "chat"),
    "alpaca": Source("alpaca", "jpacifico/French-Alpaca-dataset-Instruct-110K", None, "train", "alpaca"),
    # dolphin-r1 traduit en français : réponses avec trace de raisonnement complète.
    # Converti au format <think>...</think> de Qwen3 pour le mode "thinking".
    "reasoning": Source("reasoning", "WiroAI/dolphin-r1-french", None, "train", "dolphin_think"),
}

# Budgets de téléchargement (en caractères) des sources SFT hors mix de pré-entraînement.
SFT_BUDGETS = {"alpaca": 40_000_000, "reasoning": 90_000_000}
# Un exemple de raisonnement plus long que ça ne rentrera jamais dans le contexte : on
# le jette au téléchargement plutôt que de gaspiller le budget (~3,5 car/token).
MAX_REASONING_CHARS = 3600

# Recette par défaut du pré-entraînement (proportion du budget de caractères).
# On met déjà 20% de chat DANS le pré-entraînement : sur un tout petit modèle, voir le
# format ChatML dès le début fait une énorme différence sur la capacité à dialoguer.
DEFAULT_MIX = {"fineweb": 0.55, "wiki": 0.25, "chat": 0.20}


def render_chat(messages: list[dict]) -> str:
    """Rend une conversation au format ChatML."""
    out = []
    for m in messages:
        role = m["role"]
        content = (m.get("text") or m.get("content") or "").strip()
        if not content:
            continue
        out.append(f"{IM_START}{role}\n{content}{IM_END}\n")
    return "".join(out)


def chat_segments(messages: list[dict]) -> list[tuple[str, bool]]:
    """Découpe une conversation en (texte, on_apprend_dessus).

    On n'entraîne QUE sur les réponses de l'assistant : apprendre à prédire les
    questions de l'utilisateur gaspillerait de la capacité et rendrait le modèle
    bavard à la place de l'user.
    """
    segs: list[tuple[str, bool]] = []
    for m in messages:
        role = m["role"]
        content = (m.get("text") or m.get("content") or "").strip()
        if not content:
            continue
        segs.append((f"{IM_START}{role}\n", False))
        if role == "assistant":
            segs.append((f"{content}{IM_END}\n", True))
        else:
            segs.append((f"{content}{IM_END}\n", False))
    return segs


def _iter_source(src: Source, seed: int = 0):
    """Générateur de documents. Chaque élément : (texte, messages|None)."""
    from datasets import load_dataset

    kw = dict(split=src.split, streaming=True)
    if src.config:
        kw["name"] = src.config
    ds = load_dataset(src.repo, **kw)
    ds = ds.shuffle(seed=seed, buffer_size=10_000)

    for row in ds:
        if src.kind == "text":
            t = (row.get("text") or "").strip()
            if len(t) < 200:          # on jette les documents trop courts (souvent du bruit)
                continue
            yield t, None
        elif src.kind == "chat":
            conv = row.get("conversation") or []
            msgs = [{"role": m["role"], "text": m.get("text", "")} for m in conv]
            if len(msgs) < 2:
                continue
            yield render_chat(msgs), msgs
        elif src.kind == "alpaca":
            instr = (row.get("instruction") or "").strip()
            inp = (row.get("input") or "").strip()
            out = (row.get("output") or "").strip()
            if not instr or not out:
                continue
            user = f"{instr}\n\n{inp}" if inp else instr
            msgs = [{"role": "user", "text": user}, {"role": "assistant", "text": out}]
            yield render_chat(msgs), msgs
        elif src.kind == "dolphin_think":
            msgs = _convert_dolphin(row.get("messages") or [])
            if msgs is None:
                continue
            text = render_chat(msgs)
            if len(text) > MAX_REASONING_CHARS:
                continue
            yield text, msgs


def _convert_dolphin(messages: list[dict]) -> list[dict] | None:
    """dolphin-r1-french -> format <think>. Les réponses contiennent
    <|begin_of_thought|>...<|end_of_thought|> puis <|begin_of_solution|>...<|end_of_solution|>."""
    out = []
    for m in messages:
        role, content = m.get("role"), (m.get("content") or "").strip()
        if role == "user":
            out.append({"role": "user", "text": content})
        elif role == "assistant":
            def between(a, b):
                i, j = content.find(a), content.find(b)
                return content[i + len(a):j].strip() if 0 <= i < j else None
            thought = between("<|begin_of_thought|>", "<|end_of_thought|>")
            sol = between("<|begin_of_solution|>", "<|end_of_solution|>")
            if not sol:
                return None
            text = f"{THINK}\n{thought}\n{THINK_END}\n{sol}" if thought else sol
            out.append({"role": "assistant", "text": text})
    return out if len(out) >= 2 else None


# --------------------------------------------------------------------------------------
# Étape 1 : téléchargement -> jsonl brut
# --------------------------------------------------------------------------------------
def download_source(src_name: str, char_budget: int, out_path: Path, seed: int = 0) -> dict:
    from tqdm import tqdm

    src = SOURCES[src_name]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    n_docs, n_chars = 0, 0
    t0 = time.time()

    with out_path.open("w", encoding="utf-8") as f, tqdm(
        total=char_budget, unit="c", unit_scale=True, desc=f"  {src_name:8s}", ncols=90
    ) as bar:
        for text, msgs in _iter_source(src, seed=seed):
            rec = {"t": text}
            if msgs is not None:
                rec["m"] = msgs
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            n_docs += 1
            n_chars += len(text)
            bar.update(len(text))
            if n_chars >= char_budget:
                break

    return {"source": src_name, "docs": n_docs, "chars": n_chars, "seconds": round(time.time() - t0, 1)}


def iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


# --------------------------------------------------------------------------------------
# Étape 2 : tokenizer BPE
# --------------------------------------------------------------------------------------
def train_tokenizer(jsonl_paths: list[Path], vocab_size: int, out_file: Path, sample_chars: int = 400_000_000):
    from tokenizers import Tokenizer, decoders, models, pre_tokenizers, processors, trainers

    tok = Tokenizer(models.BPE(unk_token=None))
    # ByteLevel = aucun token <unk> possible, tout octet est représentable.
    tok.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=False)
    tok.decoder = decoders.ByteLevel()
    tok.post_processor = processors.ByteLevel(trim_offsets=False)

    trainer = trainers.BpeTrainer(
        vocab_size=vocab_size,
        special_tokens=SPECIALS,
        min_frequency=2,
        show_progress=True,
        initial_alphabet=pre_tokenizers.ByteLevel.alphabet(),
    )

    def corpus_iter():
        seen = 0
        for p in jsonl_paths:
            for rec in iter_jsonl(p):
                t = rec["t"]
                seen += len(t)
                yield t
                if seen >= sample_chars:
                    return

    tok.train_from_iterator(corpus_iter(), trainer=trainer)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    tok.save(str(out_file))
    return tok


def load_tokenizer(path: str | Path):
    from tokenizers import Tokenizer

    return Tokenizer.from_file(str(path))


def special_ids(tok) -> dict:
    return {
        "eot": tok.token_to_id(EOT),
        "im_start": tok.token_to_id(IM_START),
        "im_end": tok.token_to_id(IM_END),
    }


# --------------------------------------------------------------------------------------
# Étape 3 : binarisation (texte -> tableau plat d'uint16 sur disque)
# --------------------------------------------------------------------------------------
class BinWriter:
    """Écrit un flux de tokens (et optionnellement un masque de loss) en binaire brut."""

    def __init__(self, bin_path: Path, with_mask: bool = False):
        bin_path.parent.mkdir(parents=True, exist_ok=True)
        self.f = bin_path.open("wb")
        self.fm = bin_path.with_suffix(".mask").open("wb") if with_mask else None
        self.n = 0

    def write(self, ids: list[int] | np.ndarray, mask: list[int] | np.ndarray | None = None):
        arr = np.asarray(ids, dtype=DTYPE)
        self.f.write(arr.tobytes())
        if self.fm is not None:
            m = np.asarray(mask if mask is not None else np.ones(len(arr)), dtype=np.uint8)
            self.fm.write(m.tobytes())
        self.n += len(arr)

    def close(self):
        self.f.close()
        if self.fm is not None:
            self.fm.close()


def encode_pretrain(tok, jsonl_paths: list[Path], out_dir: Path, val_frac: float = 0.005,
                    batch: int = 1000, min_val_tokens: int = 32768):
    """Tokenise le corpus de pré-entraînement. Documents séparés par <|endoftext|>."""
    from tqdm import tqdm

    eot = tok.token_to_id(EOT)
    train_w = BinWriter(out_dir / "train.bin")
    val_w = BinWriter(out_dir / "val.bin")
    n_chars = 0

    buf: list[str] = []
    rng = random.Random(1234)

    def flush():
        nonlocal buf
        if not buf:
            return
        for enc in tok.encode_batch(buf):
            ids = enc.ids + [eot]
            # plancher sur la validation : sinon un petit corpus peut produire un
            # val.bin vide et le chargeur ne peut plus former de batch
            to_val = val_w.n < min_val_tokens or rng.random() < val_frac
            (val_w if to_val else train_w).write(ids)
        buf = []

    for p in jsonl_paths:
        for rec in tqdm(iter_jsonl(p), desc=f"  tokenize {p.stem:10s}", unit="doc", ncols=90):
            buf.append(rec["t"])
            n_chars += len(rec["t"])
            if len(buf) >= batch:
                flush()
    flush()

    n_train, n_val = train_w.n, val_w.n
    train_w.close()
    val_w.close()
    return {"train_tokens": n_train, "val_tokens": n_val, "chars": n_chars,
            "chars_per_token": round(n_chars / max(1, n_train + n_val), 3)}


def encode_sft(tok, jsonl_paths: list[Path], out_dir: Path, val_frac: float = 0.01,
               max_len: int = 1024, min_val_tokens: int = 8192):
    """Tokenise les conversations avec un masque de loss (1 = réponse assistant)."""
    from tqdm import tqdm

    eot = tok.token_to_id(EOT)
    train_w = BinWriter(out_dir / "sft_train.bin", with_mask=True)
    val_w = BinWriter(out_dir / "sft_val.bin", with_mask=True)
    rng = random.Random(4321)
    n_conv, n_sup = 0, 0

    for p in jsonl_paths:
        for rec in tqdm(iter_jsonl(p), desc=f"  sft {p.stem:14s}", unit="conv", ncols=90):
            msgs = rec.get("m")
            if not msgs:
                continue
            ids: list[int] = []
            mask: list[int] = []
            for text, learn in chat_segments(msgs):
                enc = tok.encode(text).ids
                ids += enc
                mask += [1 if learn else 0] * len(enc)
            if len(ids) > max_len or sum(mask) == 0:
                continue
            ids.append(eot)
            mask.append(0)
            to_val = val_w.n < min_val_tokens or rng.random() < val_frac
            (val_w if to_val else train_w).write(ids, mask)
            n_conv += 1
            n_sup += sum(mask)

    out = {"conversations": n_conv, "train_tokens": train_w.n, "val_tokens": val_w.n,
           "supervised_tokens": n_sup}
    train_w.close()
    val_w.close()
    return out


# --------------------------------------------------------------------------------------
# Étape 4 : chargeur de batchs
# --------------------------------------------------------------------------------------
class BinCorpus:
    """Corpus tokenisé en mémoire virtuelle (np.memmap) + échantillonnage déterministe.

    Déterministe = le batch du step N ne dépend QUE de (seed, N). Donc reprendre un
    entraînement au step N redonne exactement la même suite de batchs : pas de
    doublon, pas de trou, sans avoir à sauvegarder l'état du dataloader.
    """

    def __init__(self, bin_path: str | Path, seq_len: int, with_mask: bool = False):
        self.path = Path(bin_path)
        self.tokens = np.memmap(self.path, dtype=DTYPE, mode="r")
        self.mask = None
        mask_path = self.path.with_suffix(".mask")
        if with_mask and mask_path.exists():
            self.mask = np.memmap(mask_path, dtype=np.uint8, mode="r")
        self.seq_len = seq_len
        self.n_tokens = len(self.tokens)
        if self.n_tokens < seq_len + 1:
            raise ValueError(f"{bin_path} ne contient que {self.n_tokens} tokens (< seq_len+1)")

    def __len__(self):
        return self.n_tokens

    def get_batch(self, step: int, batch_size: int, seed: int = 1337, device: str = "cuda"):
        import torch

        rng = np.random.default_rng(seed * 1_000_003 + step)
        hi = self.n_tokens - self.seq_len - 1
        offsets = rng.integers(0, hi, size=batch_size)

        x = np.stack([self.tokens[o: o + self.seq_len] for o in offsets]).astype(np.int64)
        y = np.stack([self.tokens[o + 1: o + 1 + self.seq_len] for o in offsets]).astype(np.int64)
        xt = torch.from_numpy(x)
        yt = torch.from_numpy(y)
        mt = None
        if self.mask is not None:
            m = np.stack([self.mask[o + 1: o + 1 + self.seq_len] for o in offsets]).astype(np.uint8)
            mt = torch.from_numpy(m)

        if device.startswith("cuda"):
            xt = xt.pin_memory().to(device, non_blocking=True)
            yt = yt.pin_memory().to(device, non_blocking=True)
            if mt is not None:
                mt = mt.pin_memory().to(device, non_blocking=True)
        else:
            xt, yt = xt.to(device), yt.to(device)
            if mt is not None:
                mt = mt.to(device)
        return xt, yt, mt


# --------------------------------------------------------------------------------------
# Orchestration : la commande `prepare`
# --------------------------------------------------------------------------------------
def prepare_all(data_dir: Path, target_tokens: int, vocab_size: int, mix: dict[str, float],
                sft: bool = True, chars_per_token: float = 3.6, max_seq_len: int = 1024,
                skip_download: bool = False, seed: int = 0) -> dict:
    data_dir = Path(data_dir)
    raw_dir = data_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    report: dict = {"target_tokens": target_tokens, "vocab_size": vocab_size, "mix": mix}

    char_budget = int(target_tokens * chars_per_token)
    print(f"\n[1/4] Téléchargement (~{char_budget/1e9:.2f} G caractères visés pour ~{target_tokens/1e6:.0f}M tokens)")
    paths = []
    dl = []
    for name, w in mix.items():
        p = raw_dir / f"{name}.jsonl"
        budget = int(char_budget * w)
        if skip_download and p.exists():
            print(f"  {name:8s} : déjà là ({p.stat().st_size/1e6:.0f} Mo), on garde")
        else:
            dl.append(download_source(name, budget, p, seed=seed))
        paths.append(p)
    report["download"] = dl

    print(f"\n[2/4] Entraînement du tokenizer BPE ({vocab_size} tokens)")
    tok_path = data_dir / "tokenizer.json"
    tok = train_tokenizer(paths, vocab_size, tok_path)
    report["tokenizer"] = {"path": str(tok_path), "vocab_size": tok.get_vocab_size(), **special_ids(tok)}

    print("\n[3/4] Binarisation du pré-entraînement")
    report["pretrain"] = encode_pretrain(tok, paths, data_dir)

    if sft:
        print("\n[4/4] Sources de dialogue + raisonnement, binarisation avec masque de loss")
        for name, budget in SFT_BUDGETS.items():
            p = raw_dir / f"{name}.jsonl"
            if name in mix:
                continue                     # déjà téléchargé pour le pré-entraînement
            if skip_download and p.exists():
                print(f"  {name:9s} : déjà là ({p.stat().st_size/1e6:.0f} Mo), on garde")
            else:
                report.setdefault("download_sft", []).append(download_source(name, budget, p, seed=seed))
        chat_paths = [raw_dir / f"{n}.jsonl" for n in ("chat", "alpaca", "reasoning")
                      if (raw_dir / f"{n}.jsonl").exists()]
        if not chat_paths:
            print("  (aucune source de dialogue téléchargée — SFT ignoré)")
        else:
            report["sft"] = encode_sft(tok, chat_paths, data_dir, max_len=max_seq_len)
    (data_dir / "meta.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report
