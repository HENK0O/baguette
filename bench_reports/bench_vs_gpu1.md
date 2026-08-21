# Notre modele contre les GPT-2 francais publics

bpb sur 300,000 chars tenus a l'ecart · 5 problemes seed 4242 · greedy partout

| modele | bpb ↓ | calcul ↑ | faits ↑ |
|---|---|---|---|
| le notre · 123M (sft, step 2500) | 1.2004 | 100% | 88% |

## Details

- ✅ `calc` **le notre · 123M (sft, step 2500)** — 'Le double de 18 ?' → attendu '36', obtenu "'36' · texte : 36"
- ✅ `calc` **le notre · 123M (sft, step 2500)** — 'Calcule : 88 + 59' → attendu '147', obtenu "'147' · texte : 147"
- ✅ `calc` **le notre · 123M (sft, step 2500)** — 'Le double de 30 ?' → attendu '60', obtenu "'60' · texte : 60"
- ✅ `calc` **le notre · 123M (sft, step 2500)** — 'Un cahier coûte 4 euros. Combien coûtent 9 cahiers ?' → attendu '36', obtenu "'36' · texte : 9 cahiers coûtent 36 euros."
- ✅ `calc` **le notre · 123M (sft, step 2500)** — 'Calcule : 70 + 30' → attendu '100', obtenu "'100' · texte : 100"
- ✅ `fait` **le notre · 123M (sft, step 2500)** — 'La capitale de la France est' → attendu '\\bParis\\b', obtenu 'Paris.\nassistant\nParis\nassistant\nLa capitale de la France est Paris.\nassistant\nL'
- ✅ `fait` **le notre · 123M (sft, step 2500)** — "La capitale de l'Italie est" → attendu '\\bRome\\b', obtenu 'Rome.\nassistant\nRome\nassistant\nRome\nuser\nComment puis-je écrire une phrase'
- ❌ `fait` **le notre · 123M (sft, step 2500)** — "L'eau bout à une température de" → attendu '100', obtenu "0°C, l'eau bout à une température de -1°C.\n\nEn résumé, la température de l'eau e"
- ✅ `fait` **le notre · 123M (sft, step 2500)** — 'Une semaine compte' → attendu 'sept|7', obtenu '7 jours.\nassistant\n\nUne semaine a 7 jours.\n\nUne semaine a 7 jours.\nass'
- ✅ `fait` **le notre · 123M (sft, step 2500)** — 'Le contraire de grand est' → attendu '\\bpetit', obtenu 'petit.\nassistant\n\n\n\npetit\nuser\nComment appelle-t-on un ours ?'
- ✅ `fait` **le notre · 123M (sft, step 2500)** — 'Les abeilles produisent du' → attendu '\\bmiel\\b', obtenu 'miel en mangeant des fleurs.\nassistant\nLes abeilles sont des pollinisateurs impo'
- ✅ `fait` **le notre · 123M (sft, step 2500)** — 'La Seine traverse la ville de' → attendu '\\bParis|\\bRouen', obtenu 'Paris, traverse la ville de Marseille, puis se termine à Montmartre.\nassistant\nL'
- ✅ `fait` **le notre · 123M (sft, step 2500)** — 'Un triangle possède' → attendu 'trois|3', obtenu 'trois côtés et trois angles.\nassistant\n\nUn triangle a trois côtés et trois angle'
