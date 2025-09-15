# Create download_model.py
from huggingface_hub import snapshot_download
import os

print("Starting fresh download...")
try:
    model_path = snapshot_download(
        repo_id="jinaai/jina-colbert-v2",
        force_download=True,
        resume_download=False
    )
    print(f"✅ Model downloaded successfully to: {model_path}")
    
    # Verify download
    import os
    files = os.listdir(model_path)
    print(f"Downloaded files: {files}")
    
    # Check for essential files
    essential_files = ['config.json', 'pytorch_model.bin', 'tokenizer.json']
    for file in essential_files:
        if file in files:
            print(f"✅ {file} found")
        else:
            print(f"❌ {file} missing")
            
except Exception as e:
    print(f"❌ Download failed: {e}")
    import traceback
    traceback.print_exc()