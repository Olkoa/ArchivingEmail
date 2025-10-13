from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize
import nltk
import numpy as np
nltk.download("punkt")
from nltk.tokenize import sent_tokenize

# Modèle polyvalent multilingue
default_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

def semantic_search(query, embeddings, top_k=10, model=None):
    if model is None:
        model = default_model
    
    query_emb = model.encode([query])
    embeddings_norm = normalize(embeddings, axis=1)
    query_emb_norm = normalize(query_emb.reshape(1, -1), axis=1)

    sims = embeddings_norm @ query_emb_norm.T
    sims = sims.flatten()

    top_idx = np.argsort(sims)[::-1][:top_k]
    top_scores = sims[top_idx]
    return top_idx, top_scores

def best_matching_segment(chunk, query, model=None):
    if model is None:
        model = default_model

    sentences = sent_tokenize(chunk)
    if len(sentences) == 1:
        return sentences[0]

    seg_emb = model.encode(sentences)
    q_emb = model.encode([query])
    sims = cosine_similarity(q_emb, seg_emb)[0]
    best_idx = sims.argmax()
    return sentences[best_idx]

def format_results(chunks, scores, top_k=10, max_sents=3):
    display_texts = []
    for i, (chunk, score) in enumerate(zip(chunks[:top_k], scores[:top_k]), 1):
        sentences = sent_tokenize(chunk)
        display_text = " ".join(sentences[:max_sents])
        if len(sentences) > max_sents:
            display_text += " ..."
        display_texts.append(f"{i}. ({score:.3f}) {display_text}")
    return "\n\n".join(display_texts)

def highlight_query_terms(chunk, query):
    """Renvoie le chunk avec les mots du query en rouge gras"""
    words = chunk.split()
    query_words = set(query.lower().split())
    highlighted = []
    for word in words:
        if word.lower() in query_words:
            highlighted.append(f"<span style='color:red;font-weight:bold'>{word}</span>")
        else:
            highlighted.append(word)
    return " ".join(highlighted)
