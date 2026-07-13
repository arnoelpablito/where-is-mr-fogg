# Identifier le déplacement des personnages dans le roman : vers une modélisation de l’espace littéraire

Projet de recherche sur l’identification automatique du déplacement des personnages dans *Le Tour du monde en quatre-vingts jours* de Jules Verne.

Ce dépôt a été réalisé dans le cadre d’un stage au laboratoire Lattice (ENS, CNRS, Sorbonne Nouvelle), en lien avec le projet [PROPP](https://lattice-8094.github.io/propp/) (*Pattern Recognition and Ontologies for Prose Processing*). L’objectif est de construire une chaîne de traitement permettant de passer d’un texte annoté à des fichiers exploitables pour analyser les déplacements des personnages dans l’espace narratif.

## Objectif

Le projet cherche à repérer automatiquement des événements de déplacement dans le roman.

On s’appuie pour cela sur des triptyques :

```text
Sujet / Verbe / Objet ou complément
```

Exemples :

```text
Phileas Fogg / quitte / le Reform-Club
Passepartout / monte / dans le train
Fogg / arrive / à Suez
```

Ces triptyques sont ensuite enrichis avec des informations sur les personnages, les lieux, les véhicules, les temps et les types de déplacement.

## Organisation du dépôt

```text
where-is-mr-fogg/
│
├── data/
│   ├── PROPP/
│   ├── SACR/
│   └── dynaMouv.csv
│
├── modif_propp/
│   └── propp_fr_generate_tokens_and_entities_from_sacr_enrichi.py
│
├── results/
│   ├── conllu/
│   └── csv_triptyques/
│
├── src/
│   ├── 1_creation_corpus_annoté_depuis_propp.ipynb
│   ├── 2_extraction_triptyque_depuis_conllu.ipynb
│   ├── 2bis_ajout_chapitres.ipynb
│   ├── 3_comparaison_triptyques.ipynb
│   ├── 4_normalisation_temps_auto.ipynb
│   ├── 5_ajout_temps_triptyques_commun.ipynb
│   ├── 6_ajout_lieu_manuel.ipynb
│   ├── 7_trier_triptyques.ipynb
│   ├── run_notebooks_1to2bis.py
│   ├── run_propp_txt.py
│   └── sacr2entities_testAnnotEnrich.py
│
├── présentation.pdf
├── README.md
└── LICENSE
```

## Données

### `data/PROPP/`

Ce dossier contient les sorties issues de PROPP utilisées dans la chaîne automatique.

### `data/SACR/`

Ce dossier contient les annotations manuelles réalisées avec SACR.

Le schéma manuel ajoute notamment :

* `FUNCT` : fonction dans la phrase ;
* `STRUCT` : structure du groupe annoté ;
* `SPACESEM` : rôle spatial du lieu ;
* `VERBTYPE` : type de verbe de mouvement ou de position ;
* `PARTICULARITY` : négation, possibilité, dialogue, etc. ;
* `PROBL` : incertitude ou problème d’annotation.

Ces annotations permettent de distinguer un lieu cadre, une source, un but ou un lieu de passage.

### `data/dynaMouv.csv`

Ce fichier reprend des informations issues de [DinaVmouv](https://hal.science/hal-01979613), une ressource lexicale consacrée aux verbes de mouvement en français.

Dans ce projet, DinaVmouv sert à repérer les triptyques dont le verbe est pertinent pour l’analyse du déplacement. Elle permet notamment d’associer certains verbes à des catégories comme déplacement au sens strict, déplacement au sens faible, changement de relation ou changement de disposition.

## Modification de PROPP

Le dossier `modif_propp/` contient une version modifiée du script de génération des fichiers `.tokens` et `.entities` à partir d’un fichier SACR enrichi.

Le but est de rendre lisibles par PROPP les annotations manuelles complexes.

Par exemple, une annotation SACR comme :

```text
{reform_club:FUNCT="ARG argument",SPACESEM="SRC source",STRUCT="NP noun_phrase",TYPE="f FAC" le Reform-Club}
```

est transformée dans un format compatible :

```text
{reform_club:EN="FUNCT=ARG argument;SPACESEM=SRC source;STRUCT=NP noun_phrase;TYPE=f FAC" le Reform-Club}
```

Les informations sont ensuite réextraites dans le fichier `.entities` sous forme de colonnes :

```text
FUNCT
STRUCT
SPACESEM
VERBTYPE
PARTICULARITY
PROBL
```

Cette modification permet de conserver les informations manuelles utiles pour l’analyse du déplacement.

## Pipeline

### `src/1_creation_corpus_annoté_depuis_propp.ipynb`

Prépare le corpus et les fichiers nécessaires au traitement.

### `src/2_extraction_triptyque_depuis_conllu.ipynb`

Construit les triptyques à partir des dépendances syntaxiques.

Le script part des verbes, cherche leur sujet, puis leur objet ou complément. Il récupère les objets directs, mais aussi les compléments prépositionnels, importants pour les déplacements :

```text
arriver à Suez
monter dans le train
sortir de la maison
passer par le canal
```

Le résultat est un fichier `.csv` avec une ligne par triptyque potentiel.

### `src/2bis_ajout_chapitres.ipynb`

Ajoute l’information de chapitre aux triptyques.

### `src/3_comparaison_triptyques.ipynb`

Compare les triptyques issus de la chaîne automatique avec ceux issus des annotations manuelles.

### `src/4_normalisation_temps_auto.ipynb`

Extrait et normalise les expressions temporelles du roman.

### `src/5_ajout_temps_triptyques_commun.ipynb`

Rattache les temps normalisés aux triptyques.

### `src/6_ajout_lieu_manuel.ipynb`

Ajoute les lieux issus des annotations manuelles SACR.

Le notebook utilise notamment les rôles spatiaux :

```text
CAD cadre
SRC source
GOL goal
MED median
```

### `src/7_trier_triptyques.ipynb`

Crée des CSV plus simples à lire et à montrer pour présenter les résultats.

Il filtre les triptyques les plus utiles, par exemple ceux qui combinent :

* un personnage ;
* un verbe présent dans DinaVmouv ;
* un lieu ou un véhicule ;
* éventuellement une information temporelle.

Il produit des fichiers de présentation avec moins de colonnes techniques.

## Scripts d’exécution

### `src/run_notebooks_1to2bis.py`

Ce script permet de lancer automatiquement les premiers notebooks de la chaîne, jusqu’à l’ajout des chapitres.

Il rejoue les étapes suivantes :

```text
1_creation_corpus_annoté_depuis_propp.ipynb
2_extraction_triptyque_depuis_conllu.ipynb
2bis_ajout_chapitres.ipynb
```

Il prend un argument pour choisir la chaîne à lancer :

```bash
python src/run_notebooks_1to2bis.py auto
```

ou :

```bash
python src/run_notebooks_1to2bis.py manuel
```

`auto` correspond à la chaîne automatique à partir de PROPP.

`manuel` correspond à la chaîne fondée sur les annotations SACR.

### `src/run_propp_txt.py`

Lance PROPP sur un fichier texte et produit les fichiers `.tokens` et `.entities` associés.


## Résultats

Les fichiers produits sont stockés dans :

```text
results/csv_triptyques/
```

Les noms des fichiers suivent une codification progressive.

#### Préfixes

```text
auto_
```

désigne les fichiers issus de la chaîne automatique.

```text
manuel_
```

désigne les fichiers issus de la chaîne fondée sur les annotations manuelles SACR.

#### Suffixes

```text
_all
```

indique que le fichier porte sur l’ensemble du texte traité.

```text
_chap
```

indique que l’information de chapitre a été ajoutée.

```text
_temps
```

indique que les expressions temporelles normalisées ont été rattachées aux triptyques.

```text
_lieux_manuels
```

indique que les lieux issus des annotations manuelles SACR ont été ajoutés.

```text
_presentation
```

indique une version simplifiée, avec moins de colonnes techniques, destinée à la lecture ou à la présentation des résultats.

## Exécution

Les premiers notebooks peuvent être lancés avec :

```bash
python src/run_notebooks_1to2bis.py auto
```

ou :

```bash
python src/run_notebooks_1to2bis.py manuel
```

Les autres étapes peuvent ensuite être exécutées manuellement dans l’ordre indiqué dans le dossier `src/`.

Les scripts `run_propp_txt.py` et `sacr2entities_testAnnotEnrich.py` servent surtout à tester ou relancer des conversions plus ponctuelles.

## Remarque sur les fichiers `.conllu`

Les fichiers `.conllu` ont servi de format intermédiaire pour représenter les dépendances syntaxiques.

Ils restent présents dans le dépôt, mais ils ne sont pas une source d’information nouvelle : une partie des informations nécessaires à l’extraction des triptyques existe déjà dans les fichiers `.tokens`. Une partie du travail restant consiste à éliminer ce passage pour simplifier la chaîne de traitement.

## Présentation

La présentation effectuée au laboratoire Lattice en juin 2026 est disponible dans le dépôt sous le nom `présentation.pdf`.
