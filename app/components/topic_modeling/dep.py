import subprocess
import nltk

# Ins tallation des dépendances
subprocess.run(["pip", "install","graphviz","pyclustering","openai", "hf_xet", "spacy", "ijson", "bertopic", "stop_words"], check=True)

# Téléchargement des stopwords NLTK
nltk.download("stopwords")
