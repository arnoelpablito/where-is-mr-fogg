## Identifier le déplacement des personnages dans le roman : vers une modélisation de l’espace littéraire.

Stage de recherche au laboratoire Lattice (ENS, CNRS, Sorbonne Nouvelle).
Dans le cadre du projet [PROPP](https://lattice-8094.github.io/propp/)  (Pattern Recognition and Ontologies for Prose Processing) 

### Utilisation/Fichiers 
### Utilisation/Fichiers

Le projet est organisé autour de deux chaînes de traitement : une chaîne automatique à partir de PROPP et une chaîne manuelle à partir des annotations SACR.

#### Données d’entrée

- `data/PROPP/` : contient les fichiers utilisés pour le traitement automatique avec PROPP.
- `data/SACR/` : contient les annotations manuelles au format SACR :
  - `all_annots.sacr.tokens` : sortie tokens produite à partir du fichier SACR ;
  - `all_annots.sacr.entities` : sortie entités produite à partir du fichier SACR ;
- `data/dynaMouv.csv` : fichier contenant les informations de chapitres / déplacements utilisées pour enrichir les triptyques.

#### Résultats intermédiaires

Les fichiers `.conllu` sont stockés dans :
- `results/conllu/from_propp/` : sorties issues du traitement automatique PROPP ;
- `results/conllu/from_sacr/` : sorties issues des annotations manuelles SACR ;

#### Résultats finaux

Les triptyques extraits sont stockés dans :

- `results/csv_triptyques/auto_chap1to5.csv` : triptyques extraits automatiquement à partir de PROPP ;
- `results/csv_triptyques/auto_chap1to5_chap.csv` : mêmes triptyques avec ajout des chapitres ;
- `results/csv_triptyques/manuel_chap1to5.csv` : triptyques extraits à partir des annotations manuelles SACR ;
- `results/csv_triptyques/manuel_chap1to5_chap.csv` : mêmes triptyques avec ajout des chapitres.

#### Notebooks

Les notebooks doivent être exécutés dans l’ordre suivant :

1. `src/1_creation_corpus_annoté_depuis_propp.ipynb`  
   Crée ou prépare les fichiers annotés et les sorties CoNLL-U à partir de PROPP ou SACR.

2. `src/2_extraction_triptyque_depuis_conllu.ipynb`  
   Extrait les triptyques sujet-verbe-objet à partir d’un fichier `.conllu`.

3. `src/2bis_ajout_chapitres.ipynb`  
   Ajoute les informations de chapitres aux triptyques extraits.

4. `src/3_comparaison_triptyques.ipynb`  
   Compare les triptyques issus de l’annotation automatique et de l’annotation manuelle.

#### Exécution automatique

Le fichier suivant permet de lancer automatiquement les premiers notebooks de la chaîne de traitement (ici dans le mode auto donc pour les fichiers strictement PROPP):

```bash
python src/run_notebooks_1to2bis.py auto