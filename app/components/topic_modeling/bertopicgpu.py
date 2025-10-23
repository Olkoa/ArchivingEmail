import json
from bertopic import BERTopic
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction import text
import joblib
import ijson
from bertopic.vectorizers import ClassTfidfTransformer
from nltk.corpus import stopwords
from spacy.lang.fr.stop_words import STOP_WORDS as fr_stop
from spacy.lang.en.stop_words import STOP_WORDS as en_stop
from stop_words import get_stop_words














texts = []
with open("cleaned_emails.json", "r", encoding="utf-8") as f:
    for item in tqdm(ijson.items(f, "item"), desc="Extracting mails"):
        subject = item.get("subject", "")
        body = item.get("body", "")
        texts.append(f"{subject}\n\n{body}")

final_stopwords_list = get_stop_words('english') + get_stop_words('french')+list(fr_stop)+ list(en_stop)+stopwords.words('english') + stopwords.words('french')+['Bonjour', 'bonjour', 'Salut', 'Hello', 'hello', 'bonsoir', 'Bonsoir']
unique_list = list(set(final_stopwords_list))

vectorizer_model = CountVectorizer(stop_words=unique_list)
ctfidf_model = ClassTfidfTransformer(bm25_weighting=True)

# Embedding model (multilingual)
embedding_model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',model_kwargs={"torch_dtype":"bfloat16"})

# Define BERTopic
topic_model = BERTopic(
    embedding_model=embedding_model,
    language="multilingual",
    verbose=False,
    calculate_probabilities=True,
    ctfidf_model=ctfidf_model,
    nr_topics="auto",
    top_n_words=20,
    #min_topic_size=10,
    n_gram_range=(1, 2),
    vectorizer_model=vectorizer_model,
    seed_topic_list=[
    ["archive", "archiviste", "documents", "dossier", "catalogue"],
    ["histoire", "historique", "patrimoine", "mémoire", "manuscrit"],
    ["classement", "tri", "organisation", "conservation", "indexation"],
    ["accès", "consultation", "lecture", "données", "fichier"],
    ["AAF","SIAF","aaf","siaf"],
    ["bibliothèque", "registre", "répertoire", "stockage", "référencement"]
]
)
embeddings = embedding_model.encode(texts, show_progress_bar=True, batch_size=64)
# Fit model
topics, probs = topic_model.fit_transform(texts,embeddings)


joblib.dump(embeddings, "embeddings_fr.pkl")


# Save everything
topic_model.save("bertopic_model_fr")
joblib.dump(texts, "texts_fr.pkl")
joblib.dump(probs, "probs_fr.pkl")

import numpy as np
import pandas as pd

probs = np.array(probs)

# Get the probability corresponding to the assigned topic for each email
topics_arr = np.array(topics)
main_probs = np.where(topics_arr != -1, probs[np.arange(len(topics)), topics_arr], 0.0)


# Now it's 1D — safe to save
df = pd.DataFrame({
    "text": texts,
    "topic": topics,
    "probability": main_probs
})
df.to_csv("bertopic_output.csv", index=False)

# Print topic summary
print(topic_model.get_topic_info())

import pandas as pd
from bertopic import BERTopic
topic_model = BERTopic.load("bertopic_model_fr")
df = pd.read_csv("bertopic_output.csv")

# Get mapping from topic ID to representative label (top words)
topic_labels = {
    topic: ", ".join([word for word, _ in topic_model.get_topic(topic)[:3]])  # top 3 words
    for topic in df["topic"].unique() if topic != -1
}
topic_df = pd.DataFrame([
    {"topic_id": topic, "label": label}
    for topic, label in topic_labels.items()
])
topic_df.to_csv("topic_labels.csv", index=False)