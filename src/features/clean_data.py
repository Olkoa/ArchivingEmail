from pathlib import Path
import mailparser
import json
from tqdm import tqdm
from warnings import filterwarnings
import trafilatura
from cleantext import clean
from bs4 import BeautifulSoup
import re
import nltk
from nltk.corpus import stopwords
import spacy
from langdetect import detect

print("Packages loaded")

filterwarnings("ignore", category=UserWarning)
nltk.download('stopwords', quiet=True)

# --------------------------
# Stopwords et listes utiles
# --------------------------
stop_words = set(stopwords.words('english'))
stop_words.update(stopwords.words('french'))
stop_words.update(stopwords.words('german'))

extra_stopwords = {
    "i","le","et","la","du","des","vous","je","au","aux","les","en","un","une",
    "de","pour","avec","se","sur","par","dans","que","qui"
}
stop_words.update(extra_stopwords)


nlp_fr = spacy.load("fr_core_news_sm")
nlp_en = spacy.load("en_core_web_sm")
nlp_de = spacy.load("de_core_news_sm")


politeness_words = {
    "bonjour","bonsoir","merci","cordialement","amicalement","bien","salutations",
    "bonne","journée","soirée","salut","hello","thanks","regards","sincèrement"
}

common_firstnames = {
    "anne","céline","claire","laurent","nicolas","vincent","olivier","pierre",
    "marie","jean","pauline","dominique","charles","alice","gilles","thomas",
    "frédéric","julien","catherine","florence","benedicte","victor","raphaelle",
    "xavier","marion","lucile","helene","paul", "raphaëlle", "laure", "clerc", 
    "charly", "guyon", "bernard", "myriam","pascal", "elisabeth"
}

useless_words = {
    "afin","effet","sous","tous","toute","très","plus","donc","comme","aussi",
    "entre","cela","peut","faire","part","deux","encore","ainsi","avant","après",
    "chaque","suite","vers","lors","prochainement","toujours","ensuite"
}

# --------------------------
# Fonctions utilitaires
# --------------------------
def remove_noise_words(tokens):
    return [t for t in tokens 
            if t not in politeness_words 
            and t not in common_firstnames 
            and t not in useless_words]

def lemmatize_tokens(tokens, lang="fr"):
    if lang == "fr":
        doc = nlp_fr(" ".join(tokens))
    elif lang == "en":
        doc = nlp_en(" ".join(tokens))
    elif lang == "de":
        doc = nlp_de(" ".join(tokens))
    else:
        return tokens  
    return [token.lemma_ for token in doc if token.is_alpha]

def extract_clean_text(raw_body):
    """Extrait et nettoie le texte d'un mail HTML ou brut."""
    clean_body = trafilatura.extract(raw_body, include_comments=False, include_tables=False)
    if not clean_body:
        soup = BeautifulSoup(raw_body, "html.parser")
        clean_body = soup.get_text(separator=" ", strip=True)

    text = clean(clean_body, fix_unicode=True, to_ascii=False, lower=True,
                 no_line_breaks=False, no_urls=True, no_emails=True)
    text = re.sub(r"<.*?>", "", text)
    text = re.sub(r"\s+", " ", text).strip()

    tokens = re.findall(r"\b\w+\b", text.lower())

    tokens = [t for t in tokens if t not in stop_words and len(t) > 3]
    tokens = remove_noise_words(tokens)

    lang = "fr"
    try:
        lang_detected = detect(" ".join(tokens))
        if lang_detected.startswith("fr"):
            lang = "fr"
        elif lang_detected.startswith("en"):
            lang = "en"
        elif lang_detected.startswith("de"):
            lang = "de"
    except:
        pass

    tokens = lemmatize_tokens(tokens, lang)

    final_text = " ".join(tokens)

    final_text = re.sub(r"(envoyé depuis mon iphone|sent from my iphone|outlook)", "", final_text)

    if any(len(word) > 25 for word in final_text.split()):
        return ""

    return final_text

# --------------------------
# Code de parsing et sauvegarde (uniquement si script exécuté directement)
# --------------------------
if __name__ == "__main__":
    base_dir = Path(__file__).parent.parent

    import os
    from dotenv import load_dotenv
    load_dotenv()
    ACTIVE_PROJECT = os.getenv("ACTIVE_PROJECT")

    eml_root_folder = base_dir / "data" / "Projects" / ACTIVE_PROJECT
    if not eml_root_folder.exists():
        raise FileNotFoundError(f"Dossier non trouvé : {eml_root_folder}")

    output_folder = base_dir / "data" / "projects" / ACTIVE_PROJECT
    output_folder.mkdir(parents=True, exist_ok=True)
    output_file = output_folder / "all_cleaned_mails.json"

    all_mails = []
    number_error = 0
    eml_files = sorted(eml_root_folder.rglob("*.eml"))

    print(f"Parsing {len(eml_files)} mails ...")
    for eml_file in tqdm(eml_files, desc="Parsing mails"):
        try:
            mail = mailparser.parse_from_file(str(eml_file))
            body = mail.body or ""
            text = extract_clean_text(body)
            if not text:
                continue
            mail_data = {
                "file": eml_file.name,
                "folder": str(eml_file.parent.relative_to(eml_root_folder)),
                "from": mail.from_,
                "to": mail.to,
                "subject": mail.subject or "",
                "date": mail.date.isoformat() if mail.date else None,
                "body": text,
            }
            all_mails.append(mail_data)
        except Exception as e:
            number_error += 1
            print(f"Erreur pour {eml_file}: {e}")

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_mails, f, ensure_ascii=False, indent=4)

    print(f"\nNombre total de mails importés : {len(all_mails)}")
    print(f"Nombre total d'erreurs : {number_error}")
    print(f"{len(all_mails)} mails sauvegardés dans {output_file}")