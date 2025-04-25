import pandas as pd
import os
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter

import re
import html
import unicodedata

import tqdm

from sklearn.cluster import KMeans
from sklearn.manifold import TSNE
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction import text

from sklearn.manifold import TSNE
import plotly.express as px  # Add this import for Plotly


# Or if that doesn't work, try this (adjust path as needed):
import sys
sys.path.append('..')  # Add current directory to path

# ----- LLM Cluster Labeling -----
from src.llm.openrouter import openrouter_llm_api_call
import random


# Define the project and path
ACTIVE_PROJECT = "Projet Demo"
# embeddings_path = os.path.join('data', "Projects", ACTIVE_PROJECT, 'emails_with_embeddings_sample.pkl')
embeddings_path = os.path.join('data', "Projects", ACTIVE_PROJECT, 'emails_with_embeddings_improved.pkl')


# Load the data
df = pd.read_pickle(embeddings_path)
print(f"DataFrame shape: {df.shape}")
print(f"\nColumns: {df.columns.tolist()}")

# Check how many emails have embeddings
has_embeddings = df['embeddings'].notna()
embedding_count = has_embeddings.sum()
empty_count = (~has_embeddings).sum()

print(f"Emails with embeddings: {embedding_count} ({embedding_count/len(df):.2%})")
print(f"Emails without embeddings: {empty_count} ({empty_count/len(df):.2%})")


df_emails_with_embeddings = df[has_embeddings]
df_emails_with_embeddings.shape



def preprocess_email_text(text):
    """Applies all preprocessing steps to an email body text"""
    if pd.isna(text) or not isinstance(text, str):
        return ""

    # Step 1: Clean formatting issues
    # Decode HTML entities (like &nbsp;)
    text = html.unescape(text)

    # Normalize Unicode (convert different forms to standard form)
    text = unicodedata.normalize('NFKC', text)

    # Replace problematic non-breaking spaces with regular spaces
    text = text.replace('\xa0', ' ')

    # Convert multiple spaces to single space
    text = re.sub(r'\s+', ' ', text)

    # Remove extra line breaks
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)

    text = text.strip()

    # Step 2: Remove nested conversations
    # Common email forwarding/reply patterns
    patterns = [
        r'-----Original Message-----.*',
        r'From:.*?Sent:.*?To:.*?Subject:.*?',
        r'De\s*:.*?Envoyé\s*:.*?À\s*:.*?',  # French version
        r'Von:.*?Gesendet:.*?An:.*?Betreff:.*?',  # German version
        r'On.*wrote:.*',
        r'Le.*a écrit :.*',  # French version
        r'>.*',  # Quoted text in replies
    ]

    # Try to find the first occurrence of any pattern
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            # Keep only the text before the nested content
            text = text[:match.start()].strip()

    # Step 3: Truncate at sentence end
    max_length = 8000
    if len(text) <= max_length:
        return text

    # Cut at max_length
    truncated = text[:max_length]

    # Find the last sentence boundary (., !, ?)
    sentence_ends = list(re.finditer(r'[.!?]["\'\)\]]?\s+', truncated))
    if sentence_ends:
        # Use the position of the last found sentence end
        last_end = sentence_ends[-1]
        return truncated[:last_end.end()].strip()

    # If there are no sentence boundaries at all, just return the truncated text
    return truncated.strip()


df_emails_with_embeddings['processed_body'] = df_emails_with_embeddings['body'].apply(preprocess_email_text)


# Assuming df is your DataFrame with the embeddings column

# Define a function to extract just the embedding array
def extract_embedding_values(embedding_obj):
    if pd.isna(embedding_obj):
        return None

    # Check if the embedding is a dictionary with the 'embedding' key
    if isinstance(embedding_obj, dict) and 'embedding' in embedding_obj:
        return embedding_obj['embedding']

    # Return the embedding as-is if it's already just the array
    return embedding_obj

# Apply the function to create the new column
df_emails_with_embeddings['embeddings_values'] = df_emails_with_embeddings['embeddings'].apply(extract_embedding_values)

# Verify the new column
if not df_emails_with_embeddings['embeddings_values'].isna().all():
    print(f"Successfully extracted embedding values with shape: {len(df_emails_with_embeddings['embeddings_values'].dropna().iloc[0])}")
else:
    print("No valid embeddings were found")


def convert_embedding_to_array(embedding):
    if pd.isna(embedding):
        return None
    if isinstance(embedding, dict) and 'embedding' in embedding:
        return embedding['embedding']
    return embedding


# ----- Cluster naming using TF-IDF -----
def get_top_keywords_per_cluster(docs, labels, top_n=30):
    # Ensure docs and labels have the same length
    if len(docs) != len(labels):
        min_len = min(len(docs), len(labels))
        docs = docs[:min_len]
        labels = labels[:min_len]
        print(f"Warning: Truncated data to {min_len} samples to match lengths")

    cluster_names = {}
    # Store frequent words for each cluster for LLM processing
    cluster_freq_words = {}

    for cluster_id in sorted(set(labels)):
        cluster_docs = [docs[i] for i in range(len(docs)) if labels[i] == cluster_id]

        # Convert frozenset to list for stop_words parameter
        french_stop_words = list(text.ENGLISH_STOP_WORDS) + [
            "cette", "cet", "ces", "ça", "ce" "où", "être", "avoir", "aussi", "comme",
            "plus", "moins", "très", "sans", "entre", "leur", "leurs", "donc",
            "ainsi", "etc", "que", "quel", "quelle", "quelles", "quels", "tout", "toute", "toutes",
            "je", "tu", "il", "elle", "nous", "vous", "ils", "elles",
            "mon", "ma", "mes", "me", "ton", "ta", "tes", "son", "sa", "ses",
            "notre", "nos", "votre", "vos", "bonjour", "et", "est", "aïe",
            "lui", "y", "en", "le", "la", "les", "un", "une", "des",
            "du", "de", "d'", "à", "au", "aux", "pour", "par", "avec",
            "sous", "sur", "dans", "vers", "depuis", "avant",
            "après", "parmi", "contre", "selon", "malgré", "auprès",
            "au-delà", "envers", "à travers", "auprès de",
            "à côté de", "en dehors de", "à l'intérieur de", "au lieu de",
            "1", "2", "3", "4", "5", "6", "7", "8", "9", "0",
            "10", "11", "12", "13", "14", "15", "16", "17", "18", "19",
            "20", "21", "22", "23", "24", "25", "26", "27", "28", "29",
            "30", "31", "32", "33", "34", "35", "36", "37", "38", "39",
            "40", "41", "42", "43", "44", "45", "46", "47", "48", "49",
            "50", "51", "52", "53", "54", "55", "56", "57", "58", "59",
            "60", "61", "62", "63", "64", "65", "66", "67", "68", "69",
            "70", "71", "72", "73", "74", "75", "76", "77", "78", "79",
            "80", "81", "82", "83", "84", "85", "86", "87", "88", "89",
            "90", "91", "92", "93", "94", "95", "96", "97", "98", "99",
            "00", "000", "0000", "00000", "000000", "0000000",
            "01", "02", "03", "04", "05", "06", "07", "08", "09",
            "merci", "bonsoir", "salut", "bien", "oui", "non", "peut-être",
            "s'il", "moi", "toi", "elle",
            "eux", "toi-même", "lui-même", "elle-même",
            "pas", "ne", "ni", "aucun", "aucune", "nul", "nulle",
            "rien", "personne", "quelqu'un", "quelque chose",
            "anne", "org", "com", "fr", "net", "info", "biz", "eu", "co",
            "uk", "it", "es", "de", "jp", "cn", "ru", "br", "in",
            "au", "ca", "mx", "za", "kr", "se", "no", "fi", "dk",
            "pl", "cz", "sk", "hu", "ro", "bg", "gr", "tr", "il",
            "ae", "sa", "qa", "kw", "om", "bh", "eg", "ma", "dz",
            "tn", "ly", "jo", "lb", "sy", "ye", "iq", "ir", "pk",
            "af", "bd", "lk", "np", "mm", "kh", "la", "vn", "th",
            "my", "sg", "ph", "hk", "tw", "jp", "kr", "au", "nz",
            "us", "ca", "mx", "br", "ar", "cl", "co", "pe", "ve",
            "ec", "uy", "py", "bo", "py", "do", "ht", "jm", "tt",
            "bz", "cr", "gt", "hn", "ni", "sv", "pa", "cu", "pr",
            "ai", "ce", "www", "http", "https", "ftp", "mailto", "telnet",
            "tel", "fax", "sms", "mms", "wap", "web", "www2", "www3",
            "marie", "jean", "paul", "pierre", "jacques", "sophie",
            "laurent", "nicolas", "françois", "philippe", "isabelle",
            "laura", "luc", "louis", "marc", "olivier", "vincent",
            "laurent", "catherine", "sylvie", "valérie", "caroline",
            "audrey", "céline", "marion", "claire", "sandra",
            "nathalie", "christine", "dominique", "elodie", "amelie",
            "audrey", "marie", "laurence", "sophie", "isabelle",
            "valérie", "caroline", "audrey", "marion", "claire",
            "sandra", "nathalie", "christine", "dominique", "elodie",
            "amelie", "laurence", "marie", "jean", "paul", "rue", "qui",
            "tous", "toutes", "tout", "toute", "tous", "toutes",
            "beaucoup", "mais", "bon", "aaf", "ok", "jégo", "semb",
            "suis", "sont", "sait", "sais", "savoir", "savoir-faire",
            "savoir-vivre", "savoir-être", "savoir-faire", "savoir-vivre",
            "savoir-être", "savoir-faire", "savoir-vivre", "savoir-être",
            "semble", "sembler",
            "ou", "si", "bonne", "français", "qu", "faire", "cela", "jégo75013", "était", "laure",
            "paristél", "français8", "orghttps", "lundi", "mardi", "mercredi", "jeudi", "vendredi",
            "samedi", "dimanche", "janvier", "février", "mars", "avril", "mai", "juin", "juillet",
            "août", "septembre", "octobre", "novembre", "décembre", "année", "mois", "semaine",
            "jour", "heure", "minute", "seconde", "avant-hier", "hier", "aujourd'hui", "demain",
            "après-demain", "peut", "pourquoi", "comment", "où", "quand", "qui", "que", "quoi",
            "te", "hélène", "end", "amarie",
            "fin", "daniel", "week", "bernard", "aff", "75013", "pourrait", "violaine",
            "céline"
        ]

        # Handle empty cluster case
        if not cluster_docs:
            cluster_freq_words[cluster_id] = []
            continue

        try:
            tfidf = TfidfVectorizer(stop_words=french_stop_words, max_features=1000)
            tfidf_matrix = tfidf.fit_transform(cluster_docs)
            summed = tfidf_matrix.sum(axis=0)
            top_indices = np.argsort(summed.A1)[::-1][:top_n]
            keywords = [tfidf.get_feature_names_out()[i] for i in top_indices]
            cluster_freq_words[cluster_id] = keywords
        except Exception as e:
            print(f"Error processing cluster {cluster_id}: {e}")
            cluster_freq_words[cluster_id] = []

    return cluster_freq_words


# Load your DataFrame with embeddings
# df_emails_with_embeddings = pd.read_pickle('data/Projects/Projet Demo/emails_with_embeddings.pkl')

# First, let's extract the embeddings into a proper numpy array

# Create embeddings_values column if it doesn't exist
if 'embeddings_values' not in df_emails_with_embeddings.columns:
    df_emails_with_embeddings['embeddings_values'] = df_emails_with_embeddings['embeddings'].apply(convert_embedding_to_array)

# Filter out rows with None/NaN embeddings
valid_embeddings_mask = df_emails_with_embeddings['embeddings_values'].notna()
filtered_df = df_emails_with_embeddings[valid_embeddings_mask].copy()

print(f"Working with {len(filtered_df)} emails that have valid embeddings")


# Convert the list of embeddings to a numpy array for clustering
embeddings_array = np.array(filtered_df['embeddings_values'].tolist())

# ----- Clustering -----
n_clusters = 8
kmeans = KMeans(n_clusters=n_clusters, random_state=42)
# Get raw cluster IDs from KMeans
raw_cluster_ids = kmeans.fit_predict(embeddings_array)

# Convert to strings in a consistent way - this ensures we use the same format throughout the pipeline
clusters_id_list = [str(int(cluster_id)) for cluster_id in raw_cluster_ids]

print("Cluster distribution:")
print(pd.Series(clusters_id_list).value_counts())

# Add cluster labels back to the DataFrame
filtered_df['cluster_id'] = clusters_id_list


# Get email texts from the filtered DataFrame
# IMPORTANT: Make sure cluster_labels_list and clusters_id_list are the same
email_texts = filtered_df["body"].tolist()

# CRITICAL FIX: This is a potential source of the problem
# Previously, two different cluster ID lists were used:
# 1. clusters_id_list (from KMeans directly)
# 2. cluster_labels_list (from filtered_df['cluster_id'])
# These should be identical, but let's verify

cluster_labels_list = filtered_df["cluster_id"].tolist()

# Debug: Check if these are actually the same
print("\n===== DEBUG: CHECKING CLUSTER ID CONSISTENCY =====")
print(f"Length of clusters_id_list (from KMeans): {len(clusters_id_list)}")
print(f"Length of cluster_labels_list (from DataFrame): {len(cluster_labels_list)}")

# Check a small sample for equality
sample_size = min(10, len(clusters_id_list))
print(f"\nComparing first {sample_size} elements:")
for i in range(sample_size):
    if i < len(clusters_id_list) and i < len(cluster_labels_list):
        print(f"  {i}: KMeans={clusters_id_list[i]}, DataFrame={cluster_labels_list[i]}, Equal={clusters_id_list[i]==cluster_labels_list[i]}")

# CRITICAL FIX: Use ONE consistent list for cluster IDs
# For this fix, we'll rely on clusters_id_list from KMeans and ignore cluster_labels_list
print("\nUsing clusters_id_list from KMeans for consistency")
print("===== END DEBUG =====\n")

# Get cluster names and frequent words - use the KMeans clusters_id_list
cluster_freq_words = get_top_keywords_per_cluster(email_texts, clusters_id_list)
print(cluster_freq_words)



def get_labels_from_llm(email_texts, clusters_id_list, freq_words_dict, mails_read_by_cluster=20):
    # Prepare all clusters data for a single prompt
    all_clusters_info = {}

    for cluster_id in freq_words_dict:
        # Get sample emails for this cluster and shuffle them
        cluster_mails_indices = [i for i in range(len(email_texts))
                                if clusters_id_list[i] == cluster_id]
        # Shuffle the indices to get random emails
        # REMOVING SHUFFLING TO EXECUTE IT AT START OF DF LOADING
        # random.shuffle(cluster_mails_indices)
        # Take only up to mails_read_by_cluster emails
        cluster_mails = [email_texts[i] for i in cluster_mails_indices[:mails_read_by_cluster]]

        # Store the data for this cluster
        all_clusters_info[cluster_id] = {
            "freq_words": freq_words_dict[cluster_id],
            "sample_mails": cluster_mails
        }

    system_prompt = fr"""You are a french language expert tasked with attributing labels to multiple TF-IDF clusters at once.
    The clusters data can be found between the tags <clusters_data></clusters_data>.
    Each cluster has its frequent words and sample emails to help you find appropriate labels.

    To execute your task perfectly, you MUST follow these rules exactly:

    <rules>
    1. You must return ONLY a valid JSON object with NO additional text before or after.
    2. The JSON must use double quotes (") not single quotes (').
    3. Every cluster ID must be a string key in the JSON like "0", "1", etc.
    4. Every label must be a short French phrase (1-4 words).
    </rules>

    DO NOT include any explanation or other text in your response. ONLY return the JSON object.
    """

    # Build a single user prompt with all clusters
    user_prompt = "<clusters_data>\n"

    for cluster_id, data in all_clusters_info.items():
        user_prompt += f"CLUSTER {cluster_id}:\n"
        user_prompt += f"Frequent words: {data['freq_words']}\n"
        user_prompt += "Sample emails:\n"

        for i, mail in enumerate(data['sample_mails']):
            # Truncate long emails to prevent token explosion
            truncated_mail = mail[:300] + "..." if len(mail) > 300 else mail
            user_prompt += f"- Email {i+1}: {truncated_mail}\n"

        user_prompt += "\n---\n\n"

    user_prompt += "</clusters_data>"

    model = "google/gemini-flash-1.5"

    # Call the LLM API once with all clusters
    response = openrouter_llm_api_call(system_prompt, user_prompt, model)
    print(f"LLM response: {response}")
    print(type(response))
    # Parse the JSON response
    try:
        import json
        llm_labels = json.loads(response)
        print(f"Successfully obtained labels for {len(llm_labels)} clusters at once")
    except json.JSONDecodeError:
        print("Error parsing LLM response as JSON.")
        return False
        # # Fallback to basic labels
        # llm_labels = {str(cluster_id): f"Groupe {cluster_id}" for cluster_id in freq_words_dict.keys()}

    return llm_labels


# ----- LLM Cluster Labeling -----

# CRITICAL FIX: Ensure we're using the correct cluster ID list
print("\n===== DEBUG: PREPARING TO GET LLM LABELS =====")
print(f"Using clusters_id_list for consistency with KMeans results")
print(f"Length of email_texts: {len(email_texts)}")
print(f"Length of clusters_id_list: {len(clusters_id_list)}")
print(f"Number of keys in cluster_freq_words: {len(cluster_freq_words)}")
print("===== END DEBUG =====\n")

# Get LLM-generated labels for each cluster - use consistent clusters_id_list from KMeans
llm_cluster_labels = get_labels_from_llm(email_texts, clusters_id_list, cluster_freq_words)
print(llm_cluster_labels)


# When mapping to cluster names, convert float->int->str
filtered_df['cluster_name'] = filtered_df['cluster_id'].map(llm_cluster_labels)
print(filtered_df['cluster_name'].value_counts())

# Store clean LLM labels separately (without the keywords)
clean_llm_labels = {k: v for k, v in llm_cluster_labels.items()}


# ----- TSNE -----
# Adjust perplexity based on the number of data points
perplexity = min(30, max(5, len(filtered_df) // 10))
print(f"Using TSNE with perplexity={perplexity}")

tsne = TSNE(n_components=2, random_state=42, perplexity=perplexity)
embeddings_2d = tsne.fit_transform(embeddings_array)


# Create a function to verify consistency of cluster IDs and names
def verify_cluster_consistency(df, id_column, name_column, label=""):
    print(f"\n===== VERIFYING CLUSTER CONSISTENCY {label} =====")
    print(f"DataFrame shape: {df.shape}")
    print(f"Number of unique cluster IDs: {df[id_column].nunique()}")
    print(f"Number of unique cluster names: {df[name_column].nunique()}")

    # Check if there's a 1-to-1 mapping between IDs and names
    id_to_name_map = df.groupby(id_column)[name_column].first().to_dict()
    print("\nMapping from cluster ID to name:")
    for cluster_id, name in id_to_name_map.items():
        print(f"  Cluster ID '{cluster_id}' -> '{name}'")
        # Count how many emails have this cluster ID
        count = len(df[df[id_column] == cluster_id])
        print(f"    Count: {count} emails")

    # Check for any inconsistencies
    inconsistent = df.groupby(id_column)[name_column].nunique() > 1
    if inconsistent.any():
        print("\nWARNING: Some cluster IDs map to multiple names:")
        for cluster_id in inconsistent[inconsistent].index:
            names = df[df[id_column] == cluster_id][name_column].unique()
            print(f"  Cluster ID '{cluster_id}' has multiple names: {names}")
            # Show sample rows with this inconsistency
            sample_rows = df[df[id_column] == cluster_id].sample(min(5, len(df[df[id_column] == cluster_id])))
            print(f"  Sample rows with cluster_id '{cluster_id}':")
            for _, row in sample_rows.iterrows():
                print(f"    {row[id_column]} -> {row[name_column]}")
    else:
        print("\nAll cluster IDs consistently map to a single name.")

    # Check if all cluster names appear exactly once in the mapping
    name_counts = pd.Series(list(id_to_name_map.values())).value_counts()
    if (name_counts > 1).any():
        print("\nWARNING: Some cluster names are mapped to multiple IDs:")
        for name, count in name_counts[name_counts > 1].items():
            print(f"  Cluster name '{name}' is mapped to {count} different IDs")
            # Find the IDs that map to this name
            ids = [k for k, v in id_to_name_map.items() if v == name]
            print(f"  IDs: {ids}")

    # Check for NaN or empty values
    print(f"\nRows with NaN in {id_column}: {df[id_column].isna().sum()}")
    print(f"Rows with NaN in {name_column}: {df[name_column].isna().sum()}")

    print("===== END VERIFICATION =====\n")

# ===== DEBUG: Print LLM labels map =====
print("\n===== DEBUG: LLM CLUSTER LABELS =====")
print(f"Type of llm_cluster_labels: {type(llm_cluster_labels)}")
for cluster_id, label in llm_cluster_labels.items():
    print(f"Cluster ID '{cluster_id}' -> '{label}'")
print("===== END DEBUG =====\n")

# Apply cluster mapping to filtered dataframe
print("\n===== DEBUG: APPLYING CLUSTER NAMES TO FILTERED DF =====")
print(f"filtered_df shape before: {filtered_df.shape}")
print(f"filtered_df['cluster_id'] unique values: {filtered_df['cluster_id'].unique()}")

filtered_df['cluster_name'] = filtered_df['cluster_id'].map(llm_cluster_labels)
print(f"filtered_df['cluster_name'] after mapping: {filtered_df['cluster_name'].value_counts().to_dict()}")
print("===== END DEBUG =====\n")

# Verify consistency in the filtered dataframe
verify_cluster_consistency(filtered_df, 'cluster_id', 'cluster_name', "FILTERED DF")

# Save the results to the main DataFrame
print("\n===== DEBUG: UPDATING MAIN DATAFRAME =====")
print(f"main df shape: {df_emails_with_embeddings.shape}")
print(f"valid_embeddings_mask True count: {valid_embeddings_mask.sum()}")

df_emails_with_embeddings['cluster_id'] = np.nan
df_emails_with_embeddings.loc[valid_embeddings_mask, 'cluster_id'] = clusters_id_list

# Let's check if we correctly assigned cluster_ids
print(f"df_emails_with_embeddings['cluster_id'] non-NaN count: {df_emails_with_embeddings['cluster_id'].notna().sum()}")
print(f"df_emails_with_embeddings['cluster_id'] unique values: {df_emails_with_embeddings['cluster_id'].dropna().unique()}")

# Check if the mapping dictionary has all required keys
for cluster_id in df_emails_with_embeddings['cluster_id'].dropna().unique():
    if cluster_id not in llm_cluster_labels:
        print(f"WARNING: Cluster ID '{cluster_id}' is not in llm_cluster_labels dictionary!")

# Apply mapping
df_emails_with_embeddings['cluster_name'] = df_emails_with_embeddings['cluster_id'].map(llm_cluster_labels)
print(f"df_emails_with_embeddings['cluster_name'] value counts: {df_emails_with_embeddings['cluster_name'].value_counts().to_dict()}")
print("===== END DEBUG =====\n")

# Verify consistency in the main dataframe (only for rows with valid embeddings)
valid_rows = df_emails_with_embeddings.dropna(subset=['cluster_id'])
verify_cluster_consistency(valid_rows, 'cluster_id', 'cluster_name', "MAIN DF (VALID ROWS)")

# Save the dataframe with clusters
df_emails_with_embeddings.to_pickle('data/Projects/Projet Demo/emails_with_clusters.pkl')



# ----- Plotly Interactive Visualization with Discrete Color Scale -----
print("\n===== DEBUG: PREPARING VISUALIZATION DATA =====")
print(f"Number of data points: {len(embeddings_2d)}")
print(f"Number of cluster IDs: {len(clusters_id_list)}")

# Create a mapping dictionary from cluster_id to cluster_name
print("\nCreating mapping from cluster IDs to names...")
cluster_name_mapping = {}
for cluster_id, cluster_name in clean_llm_labels.items():
    cluster_name_mapping[cluster_id] = cluster_name
    print(f"  Mapping: '{cluster_id}' -> '{cluster_name}'")

# Check if all cluster IDs have a corresponding name
for unique_id in set(clusters_id_list):
    if unique_id not in cluster_name_mapping:
        print(f"  WARNING: Cluster ID '{unique_id}' has no name in the mapping dictionary!")

# ===== KEY FIX: THE PROBLEM SEEMS TO BE HERE =====
# Let's debug by checking a sample of emails and their assigned clusters
num_samples = min(10, len(clusters_id_list))
print(f"\nSampling {num_samples} emails to check cluster assignments:")
for i in range(num_samples):
    email_id = filtered_df.index[i]
    email_subject = filtered_df.iloc[i]['subject'] if 'subject' in filtered_df.columns else f"Email {i}"
    cluster_id = clusters_id_list[i]
    cluster_name = cluster_name_mapping.get(cluster_id, f"Unlabeled {cluster_id}")
    print(f"  Email {i} (ID: {email_id})")
    print(f"    Subject: {email_subject[:50]}..." if len(str(email_subject)) > 50 else f"    Subject: {email_subject}")
    print(f"    Cluster ID: {cluster_id}")
    print(f"    Cluster Name: {cluster_name}")

# Debug: Compare embeddings shape with dataframe rows
print(f"\nShape of embeddings_2d: {embeddings_2d.shape}")
print(f"Length of clusters_id_list: {len(clusters_id_list)}")
print(f"Number of rows in filtered_df: {len(filtered_df)}")

# ===== CRITICAL FIX: Store a copy of the original cluster IDs =====
# This ensures we preserve the exact same order for visualization
original_cluster_ids = clusters_id_list.copy()

# Ensure each data point has the correct cluster name
cluster_names = []
for cluster_id in original_cluster_ids:
    assigned_name = cluster_name_mapping.get(cluster_id, f"Unlabeled {cluster_id}")
    cluster_names.append(assigned_name)

# Create the DataFrame for plotly with consistent cluster names
tsne_df = pd.DataFrame({
    'TSNE1': embeddings_2d[:, 0],
    'TSNE2': embeddings_2d[:, 1],
    'cluster_id': original_cluster_ids,  # Use the preserved list
    'cluster_name': cluster_names,
    'email_id': filtered_df.index.tolist(),  # Store the original email IDs
    'subject': filtered_df['subject'].values if 'subject' in filtered_df.columns else [f"Email {i}" for i in range(len(embeddings_2d))]
})

# Verify consistency in the visualization DataFrame
verify_cluster_consistency(tsne_df, 'cluster_id', 'cluster_name', "VISUALIZATION DF")

# Create an interactive scatter plot with the cluster names as the color groups
print("\nCreating interactive plot...")
fig = px.scatter(
    tsne_df,
    x='TSNE1',
    y='TSNE2',
    color='cluster_name',  # Use the actual cluster names for coloring
    hover_data=['subject', 'cluster_id', 'email_id'],  # Add email_id to hover data for debugging
    title='Interactive Email Clusters (TSNE)',
    color_discrete_sequence=px.colors.qualitative.Vivid,
    labels={'cluster_name': 'Clusters'}
)

print("===== END DEBUG =====\n")

# CRITICAL FIX: Ensure all data in customdata is properly formatted as strings
print("\n===== DEBUG: PREPARING HOVER DATA =====")
# Check for any non-string data that might cause issues
print(f"Subject column type: {type(tsne_df['subject'].iloc[0])}")
print(f"Cluster ID column type: {type(tsne_df['cluster_id'].iloc[0])}")
print(f"Email ID column type: {type(tsne_df['email_id'].iloc[0])}")
print(f"Cluster name column type: {type(tsne_df['cluster_name'].iloc[0])}")

# Convert all data to strings for display
customdata = np.column_stack((
    tsne_df['subject'].astype(str),
    tsne_df['cluster_id'].astype(str),  # Ensure cluster_id is string
    tsne_df['email_id'].astype(str),
    tsne_df['cluster_name'].astype(str)
))
print(f"Customdata shape: {customdata.shape}")
print("===== END DEBUG =====\n")

# Update hover template to show more detailed information for debugging
fig.update_traces(
    hovertemplate="<b>Email:</b> %{customdata[0]}<br><b>Cluster ID:</b> %{customdata[1]}<br><b>Email ID:</b> %{customdata[2]}<br><b>Cluster Name:</b> %{customdata[3]}<extra></extra>",
    customdata=customdata
)

# Improve layout with better legend positioning and formatting
fig.update_layout(
    legend_title_text='Clusters',
    xaxis_title='TSNE Dimension 1',
    yaxis_title='TSNE Dimension 2',
    legend=dict(
        title_font=dict(size=14),
        font=dict(size=12),
        itemsizing='constant',  # Make legend items consistent size
        orientation='v',  # Vertical orientation
        yanchor="top",
        y=1.0,
        xanchor="right",
        x=1.15,  # Position legend outside the plot area
        bordercolor="Black",
        borderwidth=1
    ),
    # Make the plot area slightly smaller to accommodate the legend
    margin=dict(r=150),  # Add right margin for legend
)

# ===== ADD CRUCIAL DEBUGGING AND VALIDATION STEP =====
# This saves the visualization data with all the metadata needed to inspect individual points
# We'll write to CSV file for easy inspection
print("\n===== SAVING VISUALIZATION DATA FOR VALIDATION =====")
tsne_df.to_csv('tsne_visualization_data.csv', index=False)
print("Saved visualization data to tsne_visualization_data.csv for manual inspection")

# Let's also do one final validation check between filtered_df and tsne_df
print("\n===== FINAL VALIDATION: CHECKING CLUSTER ASSIGNMENT CONSISTENCY =====")

# Create a lookup table of email_id -> cluster_id from filtered_df
original_clusters = dict(zip(filtered_df.index, filtered_df['cluster_id']))

# Now compare with what's in the visualization DataFrame
inconsistencies = 0
for i, row in tsne_df.iterrows():
    email_id = row['email_id']
    viz_cluster = row['cluster_id']
    original_cluster = original_clusters.get(email_id)

    if original_cluster != viz_cluster:
        inconsistencies += 1
        print(f"Inconsistency found for email {email_id}:")
        print(f"  Original cluster: {original_cluster}")
        print(f"  Visualization cluster: {viz_cluster}")

        if inconsistencies >= 10:
            print("Too many inconsistencies to show all. Stopping after 10 examples.")
            break

if inconsistencies == 0:
    print("SUCCESS: All cluster assignments match between original data and visualization!")
else:
    print(f"WARNING: Found {inconsistencies} inconsistencies between original clusters and visualization.")
    print("This suggests data alignment issues that need to be fixed.")

# Save outputs with debugging labels to distinguish from previous versions
fig.write_html('email_clusters_interactive_debug.html')
print("Created interactive visualization: email_clusters_interactive_debug.html")

# Also save the original version for comparison
fig.write_html('email_clusters_interactive.html')
print("Created interactive visualization: email_clusters_interactive.html")
