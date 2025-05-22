# Run this once manually before running your script
import os
import shutil

cache_dir = os.path.expanduser("~/.cache/huggingface/transformers")
model_cache = os.path.join(cache_dir, "models--jinaai--jina-colbert-v2")

if os.path.exists(model_cache):
    shutil.rmtree(model_cache)
    print("Cleared corrupted model cache")

ragatouille_cache = os.path.expanduser("~/.ragatouille")
if os.path.exists(ragatouille_cache):
    shutil.rmtree(ragatouille_cache)
    print("Cleared ragatouille cache")