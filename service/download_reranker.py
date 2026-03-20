"""Download reranker model for offline use."""

import os
from huggingface_hub import snapshot_download
from dotenv import load_dotenv

# Load env vars to get HF_HOME
load_dotenv(".env")

hf_home = os.getenv("HF_HOME")
if not hf_home:
    print("Error: HF_HOME not found in .env")
    exit(1)

cache_dir = os.path.join(hf_home, "hub")
model_name = "BAAI/bge-reranker-base"

print(f"Downloading {model_name} to {cache_dir}...")

try:
    snapshot_download(
        repo_id=model_name,
        local_dir=os.path.join(cache_dir, f"models--{model_name.replace('/', '--')}"),
        local_dir_use_symlinks=False,  # Important for offline usage stability
        resume_download=True
    )
    print("✓ Download complete!")
    print("You can now run 'python examples/test_reranker.py' to verify.")
except Exception as e:
    print(f"✗ Download failed: {e}")
