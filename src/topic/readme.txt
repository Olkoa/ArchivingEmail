# Pipeline de traitement des mails

Dans le dossier **`features`**, tu trouveras le script **`pipeline_data_cleaning`**.
Ce script gère **tout le process** : nettoyage des mails, création de chunks, calcul des embeddings et clustering.

---

### Exemple de lancement dans le script

```
if __name__ == "__main__":
    base_dir = Path(__file__).parent

    input_folder = base_dir.parent / "data" / "mail_export" / "celine_guyon"
    json_file = base_dir.parent / "data" / "processed" / "celine_guyon" / "all_cleaned_mails.json"
    chunk_output_dir = base_dir.parent / "data" / "processed" / "clustering" / "topic"

    print("\n=== Lancement de la pipeline complète ===")
    df_chunks, all_chunks, embeddings = automate_full_process(
        input_folder=input_folder,
        json_file=json_file,
        chunk_output_dir=chunk_output_dir,
        compute_embeds=True
    )
```

---

### Comment l’utiliser avec une nouvelle boîte mail

1. Mets une boîte mail **XXXX** à la racine de `mail_export`.
2. Le script va automatiquement parcourir **tous les sous-dossiers** de `XXXX` pour récupérer tous les mails et appliquer le pipeline.
3. Les mails seront ensuite **nettoyés, découpés en chunks, embedés et clusterisés**.

> Pour lancer le process, il suffit de remplacer `celine_guyon` par `XXXX` dans le script et de faire :

```
python src/features/pipeline_data_cleaning.py
```

---

### Où sont sauvegardées les données ?

Dans le script, tu trouveras des commentaires indiquant **où sont stockés** :

* Les **chunks**
* Les **embeddings**
* Les **labels de cluster**

Ces fichiers sont ensuite utilisés par l’application Streamlit.

---

### Lancer l’application Streamlit

Dans le dossier `topic`, il y a un fichier **`config.py`** qui contient les chemins vers toutes les données nécessaires.
Le script `pipeline_data_cleaning` sauvegarde les fichiers exactement sur ces chemins.

Pour afficher les résultats :

```
streamlit run src/topic/semantic_app.py
```

> L’interface est assez intuitive : recherche sémantique, visualisation t-SNE et exploration des clusters.

