import os
import subprocess

MODE = "auto"   # "auto" ou "manuel" => auto pour les fichiers strictement PROPP et manuel pour les fichiers SACR

env = os.environ.copy()

if MODE == "auto":
    env["DATA"] = "../data/PROPP/new_txt"
    env["CONLLU_OUTPUT"] = "../results/conllu/from_propp"
    env["CONLLU_INPUT"] = "../results/conllu/from_propp/tdm_auto_chap1to5.conllu"
    env["TRIPTYQUES_OUTPUT"] = "../results/csv_triptyques/auto_chap1to5.csv"
    env["TRIPTYQUES_CHAP_OUTPUT"] = "../results/csv_triptyques/auto_chap1to5_chap.csv"

elif MODE == "manuel":
    env["DATA"] = "../data/SACR"
    env["CONLLU_OUTPUT"] = "../results/conllu/from_sacr"
    env["CONLLU_INPUT"] = "../results/conllu/from_sacr/all_annots.sacr.conllu"
    env["TRIPTYQUES_OUTPUT"] = "../results/csv_triptyques/manuel_chap1to5.csv"
    env["TRIPTYQUES_CHAP_OUTPUT"] = "../results/csv_triptyques/manuel_chap1to5_chap.csv"

else:
    raise ValueError("MODE doit être 'auto' ou 'manuel'")


notebooks = [
    "1_creation_corpus_annoté_depuis_propp.ipynb",
    "2_extraction_triptyque_depuis_conllu.ipynb",
    "2bis_ajout_chapitres.ipynb",
]

for notebook in notebooks:
    print(f"\n=== Running {notebook} [{MODE}] ===")

    subprocess.run(
        [
            "python", "-m", "jupyter",
            "nbconvert",                    # il faut pip install nbconvert pour que ca fonctionne
            "--to", "notebook",
            "--execute",
            "--inplace",
            notebook,
        ],
        cwd="src",
        env=env,
        check=True,
    )

print(f"\nTous les notebooks ont été exécutés en mode {MODE}.")