import os
from huggingface_hub import snapshot_download

# Configuration
repo_id = "sentence-transformers/all-MiniLM-L6-v2"
cache_dir = os.path.join(os.getcwd(), ".hf-cache")

print(f"Downloading {repo_id} to {cache_dir}...")

# Download only necessary files for PyTorch/Sentence-Transformers to save space
# We exclude TensorFlow, Flax, and ONNX files if the user is concerned about size
allow_patterns = [
    "*.json", 
    "*.txt", 
    "*.bin", 
    "*.safetensors", 
    "*.py", 
    "README.md",
    ".gitattributes"
]

ignore_patterns = [
    "*.h5",        # TensorFlow
    "*.msgpack",   # Flax
    "*.ot",        # Rust/TensorFlow
    "*.onnx",      # ONNX
]

try:
    path = snapshot_download(
        repo_id=repo_id,
        repo_type="model",
        cache_dir=cache_dir,
        local_files_only=False,
        # allow_patterns=allow_patterns, # Optional: strict filtering
        ignore_patterns=ignore_patterns  # Exclude heavy frameworks we don't use
    )
    print(f"Successfully downloaded to: {path}")
    
    # Calculate size
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    
    print(f"Total model size: {total_size / (1024*1024):.2f} MB")

except Exception as e:
    print(f"Error downloading model: {e}")
