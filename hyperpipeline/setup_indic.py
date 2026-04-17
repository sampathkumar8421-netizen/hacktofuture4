import os
import requests
import gzip
import shutil
from pathlib import Path

# Only targeting Hindi for the Proof of Concept to save bandwidth
LANGS = ["hi"]
BASE_URL = "https://storage.googleapis.com/ai4bharat-public-indic-nlp-corpora/embedding/indicnlp.v1.{lang}.vec.gz"

def download_and_extract(url, out_path):
    print(f"Downloading {url}...")
    temp_gz = out_path + ".gz"
    
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(temp_gz, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
                
    print(f"Extracting {temp_gz}...")
    with gzip.open(temp_gz, 'rb') as f_in:
        with open(out_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
            
    os.remove(temp_gz)
    print(f"Extracted to {out_path} smoothly")

def main():
    target_dir = Path("hyperpipeline/indic_models")
    target_dir.mkdir(parents=True, exist_ok=True)
    
    for lang in LANGS:
        url = BASE_URL.format(lang=lang)
        out_vec = str(target_dir / f"indicnlp.v1.{lang}.vec")
        if not os.path.exists(out_vec):
            download_and_extract(url, out_vec)
        else:
            print(f"Embedding {out_vec} already exists. Skipping.")

if __name__ == "__main__":
    main()
