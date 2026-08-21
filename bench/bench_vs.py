# --------------------------------------------------------------------------------------
# Benchmark : notre modele contre des GPT-2 francais publics (~124M).
#
# Adapte de la version d'origine pour une arborescence plate (run.py, model.py, data.py
# a la racine) et pour Apple Silicon / MPS.
#
# Trois epreuves, concues pour rester equitables malgre des tokenizers differents :
#   1. bpb    — bits par OCTET sur du texte francais tenu a l'ecart. C'est la seule
#               facon honnete de comparer des loss entre tokenizers differents.
#   2. calcul — exact-match sur des problemes arithmetiques generes avec une seed
#               dediee. Notre modele joue en format chat, les modeles de base en
#               few-shot 3 exemples (leur meilleur protocole).
#   3. faits  — completions factuelles en continuation brute, notees par regex.
#
# Usage :
#   python bench_vs.py --run gpu1                     # tout
#   python bench_vs.py --run gpu1 --n-problems 30     # plus court
#   python bench_vs.py --run gpu1 --skip-hf           # sans telechargement HF
#
# Prerequis pour les concurrents : pip install transformers
# Le texte d'evaluation est lu depuis eval_text.txt (voir extract_eval_text sur Modal).
# --------------------------------------------------------------------------------------
from __future__ import annotations

import argparse
import json
import math
import random
import re
import sys
import time
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import data as D  # noqa: E402
from model import ModelConfig, build_model  # noqa: E402

CONCURRENTS = [
    ("asi/gpt-fr-cased-small", "GPT-fr small · 124M (Inria)"),
    ("antoinelouis/belgpt2", "BelGPT-2 · 124M (60 Go)"),
    ("dbddv01/gpt2-french-small", "GPT-2 fr · 124M (transfert)"),
]

FAITS = [
    ("La capitale de la France est", r"\bParis\b"),
    ("La capitale de l'Italie est", r"\bRome\b"),
    ("L'eau bout à une température de", r"100"),
    ("Une semaine compte", r"sept|7"),
    ("Le contraire de grand est", r"\bpetit"),
    ("Les abeilles produisent du", r"\bmiel\b"),
    ("La Seine traverse la ville de", r"\bParis|\bRouen"),
    ("Un triangle possède", r"trois|3"),
]

FEWSHOT = (
    "Question : Calcule : 12 + 7\nRéponse : 19\n\n"
    "Question : On partage 20 billes équitablement entre 4 enfants. "
    "Combien chaque enfant en reçoit-il ?\nRéponse : 5\n\n"
    "Question : Un cahier coûte 3 euros. Combien coûtent 5 cahiers ?\nRéponse : 15\n\n"
)


# --------------------------------------------------------------------------------------
def pick_device(pref: str = "auto") -> str:
    if pref != "auto":
        return pref
    if torch.cuda.is_available():
        return "cuda"
    if getattr(torch.backends, "mps", None) is not None and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def dernier_nombre(txt: str) -> str | None:
    """Dernier nombre du texte, tolerant aux espaces de groupement ('1 000')."""
    hits = re.findall(r"\d(?:[\d ]*\d)?", txt)
    if not hits:
        return None
    return hits[-1].replace(" ", "")


def problemes_eval(n: int, seed: int) -> list[dict]:
    """Problemes arithmetiques a reponse numerique, generes avec une seed dediee.

    Remplace le module synth.py de la version d'origine, absent de ce depot.
    """
    rng = random.Random(seed)
    gabarits = [
        lambda: (f"Calcule : {(a := rng.randint(10, 99))} + {(b := rng.randint(10, 99))}",
                 a + b),
        lambda: (f"Calcule : {(a := rng.randint(50, 99))} - {(b := rng.randint(2, 49))}",
                 a - b),
        lambda: (f"Calcule : {(a := rng.randint(2, 12))} × {(b := rng.randint(2, 12))}",
                 a * b),
        lambda: (f"On partage {(b := rng.randint(2, 9)) * (q := rng.randint(2, 12))} "
                 f"billes équitablement entre {b} enfants. "
                 f"Combien chaque enfant en reçoit-il ?", q),
        lambda: (f"Un cahier coûte {(p := rng.randint(2, 9))} euros. "
                 f"Combien coûtent {(n2 := rng.randint(2, 9))} cahiers ?", p * n2),
        lambda: (f"J'ai {(a := rng.randint(20, 80))} bonbons, j'en mange "
                 f"{(b := rng.randint(3, 19))}. Combien m'en reste-t-il ?", a - b),
        lambda: (f"Le double de {(a := rng.randint(10, 60))} ?", 2 * a),
        lambda: (f"La moitié de {(a := rng.randint(5, 50)) * 2} ?", a),
    ]
    out = []
    while len(out) < n:
        q, rep = rng.choice(gabarits)()
        out.append({"q": q, "attendu": str(rep)})
    return out


def lire_texte_eval(eval_file: Path, data_dir: Path, n_chars: int) -> str:
    """Texte francais tenu a l'ecart de l'entrainement.

    Priorite au fichier eval_text.txt (produit par extract_eval_text sur Modal).
    A defaut, on retombe sur la queue des .jsonl bruts s'ils sont en local.
    """
    if eval_file.exists():
        texte = eval_file.read_text(encoding="utf-8", errors="ignore")
        if len(texte) >= 50_000:
            return texte[:n_chars]
        print(f"[!] {eval_file.name} trop court ({len(texte)} chars)")

    morceaux = []
    for name in ("wiki", "fineweb"):
        p = data_dir / "raw" / f"{name}.jsonl"
        if not p.exists():
            continue
        size = p.stat().st_size
        with p.open("rb") as f:
            f.seek(max(0, size - 8_000_000))
            brut = f.read().decode("utf-8", errors="ignore")
        lignes = brut.split("\n")[1:]
        acc, budget = [], n_chars // 2
        for ligne in reversed(lignes):
            ligne = ligne.strip()
            if not ligne:
                continue
            try:
                doc = json.loads(ligne)
            except json.JSONDecodeError:
                continue
            txt = doc.get("t") or doc.get("text") or next(
                (v for v in doc.values() if isinstance(v, str)), "")
            if txt:
                acc.append(txt)
                budget -= len(txt)
                if budget <= 0:
                    break
        morceaux.extend(reversed(acc))

    texte = "\n\n".join(morceaux)
    if len(texte) < 50_000:
        sys.exit(
            f"[!] Texte d'evaluation introuvable.\n"
            f"    Attendu : {eval_file}\n"
            f"    Produis-le avec :  modal run modal_train.py::extract_eval_text\n"
            f"    puis :  modal volume get llm-data eval_text.txt ./eval_text.txt")
    return texte[:n_chars]


# --------------------------------------------------------------------------------------
class NotreModele:
    def __init__(self, run_dir: Path, data_dir: Path, device: str):
        ckpt = None
        for phase in ("sft", "mid", "pretrain"):
            for name in ("ckpt_best.pt", "ckpt_latest.pt"):
                p = run_dir / phase / name
                if p.exists():
                    ckpt = p
                    break
            if ckpt:
                break
        assert ckpt, f"aucun checkpoint sous {run_dir}"

        ck = torch.load(ckpt, map_location=device, weights_only=False)
        mcfg = ModelConfig.from_dict(ck["model_cfg"])
        self.model = build_model(mcfg).to(device)
        self.model.load_state_dict(ck["model"])
        self.model.eval()

        # le tokenizer vit a cote du run (copie au demarrage de l'entrainement),
        # avec repli sur data/ pour les depots ou il n'a pas ete copie
        tok_path = run_dir / "tokenizer.json"
        if not tok_path.exists():
            tok_path = data_dir / "tokenizer.json"
        assert tok_path.exists(), f"tokenizer introuvable ({run_dir}, {data_dir})"
        self.tok = D.load_tokenizer(tok_path)
        self.sp = D.special_ids(self.tok)

        self.device = device
        self.phase = ckpt.parent.name
        n = sum(p.numel() for p in self.model.parameters())
        self.nom = f"le notre · {n/1e6:.0f}M ({self.phase}, step {ck.get('step', '?')})"
        print(f"[i] modele charge : {ckpt}  (phase {self.phase}, tokenizer {tok_path.name})")

    @torch.no_grad()
    def bpb(self, texte: str):
        ids = self.tok.encode(texte).ids
        nll, n_pred = 0.0, 0
        T = self.model.cfg.max_seq_len
        for i in range(0, len(ids) - 1, T):
            fen = ids[i:i + T + 1]
            if len(fen) < 2:
                break
            x = torch.tensor([fen[:-1]], device=self.device)
            y = torch.tensor([fen[1:]], device=self.device)
            m = torch.ones_like(y, dtype=torch.float32)
            _, loss, _ = self.model(x, y, m, z_loss=0.0, diagnostics=False)
            nll += loss.item() * (len(fen) - 1)
            n_pred += len(fen) - 1
        octets = len(texte.encode("utf-8"))
        return nll / math.log(2) / octets, n_pred

    @torch.no_grad()
    def repondre(self, question: str, max_new: int = 220) -> str:
        if self.phase in ("sft", "mid"):
            texte = f"{D.IM_START}user\n{question}{D.IM_END}\n{D.IM_START}assistant\n"
        else:
            texte = FEWSHOT + f"Question : {question}\nRéponse :"
        ids = torch.tensor([self.tok.encode(texte).ids], device=self.device)
        out = self.model.generate(ids, max_new_tokens=max_new, temperature=0.0,
                                  repetition_penalty=1.0,
                                  stop_ids=(self.sp["im_end"], self.sp["eot"]))
        gen = self.tok.decode(out[0, ids.shape[1]:].tolist(), skip_special_tokens=False)
        gen = gen.split("</think>")[-1]          # on ne note que la reponse finale
        return gen.split("<|im_end|>")[0]

    @torch.no_grad()
    def completer(self, amorce: str, max_new: int = 30) -> str:
        ids = torch.tensor([self.tok.encode(amorce).ids], device=self.device)
        out = self.model.generate(ids, max_new_tokens=max_new, temperature=0.0,
                                  repetition_penalty=1.0, stop_ids=(self.sp["eot"],))
        return self.tok.decode(out[0, ids.shape[1]:].tolist(), skip_special_tokens=True)


# --------------------------------------------------------------------------------------
class ModeleHF:
    def __init__(self, repo: str, nom: str, device: str):
        from transformers import AutoModelForCausalLM, AutoTokenizer

        print(f"[i] chargement {repo}…")
        self.tok = AutoTokenizer.from_pretrained(repo)
        self.model = AutoModelForCausalLM.from_pretrained(repo).to(device).eval()
        self.device = device
        self.nom = nom
        self.ctx = min(getattr(self.model.config, "n_positions", 1024), 1024)

    @torch.no_grad()
    def bpb(self, texte: str):
        ids = self.tok(texte, return_tensors="pt").input_ids[0]
        nll, n_pred = 0.0, 0
        # fenetre de ctx tokens MAX : les GPT-2 ont des embeddings de position appris
        # (1024 pile), une fenetre de ctx+1 fait deborder la table
        T = self.ctx - 1
        for i in range(0, len(ids) - 1, T):
            fen = ids[i:i + T + 1].unsqueeze(0).to(self.device)
            if fen.shape[1] < 2:
                break
            out = self.model(fen, labels=fen)
            nll += out.loss.item() * (fen.shape[1] - 1)
            n_pred += fen.shape[1] - 1
        octets = len(texte.encode("utf-8"))
        return nll / math.log(2) / octets, n_pred

    @torch.no_grad()
    def _greedy(self, prompt: str, max_new: int) -> str:
        enc = self.tok(prompt, return_tensors="pt").to(self.device)
        out = self.model.generate(**enc, max_new_tokens=max_new, do_sample=False,
                                  pad_token_id=self.tok.eos_token_id
                                  or self.tok.pad_token_id or 0)
        return self.tok.decode(out[0, enc.input_ids.shape[1]:], skip_special_tokens=True)

    def repondre(self, question: str, max_new: int = 60) -> str:
        gen = self._greedy(FEWSHOT + f"Question : {question}\nRéponse :", max_new)
        return gen.split("Question")[0]

    def completer(self, amorce: str, max_new: int = 30) -> str:
        return self._greedy(amorce, max_new)


# --------------------------------------------------------------------------------------
def charger_modeles(args, device: str) -> list:
    modeles = [NotreModele(ROOT / "runs" / args.run, ROOT / args.data_dir, device)]
    if args.skip_hf:
        return modeles
    hf_device = args.hf_device if args.hf_device != "auto" else (
        "cpu" if device == "mps" else device)
    try:
        for repo, nom in CONCURRENTS:
            try:
                modeles.append(ModeleHF(repo, nom, hf_device))
            except Exception as e:
                print(f"[!] {repo} indisponible ({e}) — ignore.")
    except ImportError:
        print("[!] transformers absent : pip install transformers")
    return modeles


def liberer(m):
    if not isinstance(m, NotreModele):
        del m.model
        if torch.cuda.is_available():
            torch.cuda.empty_cache()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="gpu1")
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--eval-file", default="eval_text.txt")
    ap.add_argument("--n-problems", type=int, default=100)
    ap.add_argument("--eval-chars", type=int, default=300_000)
    ap.add_argument("--seed", type=int, default=4242)
    ap.add_argument("--skip-hf", action="store_true")
    ap.add_argument("--device", default="auto", choices=["auto", "cuda", "mps", "cpu"])
    ap.add_argument("--hf-device", default="auto", choices=["auto", "cuda", "mps", "cpu"],
                    help="les GPT-2 HF sont plus stables sur cpu quand on est sur mps")
    args = ap.parse_args()

    device = pick_device(args.device)
    print(f"[i] device : {device}")

    modeles = charger_modeles(args, device)
    texte = lire_texte_eval(ROOT / args.eval_file, ROOT / args.data_dir, args.eval_chars)
    problemes = problemes_eval(args.n_problems, args.seed)
    print(f"[i] epreuves : bpb sur {len(texte):,} chars · "
          f"{len(problemes)} problemes (seed {args.seed}) · {len(FAITS)} faits\n")

    lignes, details = [], []
    for m in modeles:
        t0 = time.time()
        bpb, _ = m.bpb(texte)

        ok_calc = 0
        for p in problemes:
            try:
                brut = m.repondre(p["q"])
            except Exception as e:
                brut = f"<erreur : {e}>"
            rep = dernier_nombre(brut)
            bon = rep == p["attendu"]
            ok_calc += bon
            details.append((m.nom, "calc", p["q"], p["attendu"],
                            f"{rep!r} · texte : {brut.strip()[:200]}", bon))

        ok_faits = 0
        for amorce, motif in FAITS:
            try:
                gen = m.completer(amorce)
            except Exception:
                gen = ""
            bon = re.search(motif, gen, re.IGNORECASE) is not None
            ok_faits += bon
            details.append((m.nom, "fait", amorce, motif, gen.strip()[:80], bon))

        lignes.append((m.nom, bpb, ok_calc / len(problemes), ok_faits / len(FAITS)))
        print(f"{m.nom:<42} bpb {bpb:.4f} · calcul {ok_calc}/{len(problemes)} · "
              f"faits {ok_faits}/{len(FAITS)}  ({time.time()-t0:.0f}s)")
        liberer(m)

    rap_dir = ROOT / "bench_reports"
    rap_dir.mkdir(parents=True, exist_ok=True)
    rap = rap_dir / f"bench_vs_{args.run}.md"
    with rap.open("w", encoding="utf-8") as f:
        f.write("# Notre modele contre les GPT-2 francais publics\n\n")
        f.write(f"bpb sur {len(texte):,} chars tenus a l'ecart · "
                f"{len(problemes)} problemes seed {args.seed} · greedy partout\n\n")
        f.write("| modele | bpb ↓ | calcul ↑ | faits ↑ |\n|---|---|---|---|\n")
        for nom, bpb, calc, faits in lignes:
            f.write(f"| {nom} | {bpb:.4f} | {calc:.0%} | {faits:.0%} |\n")
        f.write("\n## Details\n\n")
        for nom, ep, q, attendu, obtenu, bon in details:
            f.write(f"- {'✅' if bon else '❌'} `{ep}` **{nom}** — {q!r} → "
                    f"attendu {attendu!r}, obtenu {obtenu!r}\n")
    print(f"\n[i] rapport detaille : {rap}")


if __name__ == "__main__":
    main()