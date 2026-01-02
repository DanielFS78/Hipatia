
import os
import requests
import zipfile
import io

def download_file(url, dest_path):
    print(f"Downloading {url} to {dest_path}...")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print("Done.")
    except Exception as e:
        print(f"Failed to download {url}: {e}")

def main():
    # 1. Setup Directories
    base_dir = os.getcwd()
    models_dir = os.path.join(base_dir, "core", "models")
    docs_dir = os.path.join(base_dir, "Documentacion", "opencv")
    
    os.makedirs(models_dir, exist_ok=True)
    os.makedirs(docs_dir, exist_ok=True)

    # 2. Download WeChatQRCode Models
    model_base_url = "https://raw.githubusercontent.com/WeChatCV/opencv_3rdparty/wechat_qrcode/"
    models = [
        "detect.prototxt",
        "detect.caffemodel",
        "sr.prototxt",
        "sr.caffemodel"
    ]

    print("--- Downloading WeChatQRCode Models ---")
    for model in models:
        dest = os.path.join(models_dir, model)
        if not os.path.exists(dest):
            download_file(model_base_url + model, dest)
        else:
            print(f"{model} already exists. Skipping.")

    # 3. Download OpenCV Documentation
    # Using 4.10.0 as it's a very stable recent version. 
    # Python 4.12.0.x corresponds usually to 4.10.x C++ core
    docs_url = "https://github.com/opencv/opencv/releases/download/4.10.0/opencv-4.10.0-docs.zip"
    docs_zip_path = os.path.join(docs_dir, "opencv-4.10.0-docs.zip")

    print("\n--- Downloading OpenCV Documentation ---")
    if not os.path.exists(docs_zip_path):
        download_file(docs_url, docs_zip_path)
        
        # Unzip
        print("Extracting documentation...")
        try:
            with zipfile.ZipFile(docs_zip_path, 'r') as zip_ref:
                zip_ref.extractall(docs_dir)
            print("Extraction complete.")
        except Exception as e:
            print(f"Failed to extract docs: {e}")
    else:
        print("Documentation already exists. Skipping.")

if __name__ == "__main__":
    main()
