from pathlib import Path
from propp_fr import generate_tokens_and_entities_from_sacr_enrichi, load_spacy_model

spacy_model = load_spacy_model()

file_name="all_annots.sacr"

test = generate_tokens_and_entities_from_sacr_enrichi(file_name,"Model_TDM/data/SACR",spacy_model=spacy_model)