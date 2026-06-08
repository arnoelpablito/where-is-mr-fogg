from multiprocessing import freeze_support

from propp_fr import process_text_file


def main():
    src = "Model_TDM/data/SACR/all_annots.sacr.txt"
    outdir = "Model_TDM/data/PROPP/new_txt"
    name = "tdm_auto_chap1to5"

    txt = outdir + "/" + name + ".txt"

    with open(src, "r", encoding="utf-8") as f:
        text = f.read()

    with open(txt, "w", encoding="utf-8") as f:
        f.write(text)

    process_text_file(txt)


if __name__ == "__main__":
    freeze_support()
    main()