"""Genere un corpus SFT cible sur les faiblesses mesurees au benchmark OOD.

Le modele RAISONNE bien mais CALCULE mal : il sait qu'il faut additionner
(« Emma a 7 ans, son frere 3 de plus » -> il repond 12 au lieu de 10) mais rate
l'arithmetique. Deux remedes ici :

  maths    — couverture SYSTEMATIQUE des operations a deux chiffres plutot qu'un
             echantillon aleatoire. Le modele reussit 7x11 et rate 88+59 : signe
             qu'il memorise des cas vus et interpole mal. Chaque <think> decompose
             l'operation (88+59 -> 80+50=130, 8+9=17, 130+17=147) pour transformer
             un calcul dur en calculs faciles.
  consigne — comptage et format de sortie (« donne-moi trois X, une par ligne »),
             l'autre echec net du benchmark.

Sortie au format de distill.jsonl : {"t", "m", "k"}, compatible encode_sft.

Usage : python gen_math.py math.jsonl [n_max]
"""
import json
import random
import sys
from pathlib import Path

out_path = Path(sys.argv[1] if len(sys.argv) > 1 else "math.jsonl")
n_max = int(sys.argv[2]) if len(sys.argv) > 2 else 120_000
rng = random.Random(7)

exemples = []


def ajoute(question: str, pensee: str, reponse: str, kind: str):
    assistant = f"<think>\n{pensee}\n</think>\n{reponse}"
    exemples.append({
        "t": question + assistant,
        "m": [{"role": "user", "text": question},
              {"role": "assistant", "text": assistant}],
        "k": kind,
    })


# --------------------------------------------------------------------------------------
# 1. Addition : decomposition dizaines + unites
# --------------------------------------------------------------------------------------
FORMULES_ADD = [
    "Calcule : {a} + {b}",
    "Additionne {a} et {b}.",
    "Combien font {a} plus {b} ?",
    "{b} de plus que {a}, ça fait combien ?",
    "Quel est le résultat de {a} + {b} ?",
]

for a in range(10, 100):
    for b in range(10, 100):
        da, ua = divmod(a, 10)
        db, ub = divmod(b, 10)
        dizaines, unites = da * 10 + db * 10, ua + ub
        pensee = (f"{a} + {b}.\n"
                  f"Dizaines : {da*10} + {db*10} = {dizaines}.\n"
                  f"Unités : {ua} + {ub} = {unites}.\n"
                  f"Total : {dizaines} + {unites} = {a + b}.")
        q = rng.choice(FORMULES_ADD).format(a=a, b=b)
        ajoute(q, pensee, str(a + b), "maths")

# --------------------------------------------------------------------------------------
# 2. Soustraction, retenue explicitee
# --------------------------------------------------------------------------------------
FORMULES_SUB = [
    "Calcule : {a} - {b}",
    "Retire {b} de {a}.",
    "Quelle est la différence entre {a} et {b} ?",
    "Quel est le résultat de {a} moins {b} ?",
    "{a} moins {b} ?",
]

for a in range(10, 100):
    for b in range(1, a + 1):
        if rng.random() > 0.45:          # on echantillonne, sinon ~4400 cas
            continue
        da, ua = divmod(a, 10)
        db, ub = divmod(b, 10)
        if ua >= ub:
            pensee = (f"{a} - {b}.\n"
                      f"Dizaines : {da*10} - {db*10} = {da*10 - db*10}.\n"
                      f"Unités : {ua} - {ub} = {ua - ub}.\n"
                      f"Total : {a - b}.")
        else:
            inter = a - ub
            pensee = (f"{a} - {b}.\n"
                      f"On retire d'abord les unités : {a} - {ub} = {inter}.\n"
                      f"Puis les dizaines : {inter} - {db*10} = {a - b}.")
        q = rng.choice(FORMULES_SUB).format(a=a, b=b)
        ajoute(q, pensee, str(a - b), "maths")

# --------------------------------------------------------------------------------------
# 3. Tables de multiplication jusqu'a 20, addition repetee
# --------------------------------------------------------------------------------------
FORMULES_MUL = [
    "Calcule : {a} × {b}",
    "Combien font {a} fois {b} ?",
    "Quel est le produit de {a} et {b} ?",
]

for a in range(2, 21):
    for b in range(2, 21):
        if b <= 5:
            somme = " + ".join([str(a)] * b)
            pensee = f"{a} × {b} = {somme} = {a * b}."
        else:
            pensee = (f"{a} × {b}.\n"
                      f"{a} × 10 = {a * 10}, donc {a} × {b} = "
                      f"{a * 10} {'-' if b < 10 else '+'} {a * abs(b - 10)} = {a * b}.")
        q = rng.choice(FORMULES_MUL).format(a=a, b=b)
        ajoute(q, pensee, str(a * b), "maths")

# --------------------------------------------------------------------------------------
# 4. Division exacte et partage
# --------------------------------------------------------------------------------------
for q_ in range(2, 21):
    for d in range(2, 13):
        n = q_ * d
        pensee = f"{n} divisé par {d}.\n{d} × {q_} = {n}, donc {n} / {d} = {q_}."
        gab = rng.choice([
            (f"On partage {n} billes équitablement entre {d} enfants. "
             f"Combien chaque enfant en reçoit-il ?", f"Chaque enfant reçoit {q_} billes."),
            (f"Calcule : {n} / {d}", str(q_)),
            (f"Combien de fois {d} dans {n} ?", str(q_)),
            (f"Il me faut {n} œufs. Les boîtes contiennent {d} œufs chacune. "
             f"Combien de boîtes dois-je acheter ?", f"Il faut acheter {q_} boîtes."),
        ])
        ajoute(gab[0], pensee, gab[1], "maths")

# --------------------------------------------------------------------------------------
# 5. Double et moitie (echec net : « la moitie de 90 » -> 30)
# --------------------------------------------------------------------------------------
for a in range(2, 100):
    ajoute(f"Le double de {a} ?", f"Le double, c'est × 2.\n{a} × 2 = {a * 2}.",
           str(a * 2), "maths")
    if a % 2 == 0:
        ajoute(f"La moitié de {a} ?", f"La moitié, c'est / 2.\n{a} / 2 = {a // 2}.",
               str(a // 2), "maths")

# --------------------------------------------------------------------------------------
# 6. Problemes en contexte : le raisonnement est bon, on ancre le calcul
# --------------------------------------------------------------------------------------
PRENOMS = ["Emma", "Leo", "Nina", "Tom", "Jade", "Hugo", "Lina", "Marius", "Zoe", "Ali"]
OBJETS = ["billes", "pommes", "stickers", "bonbons", "pages", "cartes", "timbres"]

for _ in range(12_000):
    p, o = rng.choice(PRENOMS), rng.choice(OBJETS)
    kind = rng.choice(["reste", "total", "age", "prix", "cadence"])
    if kind == "reste":
        a, b = rng.randint(20, 99), rng.randint(3, 19)
        ajoute(f"{p} a {a} {o}. {p} en donne {b}. Combien lui en reste-t-il ?",
               f"{a} - {b} = {a - b}.", f"Il lui reste {a - b} {o}.", "maths")
    elif kind == "total":
        a, b = rng.randint(10, 60), rng.randint(10, 60)
        ajoute(f"J'ai {a} {o} rouges et {b} {o} vertes. Combien de {o} en tout ?",
               f"{a} + {b} = {a + b}.", f"Il y a {a + b} {o} en tout.", "maths")
    elif kind == "age":
        a, d = rng.randint(5, 40), rng.randint(2, 15)
        ajoute(f"{p} a {a} ans. Son frère a {d} ans de plus qu'{'elle' if p in PRENOMS[:5] else 'lui'}. "
               f"Quel âge a son frère ?",
               f"{a} + {d} = {a + d}.", f"Son frère a {a + d} ans.", "maths")
    elif kind == "prix":
        pu, n = rng.randint(2, 12), rng.randint(2, 9)
        ajoute(f"Un cahier coûte {pu} euros. Combien coûtent {n} cahiers ?",
               f"{pu} × {n} = {pu * n}.", f"{n} cahiers coûtent {pu * n} euros.", "maths")
    else:
        v, j = rng.randint(2, 25), rng.randint(2, 12)
        ajoute(f"{p} lit {v} pages par jour. Combien de pages lit-{'elle' if p in PRENOMS[:5] else 'il'} "
               f"en {j} jours ?",
               f"{v} × {j} = {v * j}.", f"{v * j} pages.", "maths")

# --------------------------------------------------------------------------------------
# 7. Suivi de consigne : comptage et format (l'autre echec du benchmark)
# --------------------------------------------------------------------------------------
LISTES = {
    "couleurs": ["rouge", "bleu", "vert", "jaune", "orange", "violet", "rose", "noir",
                 "blanc", "gris", "marron", "turquoise"],
    "fruits": ["pomme", "poire", "banane", "cerise", "fraise", "orange", "raisin",
               "pêche", "abricot", "melon", "kiwi", "prune"],
    "animaux": ["chat", "chien", "cheval", "lapin", "renard", "loup", "ours", "aigle",
                "souris", "tortue", "dauphin", "girafe"],
    "villes": ["Paris", "Lyon", "Marseille", "Lille", "Nantes", "Toulouse", "Bordeaux",
               "Nice", "Rennes", "Strasbourg", "Montpellier", "Grenoble"],
}
MOTS_NB = {1: "un", 2: "deux", 3: "trois", 4: "quatre", 5: "cinq", 6: "six"}

for _ in range(8_000):
    cat, items = rng.choice(list(LISTES.items()))
    n = rng.randint(2, 6)
    choix = rng.sample(items, n)
    style = rng.choice(["ligne", "numerote", "virgule"])
    if style == "ligne":
        q = f"Donne-moi {MOTS_NB[n]} {cat}, une par ligne."
        rep = "\n".join(choix)
    elif style == "numerote":
        q = f"Liste {MOTS_NB[n]} {cat}."
        rep = "\n".join(f"{i}. {c}" for i, c in enumerate(choix, 1))
    else:
        q = f"Cite {MOTS_NB[n]} {cat}, séparées par des virgules."
        rep = ", ".join(choix)
    pensee = (f"On demande exactement {n} {cat}. Je compte : "
              + ", ".join(f"{i} {c}" for i, c in enumerate(choix, 1))
              + f". Cela fait bien {n}.")
    ajoute(q, pensee, rep, "consigne")

# --------------------------------------------------------------------------------------
rng.shuffle(exemples)
exemples = exemples[:n_max]
with out_path.open("w", encoding="utf-8") as f:
    for ex in exemples:
        f.write(json.dumps(ex, ensure_ascii=False) + "\n")

par_kind = {}
for ex in exemples:
    par_kind[ex["k"]] = par_kind.get(ex["k"], 0) + 1
print(f"[i] {out_path} : {len(exemples)} exemples")
for k, v in sorted(par_kind.items()):
    print(f"    {k:10s} {v}")
