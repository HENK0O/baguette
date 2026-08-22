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
  refus    — l'information demandee est ABSENTE de l'enonce. Le modele repondait
             « il y a 8 bananes » a un panier de pommes et d'oranges : il additionne
             les nombres qu'il voit et fabrique une phrase confiante. Aucun corpus
             SFT grand public n'enseigne a dire « on ne peut pas savoir ».
  compose  — deux operations enchainees. « Le double du double de 5 » donnait 10 :
             le modele calcule la premiere etape et s'arrete. Le <think> pose donc
             les deux etapes separement.
  suite    — dialogues a deux tours dont le sujet change. Le modele traine un nombre
             de la question precedente dans la reponse suivante.

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
# 8. Refus : l'information n'est pas dans l'enonce
# --------------------------------------------------------------------------------------
ABSENTS = [
    ("pommes", "oranges", "bananes"),
    ("billes rouges", "billes vertes", "billes bleues"),
    ("crayons", "stylos", "gommes"),
    ("chats", "chiens", "lapins"),
    ("livres", "cahiers", "classeurs"),
    ("croissants", "pains", "brioches"),
]
for _ in range(3_000):
    a1, a2, absent = rng.choice(ABSENTS)
    n1, n2 = rng.randint(2, 40), rng.randint(2, 40)
    ajoute(f"J'ai {n1} {a1} et {n2} {a2} dans mon panier. "
           f"Combien y a-t-il de {absent} dans le panier ?",
           f"L'énoncé parle de {a1} et de {a2}. Il ne mentionne aucune {absent}.\n"
           f"La réponse est donc 0.",
           f"Il n'y a aucune {absent} dans le panier.", "refus")

HORS_SUJET = [
    ("Un train roule à {v} km/h pendant {h} heures.", "Quel âge a le conducteur ?",
     "l'âge du conducteur"),
    ("{p} a {a} ans. Son chat s'appelle Félix.", "Quel âge a le chat ?",
     "l'âge du chat"),
    ("J'achète une baguette à {v} euros et un croissant à {h} euros.",
     "Combien coûte le journal ?", "le prix du journal"),
    ("Le boulanger vend {v} croissants le matin.", "Combien de baguettes vend-il ?",
     "le nombre de baguettes"),
    ("{p} habite à {v} km de l'école.", "Combien de frères a-t-elle ?",
     "le nombre de frères"),
]
for _ in range(3_000):
    gab, question, manquant = rng.choice(HORS_SUJET)
    contexte = gab.format(v=rng.randint(2, 90), h=rng.randint(2, 12),
                          a=rng.randint(5, 60), p=rng.choice(PRENOMS))
    ajoute(f"{contexte} {question}",
           f"L'énoncé ne donne pas {manquant}.\n"
           f"Les nombres présents ne permettent pas de le calculer.",
           "On ne peut pas le savoir, l'énoncé ne le précise pas.", "refus")

# --------------------------------------------------------------------------------------
# 9. Composition : deux operations enchainees
# --------------------------------------------------------------------------------------
for _ in range(6_000):
    forme = rng.choice(["double_double", "moitie_somme", "ajoute_produit",
                        "soustrais_moitie", "triple_diff", "somme_doubles",
                        "chaine"])
    if forme == "double_double":
        a = rng.randint(2, 40)
        ajoute(f"Quel est le double du double de {a} ?",
               f"Le double de {a} = {a * 2}.\nLe double de {a * 2} = {a * 4}.",
               str(a * 4), "compose")
    elif forme == "moitie_somme":
        a, b = rng.randint(2, 40) * 2, rng.randint(2, 40) * 2
        ajoute(f"Quelle est la moitié de la somme de {a} et {b} ?",
               f"{a} + {b} = {a + b}.\nLa moitié de {a + b} = {(a + b) // 2}.",
               str((a + b) // 2), "compose")
    elif forme == "ajoute_produit":
        a, b, c = rng.randint(2, 12), rng.randint(2, 12), rng.randint(2, 30)
        ajoute(f"Ajoute {c} au produit de {a} et {b}. Combien ?",
               f"{a} × {b} = {a * b}.\n{a * b} + {c} = {a * b + c}.",
               str(a * b + c), "compose")
    elif forme == "soustrais_moitie":
        a, c = rng.randint(3, 40) * 2, rng.randint(2, 15)
        ajoute(f"Soustrais {c} de la moitié de {a}. Combien ?",
               f"La moitié de {a} = {a // 2}.\n{a // 2} - {c} = {a // 2 - c}.",
               str(a // 2 - c), "compose")
    elif forme == "triple_diff":
        a, b = rng.randint(10, 60), rng.randint(2, 9)
        ajoute(f"Quel est le triple de la différence entre {a} et {b} ?",
               f"{a} - {b} = {a - b}.\nLe triple de {a - b} = {(a - b) * 3}.",
               str((a - b) * 3), "compose")
    elif forme == "somme_doubles":
        a, b = rng.randint(2, 30), rng.randint(2, 30)
        ajoute(f"Quelle est la somme du double de {a} et du double de {b} ?",
               f"Le double de {a} = {a * 2}.\nLe double de {b} = {b * 2}.\n"
               f"{a * 2} + {b * 2} = {(a + b) * 2}.",
               str((a + b) * 2), "compose")
    else:
        d = rng.randint(2, 9)
        a = rng.randint(2, 30)
        b = rng.randint(1, 40)
        total = a + b
        total -= total % d           # on force une division exacte
        b = total - a
        if b < 1:
            continue
        ajoute(f"Prends {a}, ajoute {b}, puis divise le tout par {d}. Combien ?",
               f"{a} + {b} = {total}.\n{total} / {d} = {total // d}.",
               str(total // d), "compose")

# --------------------------------------------------------------------------------------
# 10. Suites de deux tours : le sujet change, les nombres du tour 1 ne doivent pas
#     contaminer le tour 2
# --------------------------------------------------------------------------------------
FAITS_COURTS = [
    ("Quelle est la capitale de la France ?", "Paris."),
    ("Qui a écrit Les Misérables ?", "Victor Hugo."),
    ("Combien de jours dans une semaine ?", "Sept."),
    ("De quelle couleur est la neige ?", "Blanche."),
    ("Quel est le premier mois de l'année ?", "Janvier."),
    ("Les abeilles produisent quoi ?", "Du miel."),
    ("Combien de côtés a un triangle ?", "Trois."),
    ("La Terre tourne autour de quoi ?", "Du Soleil."),
]
for _ in range(4_000):
    p_ = rng.choice(PRENOMS)
    o = rng.choice(OBJETS)
    a, b = rng.randint(20, 90), rng.randint(2, 19)
    q1 = f"{p_} a {a} {o} et en donne {b}. Combien lui en reste-t-il ?"
    r1 = f"<think>\n{a} - {b} = {a - b}.\n</think>\n{p_} a {a - b} {o}."
    q2, r2 = rng.choice(FAITS_COURTS)
    r2 = f"<think>\n\n</think>\n{r2}"
    exemples.append({
        "t": q1 + r1 + q2 + r2,
        "m": [{"role": "user", "text": q1}, {"role": "assistant", "text": r1},
              {"role": "user", "text": q2}, {"role": "assistant", "text": r2}],
        "k": "suite",
    })

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