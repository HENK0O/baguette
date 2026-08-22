# Benchmark hors-distribution v2 (familles secretes)

/!\ Ces enonces ne doivent jamais entrer dans un corpus d'entrainement.

| modele | transitif | piège | intervalle | branches | reste | cycle | composition | total | faits |
|---|---|---|---|---|---|---|---|---|---|
| le notre · 123M (sft, step 2500) | 2/6 | 5/6 | 1/6 | 2/5 | 1/5 | 0/5 | 7/7 | **18/40** | 11/12 |

## Details

- ✅ `transitif` **le notre · 123M (sft, step 2500)** — 'Léa est plus grande que Max. Max est plus grand que Zoé. Qui est le plus grand des trois ?' → attendu 'Léa', obtenu "'Léa' · texte : Léa est la plus grande."
- ❌ `transitif` **le notre · 123M (sft, step 2500)** — 'Paul court plus vite que Jules. Anna court plus vite que Paul. Qui est le plus rapide ?' → attendu 'Anna', obtenu "'Paul' · texte : C'est Paul qui est le plus rapide."
- ✅ `transitif` **le notre · 123M (sft, step 2500)** — 'Le chien est plus lourd que le chat. Le chat est plus lourd que le lapin. Qui est le plus léger ?' → attendu 'lapin', obtenu "'lapin' · texte : Le lapin est le plus léger."
- ❌ `transitif` **le notre · 123M (sft, step 2500)** — 'Marc est plus âgé que Lise. Lise est plus âgée que Tom. Qui est le plus jeune ?' → attendu 'Tom', obtenu "'Marc' · texte : Le plus jeune est Marc."
- ❌ `transitif` **le notre · 123M (sft, step 2500)** — 'La tour A est plus haute que la tour B. La tour C est plus basse que la tour B. Quelle tour est la plus haute ?' → attendu 'A', obtenu "'C' · texte : La tour C est la plus haute."
- ❌ `transitif` **le notre · 123M (sft, step 2500)** — "Zoé a plus de billes qu'Émile, et Émile en a plus que Sami. Qui en a le moins ?" → attendu 'Sami', obtenu "'Zoé' · texte : Zoé en a le moins, elle a 4 billes de moins que Émile."
- ✅ `piège` **le notre · 123M (sft, step 2500)** — "J'ai 5 pommes et 3 oranges dans mon panier. Combien y a-t-il de bananes dans le panier ?" → attendu '\\b(0|zéro|aucune?|pas de banane)', obtenu "Il n'y a aucune bananes dans le panier. · texte : Il n'y a aucune bananes dans le panier."
- ✅ `piège` **le notre · 123M (sft, step 2500)** — 'Un train roule à 80 km/h pendant 2 heures. Quel âge a le conducteur ?' → attendu '(ne (peux|peut|sait)|sais pas|impossible|pas possible|ne le dit pas|pas précisé|pas indiqué|inconnu|aucune information|ne permet pas)', obtenu "On ne peut pas le savoir, l'énoncé ne le précise pas. · texte : On ne peut pas le savoir, l'énoncé ne le précise pas."
- ✅ `piège` **le notre · 123M (sft, step 2500)** — "Marie a 12 ans. Son chat s'appelle Félix. Quel âge a le chat ?" → attendu '(ne (peux|peut|sait)|sais pas|impossible|pas possible|ne le dit pas|pas précisé|pas indiqué|inconnu|aucune information|ne permet pas)', obtenu "On ne peut pas le savoir, l'énoncé ne le précise pas. · texte : On ne peut pas le savoir, l'énoncé ne le précise pas."
- ✅ `piège` **le notre · 123M (sft, step 2500)** — "J'achète une baguette à 1 euro et un croissant à 2 euros. Combien coûte le journal ?" → attendu '(ne (peux|peut|sait)|sais pas|impossible|pas possible|ne le dit pas|pas précisé|pas indiqué|inconnu|aucune information|ne permet pas)', obtenu "On ne peut pas le savoir, l'énoncé ne le précise pas. · texte : On ne peut pas le savoir, l'énoncé ne le précise pas."
- ❌ `piège` **le notre · 123M (sft, step 2500)** — 'Dans un sac, il y a 10 billes rouges. Combien de billes bleues y a-t-il dans le sac ?' → attendu '\\b(0|zéro|aucune?|pas de bille bleue)', obtenu "On ne peut pas le savoir, l'énoncé ne le précise pas. · texte : On ne peut pas le savoir, l'énoncé ne le précise pas."
- ✅ `piège` **le notre · 123M (sft, step 2500)** — "Le boulanger vend 30 croissants le matin et 20 l'après-midi. Combien de baguettes vend-il ?" → attendu '\\b(0|zéro|aucune?)\\b|(ne (peux|peut|sait)|sais pas|impossible|ne le dit pas|pas précisé|inconnu)', obtenu "On ne peut pas le savoir, l'énoncé ne le précise pas. · texte : On ne peut pas le savoir, l'énoncé ne le précise pas."
- ❌ `intervalle` **le notre · 123M (sft, step 2500)** — 'Combien y a-t-il de nombres entiers de 4 à 9, en comptant 4 et 9 ?' → attendu '6', obtenu "'36' · texte : 36"
- ❌ `intervalle` **le notre · 123M (sft, step 2500)** — 'Une clôture droite de 12 mètres a un poteau tous les 3 mètres, avec un poteau à chaque bout. Combien de poteaux ?' → attendu '5', obtenu "'9' · texte : Il y a 9 mètres dans une clôture."
- ❌ `intervalle` **le notre · 123M (sft, step 2500)** — 'Je lis du chapitre 3 au chapitre 8 inclus. Combien de chapitres vais-je lire ?' → attendu '6', obtenu "'3' · texte : Il y a 24 chapitres dans le chapitre 3."
- ❌ `intervalle` **le notre · 123M (sft, step 2500)** — "Un immeuble a des étages numérotés de 0 à 6. Combien d'étages différents l'ascenseur dessert-il ?" → attendu '7', obtenu "'6' · texte : L'ascenseur dessert un étage de 0 à 6."
- ✅ `intervalle` **le notre · 123M (sft, step 2500)** — 'Un escalier a 10 marches. Je suis sur la 4e marche. Combien de marches me reste-t-il à monter ?' → attendu '6', obtenu "'6' · texte : Il te reste 6 marches."
- ❌ `intervalle` **le notre · 123M (sft, step 2500)** — 'On coupe un ruban en 5 morceaux. Combien de coupes faut-il faire ?' → attendu '4', obtenu "'50' · texte : Il faut faire 50 coupes."
- ❌ `branches` **le notre · 123M (sft, step 2500)** — "Qu'est-ce qui coûte le plus cher : 3 stylos à 2 euros pièce, ou 2 cahiers à 4 euros pièce ?" → attendu 'cahier', obtenu "'stylo' · texte : Le coût de 3 stylos à 2 euros est de 4 euros."
- ✅ `branches` **le notre · 123M (sft, step 2500)** — 'Qui a le plus de fruits : Ali avec 4 sacs de 3 pommes, ou Bea avec 2 sacs de 7 pommes ?' → attendu 'Bea', obtenu "'Bea' · texte : Bey a 4 sacs de 7 pommes, ou Bea a 2 sacs de 7 pommes."
- ❌ `branches` **le notre · 123M (sft, step 2500)** — 'Lise calcule 6 × 5. Nino calcule 4 × 8. Qui obtient le plus grand résultat ?' → attendu 'Nino', obtenu 'None · texte : 30'
- ❌ `branches` **le notre · 123M (sft, step 2500)** — "Un pack de 6 bouteilles coûte 12 euros. Une bouteille seule coûte 3 euros. Qu'est-ce qui est le moins cher par bouteille ?" → attendu 'pack', obtenu 'None · texte : 18 euros.'
- ✅ `branches` **le notre · 123M (sft, step 2500)** — 'Tom a 25 billes et en gagne 5. Léo a 40 billes et en perd 15. Qui a le plus de billes maintenant ?' → attendu 'Tom', obtenu "'Tom' · texte : Tom a 20 billes."
- ❌ `reste` **le notre · 123M (sft, step 2500)** — 'On partage 23 bonbons entre 4 enfants, chacun en reçoit autant. Combien de bonbons restent ?' → attendu '3', obtenu "'14' · texte : Il reste 27 bonbons à 14 enfants."
- ❌ `reste` **le notre · 123M (sft, step 2500)** — "J'ai 17 œufs et des boîtes de 6. Je remplis uniquement des boîtes complètes. Combien d'œufs ne sont pas en boîte ?" → attendu '5', obtenu "'23' · texte : Il y a 23 œufs en boîte."
- ❌ `reste` **le notre · 123M (sft, step 2500)** — 'Un ruban de 20 cm est coupé en morceaux de 6 cm. Quelle longueur de ruban reste-t-il, en cm ?' → attendu '2', obtenu "'26' · texte : Le ruban est maintenant 26 cm."
- ✅ `reste` **le notre · 123M (sft, step 2500)** — "31 élèves montent dans des voitures de 4 places. Toutes les voitures sont pleines sauf la dernière. Combien d'élèves dans la dernière voiture ?" → attendu '3', obtenu "'3' · texte : Il y a 31 - 4 = 27 étudiants qui sont encore pleines. Il y a 27 - 1 = 26 étudiants qui sont encore en train de conduire. Il y a donc 27 - 26 = 3 étudiants qui sont encore en train de conduire."
- ❌ `reste` **le notre · 123M (sft, step 2500)** — 'Il y a 50 chaises à ranger en rangées de 8. Combien de chaises ne forment pas une rangée complète ?' → attendu '2', obtenu "'480' · texte : Il y a 50 x 8 = 480 chaises qui ne forment pas une rangée complète."
- ❌ `cycle` **le notre · 123M (sft, step 2500)** — 'Nous sommes mardi. Quel jour serons-nous dans 3 jours ?' → attendu 'vendredi', obtenu 'None · texte : 17'
- ❌ `cycle` **le notre · 123M (sft, step 2500)** — "Hier, c'était dimanche. Quel jour serons-nous demain ?" → attendu 'mardi', obtenu "None · texte : Je suis désolé, mais je ne peux pas répondre à cette question car je suis un modèle de langage AI et je n'ai pas accès à des informations en temps réel. Je ne peux pas non plus fournir d'informations "
- ❌ `cycle` **le notre · 123M (sft, step 2500)** — 'Nous sommes samedi. Quel jour étions-nous il y a 2 jours ?' → attendu 'jeudi', obtenu "None · texte : Il y a 4 jours dans l'année."
- ❌ `cycle` **le notre · 123M (sft, step 2500)** — 'Nous sommes vendredi. Quel jour serons-nous dans 7 jours ?' → attendu 'vendredi', obtenu 'None · texte : 21'
- ❌ `cycle` **le notre · 123M (sft, step 2500)** — 'Nous sommes jeudi. Quel jour serons-nous dans 4 jours ?' → attendu 'lundi', obtenu 'None · texte : 4 jours.'
- ✅ `composition` **le notre · 123M (sft, step 2500)** — 'Quel est le double du double de 5 ?' → attendu '20', obtenu "'20' · texte : 20"
- ✅ `composition` **le notre · 123M (sft, step 2500)** — 'Quelle est la moitié de la somme de 6 et 10 ?' → attendu '8', obtenu "'8' · texte : 8"
- ✅ `composition` **le notre · 123M (sft, step 2500)** — 'Ajoute 3 au produit de 4 et 5. Combien ?' → attendu '23', obtenu "'23' · texte : 23"
- ✅ `composition` **le notre · 123M (sft, step 2500)** — 'Soustrais 2 de la moitié de 18. Combien ?' → attendu '7', obtenu "'7' · texte : 7"
- ✅ `composition` **le notre · 123M (sft, step 2500)** — 'Quel est le triple de la différence entre 9 et 4 ?' → attendu '15', obtenu "'15' · texte : 15"
- ✅ `composition` **le notre · 123M (sft, step 2500)** — 'Prends 10, ajoute 5, puis divise le tout par 3. Combien ?' → attendu '5', obtenu "'5' · texte : 5"
- ✅ `composition` **le notre · 123M (sft, step 2500)** — 'Quelle est la somme du double de 3 et du double de 4 ?' → attendu '14', obtenu "'14' · texte : 14"
- ✅ `fait` **le notre · 123M (sft, step 2500)** — 'La capitale du Portugal est' → attendu '\\bLisbonne\\b', obtenu 'Lisbonne.\nassistant\nLa capitale du Portugal est Brasília.\nassistant\nLa capitale du Portugal est'
- ✅ `fait` **le notre · 123M (sft, step 2500)** — 'La capitale de la Belgique est' → attendu '\\bBruxelles\\b', obtenu 'Bruxelles.\nassistant\nLa capitale de la Belgique est Bruxelles.\nuser\nComment puis-je trouver la capit'
- ❌ `fait` **le notre · 123M (sft, step 2500)** — 'Le mois de février compte généralement' → attendu '\\b28\\b|vingt-huit', obtenu 'trois mois : mars, avril et mai.\nassistant\nLe mois de février est généralement considéré comme le dé'
- ✅ `fait` **le notre · 123M (sft, step 2500)** — 'Le contraire de gauche est la' → attendu '\\bdroite\\b', obtenu "droite.\n\nL'énoncé ne donne pas le contraire de gauche.\nassistant\n\nOn ne peut pas le"
- ✅ `fait` **le notre · 123M (sft, step 2500)** — "Les poissons vivent dans l'" → attendu '\\beau\\b', obtenu 'eau douce et les poissons sont des animaux aquatiques.\nassistant\nLes poissons sont des animaux aquat'
- ✅ `fait` **le notre · 123M (sft, step 2500)** — "L'auteur des Misérables est" → attendu '\\bHugo\\b', obtenu 'Victor Hugo.\nassistant\nVictor Hugo est un écrivain, poète et dramaturge français du XIXe siècle'
- ✅ `fait` **le notre · 123M (sft, step 2500)** — 'Un vélo a deux' → attendu '\\broues?\\b', obtenu 'roues, et les roues sont les roues. Le vélo a deux roues, et les roues sont les roues.\nassistant\nUn '
- ✅ `fait` **le notre · 123M (sft, step 2500)** — 'La Terre tourne autour du' → attendu '\\b[Ss]oleil\\b', obtenu "Soleil. C'est une sphère, ce qui signifie que c'est une sphère. La Terre tourne sur son axe, ce qui"
- ✅ `fait` **le notre · 123M (sft, step 2500)** — "Le premier mois de l'année est" → attendu '\\bjanvier\\b', obtenu "le mois de janvier, qui est le mois de l'année où le soleil est le plus brillant. Le mois de février"
- ✅ `fait` **le notre · 123M (sft, step 2500)** — 'Les feuilles des arbres sont généralement de couleur' → attendu '\\bvert', obtenu 'verte, jaune ou violette. Les feuilles des arbres sont généralement de couleur rouge, orange ou jaun'
- ✅ `fait` **le notre · 123M (sft, step 2500)** — 'Pour écrire, on utilise un stylo ou un' → attendu '\\bcrayon\\b|\\bclavier\\b|\\bfeutre\\b|\\bstylet\\b', obtenu "crayon pour dessiner la forme de l'image. Ensuite, on utilise un crayon pour écrire le nom de la per"
- ✅ `fait` **le notre · 123M (sft, step 2500)** — 'Le lait provient principalement de la' → attendu '\\bvache\\b', obtenu 'vache, qui est la principale source de lait. Le lait est ensuite chauffé et la chaleur du lait est t'
