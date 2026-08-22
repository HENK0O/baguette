# Benchmark hors-distribution (problemes 100% inedits)

| modele | reformule | contexte | concept | total | faits |
|---|---|---|---|---|---|
| le notre · 123M (sft, step 2500) | 12/15 | 10/15 | 6/10 | 28/40 | 8/8 |

## Details

- ✅ `reformulé` **le notre · 123M (sft, step 2500)** — "Si j'ai 14 billes et que tu m'en donnes 9, combien en ai-je ?" → attendu '23', obtenu "'23' · texte : Tu as 23 billes."
- ✅ `reformulé` **le notre · 123M (sft, step 2500)** — 'Quel est le résultat de 45 moins 17 ?' → attendu '28', obtenu "'28' · texte : 28"
- ✅ `reformulé` **le notre · 123M (sft, step 2500)** — 'Additionne 23 et 39.' → attendu '62', obtenu "'62' · texte : 62"
- ✅ `reformulé` **le notre · 123M (sft, step 2500)** — 'Retire 8 de 30.' → attendu '22', obtenu "'22' · texte : 22"
- ✅ `reformulé` **le notre · 123M (sft, step 2500)** — 'Chaque table a 4 chaises. Il y a 7 tables. Combien de chaises ?' → attendu '28', obtenu "'28' · texte : Il y a 28 chaises."
- ✅ `reformulé` **le notre · 123M (sft, step 2500)** — 'Trois amis se partagent 27 bonbons à parts égales. Combien chacun en reçoit-il ?' → attendu '9', obtenu "'9' · texte : Chaque enfant reçoit 9 bonbons."
- ✅ `reformulé` **le notre · 123M (sft, step 2500)** — 'Le double de 16 ?' → attendu '32', obtenu "'32' · texte : 32"
- ✅ `reformulé` **le notre · 123M (sft, step 2500)** — 'La moitié de 90 ?' → attendu '45', obtenu "'45' · texte : 45"
- ❌ `reformulé` **le notre · 123M (sft, step 2500)** — '9 de plus que 37, ça fait combien ?' → attendu '46', obtenu "'136' · texte : 136"
- ✅ `reformulé` **le notre · 123M (sft, step 2500)** — 'Quelle est la différence entre 80 et 46 ?' → attendu '34', obtenu "'34' · texte : 34"
- ✅ `reformulé` **le notre · 123M (sft, step 2500)** — 'Quel nombre vient après 15 quand on compte de 5 en 5 ?' → attendu '20', obtenu "'20' · texte : 20"
- ❌ `reformulé` **le notre · 123M (sft, step 2500)** — '1000 moins 1 ?' → attendu '999', obtenu "'119' · texte : 119"
- ✅ `reformulé` **le notre · 123M (sft, step 2500)** — 'Combien de fois 6 dans 42 ?' → attendu '7', obtenu "'7' · texte : 7"
- ✅ `reformulé` **le notre · 123M (sft, step 2500)** — '5 équipes de 11 joueurs. Combien de joueurs en tout ?' → attendu '55', obtenu "'55' · texte : Il y a 55 joueurs en tout."
- ❌ `reformulé` **le notre · 123M (sft, step 2500)** — 'De 13 pour aller à 21, combien faut-il ajouter ?' → attendu '8', obtenu "'26' · texte : 26"
- ✅ `contexte` **le notre · 123M (sft, step 2500)** — "J'avais 50 euros. Après avoir acheté un jeu à 34 euros, combien me reste-t-il ?" → attendu '16', obtenu "'16' · texte : Il te reste 16 euros."
- ❌ `contexte` **le notre · 123M (sft, step 2500)** — "Un bus transporte 28 passagers. À l'arrêt, 12 descendent et 5 montent. Combien de passagers restent dans le bus ?" → attendu '21', obtenu "'16' · texte : Il reste 16 passagers dans le bus."
- ❌ `contexte` **le notre · 123M (sft, step 2500)** — 'Sur 25 élèves, 11 sont des filles. Combien y a-t-il de garçons ?' → attendu '14', obtenu "'5' · texte : Il y a 5 garçons."
- ✅ `contexte` **le notre · 123M (sft, step 2500)** — "J'achète 3 croissants à 2 euros pièce. Je paie avec 10 euros. On me rend combien ?" → attendu '4', obtenu "'4' · texte : On me rend 4 euros."
- ✅ `contexte` **le notre · 123M (sft, step 2500)** — "Un fermier a 12 poules. Chaque poule pond 2 œufs. Combien d'œufs au total ?" → attendu '24', obtenu "'24' · texte : Il y a 24 œufs au total."
- ✅ `contexte` **le notre · 123M (sft, step 2500)** — 'Tom lit 10 pages par jour. Combien de pages lit-il en une semaine ?' → attendu '70', obtenu "'70' · texte : 70 pages."
- ✅ `contexte` **le notre · 123M (sft, step 2500)** — "Il y a 24 heures dans une journée. Combien d'heures dans 3 journées ?" → attendu '72', obtenu "'72' · texte : Il y a 72 heures dans une journée."
- ❌ `contexte` **le notre · 123M (sft, step 2500)** — "Un livre fait 120 pages. J'en ai lu 45. Combien de pages me reste-t-il à lire ?" → attendu '75', obtenu "'255' · texte : Il te reste 255 pages."
- ❌ `contexte` **le notre · 123M (sft, step 2500)** — 'Le train part avec 100 passagers. À la première gare, 23 descendent. À la deuxième, 41 descendent. Combien reste-t-il de passagers ?' → attendu '36', obtenu "'73' · texte : Il reste 73 passagers à Hugo."
- ✅ `contexte` **le notre · 123M (sft, step 2500)** — "Emma a 7 ans. Son frère a 3 ans de plus qu'elle. Quel âge a son frère ?" → attendu '10', obtenu "'10' · texte : Son frère a 10 ans."
- ✅ `contexte` **le notre · 123M (sft, step 2500)** — "J'ai 15 pommes rouges et 8 pommes vertes. Combien de pommes en tout ?" → attendu '23', obtenu "'23' · texte : Il y a 23 pommes en tout."
- ❌ `contexte` **le notre · 123M (sft, step 2500)** — 'Nina a 40 stickers. Elle en colle la moitié. Combien lui en reste-t-il ?' → attendu '20', obtenu "'38' · texte : Il lui reste 38 stickers."
- ✅ `contexte` **le notre · 123M (sft, step 2500)** — 'Un kilo de pommes coûte 3 euros. Combien coûtent 2 kilos ?' → attendu '6', obtenu "'6' · texte : 2 kilos coûtent 6 euros."
- ✅ `contexte` **le notre · 123M (sft, step 2500)** — 'Papa a 40 ans et maman a 38 ans. Quelle est la somme de leurs âges ?' → attendu '78', obtenu "'78' · texte : La somme de leurs âges est 78 ans."
- ✅ `contexte` **le notre · 123M (sft, step 2500)** — 'Un escargot avance de 2 mètres par jour. Quelle distance parcourt-il en 5 jours ?' → attendu '10', obtenu "'10' · texte : 10 minutes."
- ✅ `concept` **le notre · 123M (sft, step 2500)** — 'Combien font trois plus cinq ?' → attendu '8', obtenu "'8' · texte : 8"
- ✅ `concept` **le notre · 123M (sft, step 2500)** — 'Marie a 3 fois plus de livres que Paul. Paul en a 8. Combien Marie en a-t-elle ?' → attendu '24', obtenu "'24' · texte : Marie a 24 livres."
- ❌ `concept` **le notre · 123M (sft, step 2500)** — 'Il me faut 60 œufs. Les boîtes contiennent 12 œufs chacune. Combien de boîtes dois-je acheter ?' → attendu '5', obtenu "'24' · texte : Il faut acheter 24 boîtes."
- ✅ `concept` **le notre · 123M (sft, step 2500)** — 'Un film commence à 20 h et dure 2 heures. À quelle heure se termine-t-il ?' → attendu '22', obtenu "'22' · texte : Il se termine à 22 h."
- ❌ `concept` **le notre · 123M (sft, step 2500)** — 'Léo est né en 2010. Quel âge a-t-il en 2026 ?' → attendu '16', obtenu "'67' · texte : En 2026, Léo a 67 ans."
- ❌ `concept` **le notre · 123M (sft, step 2500)** — 'Un carré a des côtés de 6 cm. Quel est son périmètre ?' → attendu '24', obtenu "'12' · texte : Son périmètre est de 12 cm."
- ❌ `concept` **le notre · 123M (sft, step 2500)** — 'Un crayon coûte 1 euro et une gomme coûte 2 euros. Combien coûtent 2 crayons et 1 gomme ?' → attendu '4', obtenu "'2' · texte : 2 crayons et 1 gomme coûtent 2 euros."
- ✅ `concept` **le notre · 123M (sft, step 2500)** — "Dans une classe de 30 élèves, un tiers porte des lunettes. Combien d'élèves portent des lunettes ?" → attendu '10', obtenu "'10' · texte : Un tiers de 30 élèves, soit 30/3 = 10 élèves, portent des lunettes."
- ✅ `concept` **le notre · 123M (sft, step 2500)** — 'Il est 15 h. Quelle heure sera-t-il dans 4 heures ?' → attendu '19', obtenu "'19' · texte : Il sera 19 h."
- ✅ `concept` **le notre · 123M (sft, step 2500)** — "J'ai deux billets de 20 euros. Combien d'argent ai-je en tout ?" → attendu '40', obtenu "'40' · texte : Tu as 40 euros en tout."
- ✅ `fait` **le notre · 123M (sft, step 2500)** — "La capitale de l'Espagne est" → attendu '\\bMadrid\\b', obtenu "Madrid.\nassistant\nLa capitale de l'Espagne est Madrid.\nuser\nComment puis-je trouver la capitale de"
- ✅ `fait` **le notre · 123M (sft, step 2500)** — "La capitale de l'Allemagne est" → attendu '\\bBerlin\\b', obtenu "Berlin.\nassistant\nBerlin\nuser\nComment puis-je trouver la capitale de l'Allemagne ?"
- ✅ `fait` **le notre · 123M (sft, step 2500)** — 'Une année compte' → attendu 'douze|12|365', obtenu "en moyenne 365 jours par an.\nassistant\nPour calculer la moyenne d'une année, il faut multiplier le n"
- ✅ `fait` **le notre · 123M (sft, step 2500)** — 'Le fromage est fabriqué à partir de' → attendu '\\blait\\b', obtenu "lait, de lait caillé, de levure et d'eau, et est généralement cuit lentement dans un four chaud ou a"
- ✅ `fait` **le notre · 123M (sft, step 2500)** — 'La neige est de couleur' → attendu '\\bblanc', obtenu 'bleue.\nassistant\n\n\n\nBlanche.\nassistant\n\nBlanche.\nass'
- ✅ `fait` **le notre · 123M (sft, step 2500)** — 'Le miel est produit par les' → attendu '\\babeille', obtenu 'abeilles, qui produisent des fleurs et des graines. Les abeilles sont des insectes sociaux qui viven'
- ✅ `fait` **le notre · 123M (sft, step 2500)** — 'En hiver, il fait généralement' → attendu '\\bfroid\\b', obtenu 'plus chaud et plus froid, mais il y a aussi plus de vent et de froid. Cela peut être dû à une variét'
- ✅ `fait` **le notre · 123M (sft, step 2500)** — 'Un carré possède quatre' → attendu 'côtés|angles|sommets', obtenu 'côtés, quatre angles droits et quatre côtés.\nassistant\nUn carré a 4 côtés, 4 angles droits et 4 côté'
