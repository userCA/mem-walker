import os
import sys
from sentence_transformers import SentenceTransformer

# Load .env
from dotenv import load_dotenv
load_dotenv(".env")

hf_home = os.getenv("HF_HOME")
cache_dir = os.path.join(hf_home, "hub")
model_name = "sentence-transformers/all-MiniLM-L6-v2"

# Find snapshot path
snapshot_path = None
model_path = os.path.join(cache_dir, f"models--{model_name.replace('/', '--')}")
if os.path.exists(model_path):
    refs_path = os.path.join(model_path, "refs", "main")
    if os.path.exists(refs_path):
        with open(refs_path, "r") as f:
            commit_hash = f.read().strip()
        snapshot_path = os.path.join(model_path, "snapshots", commit_hash)

print(f"Snapshot path: {snapshot_path}", flush=True)

if snapshot_path:
    print(f"Checking files in {snapshot_path}:", flush=True)
    files = ["pytorch_model.bin", "model.safetensors", "config.json"]
    for f in files:
        fp = os.path.join(snapshot_path, f)
        exists = os.path.exists(fp)
        print(f"  {f}: {exists}", flush=True)
        if exists:
            print(f"  {f} size: {os.path.getsize(fp)}", flush=True)

print("\n--- Attempt 3: Pointing to snapshot directly WITHOUT local_files_only ---", flush=True)
# If path is local, we don't strictly need local_files_only=True if we are sure it's a path
# But we are offline, so we want to avoid connection.
# However, if it's a path, transformers usually doesn't connect.

if snapshot_path and os.path.exists(snapshot_path):
    try:
        model = SentenceTransformer(
            snapshot_path,
            local_files_only=True
        )
        print("Success with snapshot path!", flush=True)
    except Exception as e:
        print(f"Failed with snapshot path: {e}", flush=True)
