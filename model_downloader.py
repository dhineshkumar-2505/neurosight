"""
Model Downloader for NeuroSight
Downloads AI models from Google Drive on-demand
"""

import os
import requests
from pathlib import Path
import sys


class ModelDownloader:
    """Download AI models from Google Drive"""
    
    # Google Drive file IDs - REPLACE WITH YOUR ACTUAL FILE IDs
    # To get file ID: Share file → Copy link → Extract ID from URL
    # URL format: https://drive.google.com/file/d/FILE_ID_HERE/view
    MODEL_URLS = {
        'alzhimermodel.pth': 'YOUR_ALZHEIMER_FILE_ID',
        'dementia_detection_model_2.h5': 'YOUR_DEMENTIA_FILE_ID',
        'multiple_sclerosis.pth': 'YOUR_MS_FILE_ID',
        'stroke.pth': 'YOUR_STROKE_FILE_ID'
    }
    
    def __init__(self, models_dir='models'):
        """Initialize downloader with models directory"""
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(exist_ok=True)
        print(f"📁 Models directory: {self.models_dir.absolute()}")
    
    def download_file_from_google_drive(self, file_id, destination):
        """
        Download file from Google Drive
        Handles large files with confirmation token
        """
        URL = "https://docs.google.com/uc?export=download"
        
        session = requests.Session()
        
        print(f"   Connecting to Google Drive...")
        response = session.get(URL, params={'id': file_id}, stream=True)
        
        # Get file size if available
        file_size = response.headers.get('content-length')
        if file_size:
            file_size_mb = int(file_size) / (1024 * 1024)
            print(f"   File size: {file_size_mb:.1f} MB")
        
        # Handle large file confirmation
        token = None
        for key, value in response.cookies.items():
            if key.startswith('download_warning'):
                token = value
                break
        
        if token:
            params = {'id': file_id, 'confirm': token}
            response = session.get(URL, params=params, stream=True)
        
        # Save file with progress
        print(f"   Downloading to: {destination}")
        downloaded = 0
        with open(destination, 'wb') as f:
            for chunk in response.iter_content(chunk_size=32768):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    # Show progress every 10MB
                    if downloaded % (10 * 1024 * 1024) == 0:
                        print(f"   Downloaded: {downloaded / (1024*1024):.1f} MB...")
        
        final_size = os.path.getsize(destination) / (1024 * 1024)
        print(f"   ✓ Complete! Final size: {final_size:.1f} MB")
    
    def download_model(self, model_name):
        """Download a specific model if not already present"""
        if model_name not in self.MODEL_URLS:
            raise ValueError(f"Unknown model: {model_name}")
        
        destination = self.models_dir / model_name
        
        # Check if already exists
        if destination.exists():
            size_mb = os.path.getsize(destination) / (1024 * 1024)
            print(f"✓ {model_name} already exists ({size_mb:.1f} MB)")
            return str(destination)
        
        # Download
        print(f"\n⬇️  Downloading {model_name}...")
        file_id = self.MODEL_URLS[model_name]
        
        if file_id.startswith('YOUR_'):
            print(f"   ⚠️  ERROR: File ID not configured!")
            print(f"   Please update MODEL_URLS in model_downloader.py")
            print(f"   See CLOUD_MODEL_STORAGE.md for instructions")
            return None
        
        try:
            self.download_file_from_google_drive(file_id, destination)
            print(f"✅ Downloaded {model_name}")
            return str(destination)
        except Exception as e:
            print(f"❌ Error downloading {model_name}: {str(e)}")
            if destination.exists():
                os.remove(destination)
            return None
    
    def download_all_models(self):
        """Download all models"""
        print("\n" + "="*60)
        print("📥 NeuroSight Model Downloader")
        print("="*60)
        
        success_count = 0
        total_count = len(self.MODEL_URLS)
        
        for model_name in self.MODEL_URLS.keys():
            result = self.download_model(model_name)
            if result:
                success_count += 1
        
        print("\n" + "="*60)
        if success_count == total_count:
            print(f"✅ All {total_count} models downloaded successfully!")
        else:
            print(f"⚠️  Downloaded {success_count}/{total_count} models")
            print(f"   Check file IDs in MODEL_URLS")
        print("="*60 + "\n")
        
        return success_count == total_count
    
    def get_model_path(self, model_name):
        """
        Get path to model, download if needed
        Returns path string or None if download fails
        """
        path = self.models_dir / model_name
        
        if not path.exists():
            print(f"Model {model_name} not found, downloading...")
            result = self.download_model(model_name)
            if not result:
                return None
        
        return str(path)
    
    def check_all_models(self):
        """Check if all models are present"""
        missing = []
        for model_name in self.MODEL_URLS.keys():
            path = self.models_dir / model_name
            if not path.exists():
                missing.append(model_name)
        
        if missing:
            print(f"⚠️  Missing models: {', '.join(missing)}")
            return False
        else:
            print(f"✓ All {len(self.MODEL_URLS)} models present")
            return True


def main():
    """Main function for command-line usage"""
    print("\n🧠 NeuroSight Model Downloader\n")
    
    downloader = ModelDownloader()
    
    # Check current status
    print("Checking current models...")
    all_present = downloader.check_all_models()
    
    if all_present:
        print("\n✅ All models already downloaded!")
        response = input("\nRe-download anyway? (y/N): ")
        if response.lower() != 'y':
            print("Exiting...")
            return
    
    # Download models
    print("\nStarting download...")
    success = downloader.download_all_models()
    
    if success:
        print("🎉 Setup complete! Your models are ready.")
    else:
        print("\n⚠️  Some models failed to download.")
        print("Please check:")
        print("1. File IDs are correct in MODEL_URLS")
        print("2. Files are shared publicly on Google Drive")
        print("3. Internet connection is stable")
        print("\nSee CLOUD_MODEL_STORAGE.md for detailed instructions")


if __name__ == "__main__":
    main()
