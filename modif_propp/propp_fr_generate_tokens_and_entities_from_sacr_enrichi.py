import os
import re
import pandas as pd
import numpy as np
from tqdm.auto import tqdm

from .propp_fr_load_save_functions import load_sacr_file, save_text_file, save_tokens_df, save_entities_df
from .propp_fr_generate_tokens_df import load_spacy_model, generate_tokens_df
from .propp_fr_add_entities_features import add_features_to_entities


def clean_sacr_content(sacr_content):
    """Removes color and tokenization metadata from the end of SACR files."""
    color_idx = sacr_content.find("#COLOR")
    tokenization_idx = sacr_content.find("#TOKENIZATION-TYPE")


    # MODIF
    # Objectif :
    # Transformer une ouverture SACR du type : {mr_fogg:FUNCT="...",TYPE="p PER",VERBTYPE="..." texte}
    # En : {mr_fogg:EN="FUNCT=...;TYPE=p PER;VERBTYPE=..." texte} pour tout type de schéma d'annotation SACR

    pattern = (
        r'\{([A-Za-z0-9_-]+):'                      # groupe 1 : nom de l'entité / COREF
        r'((?:[A-Za-z0-9_-]+="[^"]*"\s*,?\s*)+)'    # groupe 2 : tous les champs LABEL="valeur"
        r'\s+'                                      # espace avant le texte annoté
    )

    def replacement(match):
        coref_name = match.group(1)
        attributes = match.group(2)

        pairs = re.findall(
            r'([A-Za-z0-9_-]+)="([^"]*)"',          # groupe a : nom du champ ; groupe b : valeur
            attributes
        )

        annotation_value = ";".join(                # on reconstruit nos annotations à l'aide du groupe a et b, on sépare le tout avec un ;
            f"{key}={value}"
            for key, value in pairs
        )

        return f'{{{coref_name}:EN="{annotation_value}" '

    sacr_content = re.sub(
        pattern,
        replacement,
        sacr_content
    )
    # FIN DE MODIF

    # Find the first occurring metadata marker
    first_metadata_idx = min(filter(lambda x: x != -1, [color_idx, tokenization_idx]), default=-1)

    if first_metadata_idx != -1:
        sacr_content = sacr_content[:first_metadata_idx].rstrip()

    sacr_content = sacr_content.strip()
    sacr_content = re.sub(r'�', ' ', sacr_content)
    sacr_content = re.sub(r'■', ' ', sacr_content)
    sacr_content = re.sub(r'•', ' ', sacr_content)
    sacr_content = sacr_content.replace("’", "'")
    sacr_content = sacr_content.replace("' ", "'")
    sacr_content = sacr_content.replace(' .', '.')
    sacr_content = sacr_content.replace(" , ", ", ")
    sacr_content = sacr_content.replace("\xa0", " ")
    # Replace multiple spaces (but not newlines) with a single space
    sacr_content = re.sub(r'[–—―‒]', '-', sacr_content)
    sacr_content = sacr_content.replace(".-", ". -")
    sacr_content = sacr_content.replace("!-", "! -")
    sacr_content = sacr_content.replace("?-", "? -")
    sacr_content = sacr_content.replace(" }", "}")
    sacr_content = sacr_content.replace(",}", "},")
    sacr_content = re.sub(r'(?<=\S) {2,}(?=\S)', ' ', sacr_content)
    return sacr_content

def remove_sacr_annotations(sacr_content):
    # Remove all substrings matching the mention_oppening_pattern

    mention_oppening_pattern = r'\{[A-Za-z0-9_-]+:EN="([^"]*)"+ '
    
    raw_text = re.sub(mention_oppening_pattern, "", sacr_content)

    # Remove all '}' mention_closing characters
    raw_text = raw_text.replace('{', '')
    raw_text = raw_text.replace('}', '')
    raw_text = raw_text.replace("\xa0", " ")
    # Replace multiple spaces (but not newlines) with a single space
    # raw_text = re.sub(r'(?<=\S) {2,}(?=\S)', ' ', raw_text)
    raw_text = raw_text.replace(' .', '.')
    # raw_text = raw_text.replace(' , ', ', ')
    raw_text = raw_text.replace("’ ", "'")
    
    return raw_text

def get_mention_text_from_ids(start_id, end_id, text):
    return text[start_id: end_id]

def extract_entities_annotations(sacr_content):
    mention_opening_pattern = r'\{[A-Za-z0-9_-]+:EN="([^"]*)"+ '
    
    # Find all matches with their start and end positions
    matches = [(m.start(), m.end(), m.group()) for m in re.finditer(mention_opening_pattern, sacr_content)]
    opening_ids = sorted([start for start, end, match in matches])
    closing_ids = [i for i, char in enumerate(sacr_content) if char == "}"] # Find indices of all "}" characters

    # annotation pairs
    ordered_annotations_boundaries = []
    for annotation_opening in opening_ids:
        closing_candidates = [end for end in closing_ids if end > annotation_opening]
        for closing_candidate in closing_candidates:
            contained_annotations_opening = [start for start in opening_ids if annotation_opening < start < closing_candidate]
            contained_annotations_closing = [end for end in closing_candidates if annotation_opening < end < closing_candidate]
            if len(contained_annotations_opening) == len(contained_annotations_closing):
                ordered_annotations_boundaries.append({"sacr_start_id": annotation_opening,
                                                       "sacr_end_id": closing_candidate})
                break

    # le df des entites avec start et end (ordonnes)
    df = pd.DataFrame(ordered_annotations_boundaries)
    
    # Apply the function to create a new 'text' column
    df["annotation"] = df.apply(lambda row: get_mention_text_from_ids(row["sacr_start_id"], row["sacr_end_id"]+1, sacr_content), axis=1)
    # Apply regex to extract the substring between { and :EN="
    df["COREF_name"] = df["annotation"].str.extract(r'\{([A-Za-z0-9_-]+):EN="')
    # Apply regex to extract text between the first two quotation marks

    # MODIF : un "_" pour garder la 'cat' (exemple : EN=p PER)
    #df["cat"] = df["annotation"].str.extract(r'="([^"]*)"')
    df["annotation"] = df["annotation"].str.extract(r'EN="([^"]*)"') # on prends ce qui a l'interieur des annotations SACR comme colonne

    df["cat"] = df["annotation"].str.extract(r'TYPE=([^;]*)') # on selectionne en particulier TYPE car c'est la ou on la cat

    df["cat"] = df["cat"].fillna("")

    # FIN DE MODIF

    return df

def convert_ids_from_sacr_to_recovered(entities_df, sacr_content, recovered_text):
    all_ids = entities_df["sacr_start_id"].tolist() + entities_df["sacr_end_id"].tolist()
    sorted_ids = sorted(all_ids)

    sacr_to_recovered_index_dict = {}

    for sacr_index in sorted_ids:
        last_known_sacr_index = max(list(sacr_to_recovered_index_dict.keys()), default=None)
        if last_known_sacr_index:
            last_known_recovered_text_index = sacr_to_recovered_index_dict[last_known_sacr_index]
            sacr_to_recovered_delta = len(remove_sacr_annotations(sacr_content[last_known_sacr_index:sacr_index]))
            recovered_text_index = last_known_recovered_text_index + sacr_to_recovered_delta
        else:
            recovered_text_index = len(remove_sacr_annotations(sacr_content[:sacr_index]))

        sacr_to_recovered_index_dict[sacr_index] = recovered_text_index

    entities_df["byte_onset"] = entities_df["sacr_start_id"].map(sacr_to_recovered_index_dict)
    entities_df["byte_offset"] = entities_df["sacr_end_id"].map(sacr_to_recovered_index_dict)

    # Apply the function to create a new 'text' column
    entities_df["sacr_text"] = entities_df.apply(lambda row: get_mention_text_from_ids(row["byte_onset"], row["byte_offset"], recovered_text), axis=1)

    return entities_df

def get_tokens_start_end(entities_df, tokens_df):
    # Convert tokens byte onset and offset into NumPy arrays for efficient processing
    token_onsets = tokens_df['byte_onset'].values
    token_offsets = tokens_df['byte_offset'].values

    # Precompute masks for each entity
    start_tokens = []
    end_tokens = []

    for byte_onset, byte_offset in entities_df[["byte_onset", "byte_offset"]].values:
        # Efficiently find token range that overlaps with entity using NumPy boolean indexing
        start_mask = token_offsets > byte_onset
        end_mask = token_onsets < byte_offset

        # The tokens that satisfy both conditions are the ones that are part of the entity
        relevant_tokens = np.where(start_mask & end_mask)[0]

        # Get the first and last token
        start_tokens.append(relevant_tokens[0] if len(relevant_tokens) > 0 else -1)  # -1 if no token found
        end_tokens.append(relevant_tokens[-1] if len(relevant_tokens) > 0 else -1)

    # Add the results back to the entities DataFrame
    entities_df["start_token"] = start_tokens
    entities_df["end_token"] = end_tokens

    return entities_df

def reorder_coref_ids(entities_df):
    COREF_column = 'COREF_name'
    
    # Get the most frequent category for each COREF_name
    # PB bcp de valeurs => pas agreg poss
    coref_counts = entities_df.groupby(COREF_column)['cat'].agg(lambda x: x.value_counts().idxmax())

    # Get the count of mentions per COREF_name
    coref_sizes = entities_df[COREF_column].value_counts()

    # Combine the counts and most frequent categories
    grouped_entities_df = pd.DataFrame({
        'Count': coref_sizes,
        'coref_cat': coref_counts
    }).reset_index()

    # Sort by 'Count' to get the coref_name with the most mentions first
    grouped_entities_df.sort_values(by='Count', ascending=False, inplace=True)

    # Use pd.factorize to generate new coref ids
    grouped_entities_df['new_COREF'] = pd.factorize(grouped_entities_df['COREF_name'])[0]

    # Map the old COREF_name to the new COREF id
    COREF_converter = dict(zip(grouped_entities_df[COREF_column], grouped_entities_df['new_COREF']))

    # Assign the new COREF ids back to the entities dataframe
    
    entities_df['COREF'] = entities_df[COREF_column].map(COREF_converter)
    
    return entities_df

def extract_text_for_entities(tokens_df, entities_df, recovered_text):
    # Precompute the byte onset and offset for each token
    tokens_byte_onsets = tokens_df["byte_onset"].values
    tokens_byte_offsets = tokens_df["byte_offset"].values

    # Initialize a list to store the extracted texts
    texts = []

    # Iterate over each entity's start and end token indices
    for start_token, end_token in entities_df[["start_token", "end_token"]].values:
        # Find the start and end byte offsets
        byte_onset = tokens_byte_onsets[start_token]
        byte_offset = tokens_byte_offsets[end_token]

        # Slice the text from the recovered_text using the precomputed offsets
        texts.append(recovered_text[byte_onset: byte_offset])

    # Assign the extracted texts to the DataFrame
    entities_df["text"] = texts
    return entities_df

def generate_tokens_and_entities_from_sacr_enrichi(file_name,
                                           files_directory,
                                           end_directory=None,
                                           spacy_model=None,
                                           max_char_sentence_length=75000,
                                           cat_replace_dict=None,
                                           entity_types=None):
    # print(SACR_file_name)
    if cat_replace_dict is None:
        cat_replace_dict = {"f FAC": "FAC",
                            "g GPE": "GPE",
                            "h HIST": "TIME",
                            "l LOC": "LOC",
                            "m METALEPSE": "PER",
                            "n NO_PER": "PER",
                            "o ORG": "ORG",
                            "p PER": "PER",
                            "t TIME": "TIME",
                            "v VEH": "VEH",
                            "": "_",    # modif si jamais il n'y a pas d'annotation TYPE
                            }
    if spacy_model == None:
        spacy_model = load_spacy_model(model_name='fr_dep_news_trf', model_max_length=500000)

    if end_directory==None:
        end_directory = files_directory

    sacr_file_path = os.path.join(files_directory, file_name)
    if not sacr_file_path.endswith(".sacr"):
        sacr_file_path = sacr_file_path + ".sacr"

    with open(sacr_file_path, "r", encoding="UTF-8") as sacr_file:
        sacr_content = sacr_file.read()


    sacr_content = clean_sacr_content(sacr_content)
    # MODIF == amalgamer les annot

    recovered_text = remove_sacr_annotations(sacr_content)
    # == text sans annot

    entities_df = extract_entities_annotations(sacr_content)
    # MODIF == identifier la 'cat' 
    #print(entities_df)
    print("1- df entities cat")

    entities_df = convert_ids_from_sacr_to_recovered(entities_df, sacr_content, recovered_text)
    print("2- ras")
 
    entities_df["cat"] = entities_df["cat"].map(cat_replace_dict)

    # modif en plus : on propage l'entité nommée sur toute la chaine
    known_cats = entities_df[entities_df["cat"] != "_"]   
    cat_by_coref = (known_cats.groupby("COREF_name")["cat"].agg(lambda x: x.value_counts().index[0]))
    entities_df["cat"] = (entities_df["COREF_name"].map(cat_by_coref).fillna(entities_df["cat"]))

    #print(entities_df["cat"])
    # utiliser le dico pour simplifier étiquette "p PER" -> "PER"
    print("3- ras : catégories propagées par chaîne de coréférence")

    tokens_df = generate_tokens_df(recovered_text, spacy_model, max_char_sentence_length=max_char_sentence_length)
    #print(tokens_df)
    # tokeniser le texte (texte brut sans annot == recovered_text)
    print("4- ras")

    entities_df = get_tokens_start_end(entities_df, tokens_df)
    #print(entities_df["COREF_name"])
    # mettre un id (numerique) par coref_name
    print("5- ras")
        
    entities_df = reorder_coref_ids(entities_df)
    #print(entities_df)
    #ordonner chronologiquement les entités 
    print("6- ras")

    # MODIF
    entities_df = entities_df[['COREF_name', 'COREF', 'start_token', 'end_token', 'cat', 'sacr_text', 'byte_onset', 'byte_offset','annotation']]
    # selectionner les champs du df que l'on veut garder
    print("7- ajout annotation")

    entities_df = extract_text_for_entities(tokens_df, entities_df, recovered_text)

    if entity_types:
        entities_df = entities_df[entities_df["cat"].isin(entity_types)]
    entities_df = add_features_to_entities(entities_df, tokens_df)
    # return entities_df

    # remove tokens after the last sentence with annotated entity // allow to filter partially anotated SACR files, can continue annotations at anny given time
    last_annotated_sentence = tokens_df.loc[entities_df['end_token'].max(), 'sentence_ID']
    tokens_df = tokens_df[tokens_df['sentence_ID'] <= last_annotated_sentence]


    save_text_file(recovered_text, file_name, files_directory=end_directory, extension=".txt")
    save_tokens_df(tokens_df, file_name, files_directory=end_directory, extension=".tokens")
    save_entities_df(entities_df, file_name, files_directory=end_directory, extension=".entities")





